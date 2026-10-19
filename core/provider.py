"""Bounded Responses API transport. No SDK, automatic retries, or secret persistence."""

from __future__ import annotations

import base64
import http.client
import ipaddress
import json
import socket
import ssl
from urllib.parse import urlsplit, urlunsplit

from core.contracts import check_schema


class ProviderError(RuntimeError):
    def __init__(self, message: str, usage: dict | None = None):
        super().__init__(message)
        self.usage = usage or {}


def validated_url(url: str, *, endpoint: bool = False) -> str:
    if not isinstance(url, str) or len(url) > 2048 or any(ord(c) < 33 for c in url):
        raise ValueError("服务地址不是有效的 HTTPS URL。")
    parts = urlsplit(url)
    if parts.scheme != "https" or not parts.hostname or parts.username or parts.password or parts.fragment:
        raise ValueError("只支持不含凭据的公开 HTTPS 地址。")
    if parts.port not in (None, 443):
        raise ValueError("首版只连接 HTTPS 443 端口。")
    if endpoint and (parts.query or ".." in parts.path.split("/")):
        raise ValueError("API 基地址不能包含查询参数或上级路径。")
    if parts.hostname.lower() in {"localhost", "localhost.localdomain"} or parts.hostname.lower().endswith((".local", ".localhost")):
        raise ValueError("不允许将服务地址指向本机或内网。")
    try:
        address = ipaddress.ip_address(parts.hostname)
    except ValueError:
        address = None
    if address is not None and not address.is_global:
        raise ValueError("不允许将服务地址指向本机或内网。")
    return urlunsplit(("https", parts.netloc, parts.path.rstrip("/") if endpoint else parts.path, parts.query, ""))


class PublicHTTPSConnection(http.client.HTTPSConnection):
    def connect(self):
        addresses = socket.getaddrinfo(self.host, self.port, type=socket.SOCK_STREAM)
        if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
            raise ProviderError("服务域名解析到了非公开地址，已阻止连接。")
        # Pin the validated address while retaining hostname verification / SNI.
        raw = socket.create_connection((addresses[0][4][0], self.port), self.timeout)
        try:
            self.sock = self._context.wrap_socket(raw, server_hostname=self.host)
        except Exception:
            raw.close()
            raise


def request_bytes(url: str, method: str = "GET", body: bytes | None = None,
                  headers: dict | None = None, limit: int = 4_000_000, timeout: int = 120) -> tuple[bytes, str]:
    parts = urlsplit(validated_url(url))
    connection = PublicHTTPSConnection(parts.hostname, timeout=timeout, context=ssl.create_default_context())
    path = parts.path or "/"
    if parts.query:
        path += "?" + parts.query
    try:
        connection.request(method, path, body=body, headers={"Accept-Encoding": "identity", **(headers or {})})
        response = connection.getresponse()
        if response.status >= 300:
            codes = {401: "API 密钥无效或已过期。", 403: "账户无权调用所选模型或工具。", 429: "模型额度或速率限制已触发。"}
            raise ProviderError(codes.get(response.status, f"服务返回 HTTP {response.status}。请检查地址、模型和协议；未自动重试。"))
        if response.getheader("Content-Encoding", "identity") != "identity":
            raise ProviderError("服务返回了不支持的压缩内容。")
        result = response.read(limit + 1)
        if len(result) > limit:
            raise ProviderError("服务返回内容过大，已停止读取。")
        return result, response.getheader("Content-Type", "").split(";")[0]
    except ProviderError:
        raise
    except (OSError, http.client.HTTPException) as exc:
        # Never expose response bodies, authorization headers, or full private URLs.
        raise ProviderError("无法连接模型服务或等待超时。没有自动重试；本次调用可能已产生费用。") from exc
    finally:
        connection.close()


def image_part(data: bytes) -> dict:
    return {"type": "input_image", "image_url": "data:image/jpeg;base64," + base64.b64encode(data).decode(), "detail": "high"}


def usage_only(raw: dict) -> dict:
    return {key: raw[key] for key in ("input_tokens", "output_tokens", "total_tokens")
            if isinstance(raw.get(key), int) and not isinstance(raw[key], bool) and raw[key] >= 0}


class ResponsesProvider:
    def __init__(self, settings: dict, transport=request_bytes):
        self.settings = dict(settings)
        self.transport = transport

    def generate(self, *, instructions: str, text: str, schema: dict, images: list[bytes] | None = None,
                 search: bool = False) -> tuple[dict, dict, list[str]]:
        settings = self.settings
        payload = {
            "model": settings["model"], "instructions": instructions,
            "input": [{"role": "user", "content": [{"type": "input_text", "text": text}, *[image_part(image) for image in images or []]]}],
            "store": False, "max_output_tokens": settings.get("max_output_tokens", 10000),
            "text": {"format": {"type": "json_schema", "name": "photography_coach", "strict": True, "schema": schema}},
        }
        if search:
            payload["tools"] = [{"type": "web_search"}]
            payload["tool_choice"] = "required"
            payload["include"] = ["web_search_call.action.sources"]
        body, _ = self.transport(validated_url(settings["base_url"], endpoint=True) + "/responses", "POST",
                                 json.dumps(payload).encode(), {"Authorization": "Bearer " + settings["api_key"], "Content-Type": "application/json"})
        try:
            result = json.loads(body)
            usage = usage_only(result.get("usage") or {})
            if result.get("status") not in (None, "completed") or result.get("error"):
                raise ProviderError("模型未完整返回结果，可能达到输出上限。已保留原图，未自动重试。", usage)
            texts, citations = [], []
            for item in result.get("output", []):
                if item.get("type") == "web_search_call":
                    citations.extend(source["url"] for source in item.get("action", {}).get("sources", []) if isinstance(source.get("url"), str))
                for content in item.get("content", []):
                    if content.get("type") == "refusal":
                        raise ProviderError("模型拒绝了这次请求。原图和已有反馈仍保留。", usage)
                    if content.get("type") == "output_text":
                        texts.append(content["text"])
                        citations.extend(a["url"] for a in content.get("annotations", []) if a.get("type") == "url_citation" and isinstance(a.get("url"), str))
            parsed = json.loads("".join(texts))
            check_schema(parsed, schema)
            return parsed, usage, citations
        except ProviderError:
            raise
        except (ValueError, TypeError, KeyError, AttributeError) as exc:
            raise ProviderError("模型输出不符合摄影教练的数据要求。没有用样例或猜测补齐；请更换支持图像及结构化输出的模型。", locals().get("usage")) from exc
