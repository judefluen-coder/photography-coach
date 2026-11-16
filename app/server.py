"""Loopback-only workbench. Run with: python -m app.server"""

from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

from app.workbench import ROOT, Workbench, WorkbenchError
from core.images import MAX_BYTES

STATIC = ROOT / "app" / "static"
MIME = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8", ".js": "text/javascript; charset=utf-8",
        ".jpg": "image/jpeg", ".png": "image/png", ".webp": "image/webp", ".zip": "application/zip"}
ASSETS = {"source.png", "source.jpg", "source-preview.jpg", "color.jpg", "color-preview.jpg", "treatment.jpg", "treatment-preview.jpg"}


def default_data_dir() -> Path:
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Photography Coach" / "workbench"
    if os.name == "nt":
        return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "Photography Coach" / "workbench"
    return Path.home() / ".local" / "share" / "photography-coach" / "workbench"


class LocalServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, port: int, workbench: Workbench):
        self.workbench = workbench
        self.token = secrets.token_urlsafe(32)
        super().__init__(("127.0.0.1", port), Handler)
        self.host = f"127.0.0.1:{self.server_port}"
        self.origin = "http://" + self.host


class Handler(BaseHTTPRequestHandler):
    server: LocalServer
    protocol_version = "HTTP/1.0"

    def setup(self):
        super().setup()
        self.connection.settimeout(15)

    def log_message(self, *args):
        # Do not log private filenames, questions, request bodies or secrets.
        pass

    def _headers(self, status: int, content_type: str, length: int, *, report=False, download=None):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(length))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        self.send_header("Content-Security-Policy", "default-src 'none'; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline'; script-src 'self'" + (" 'unsafe-inline'" if report else "") + "; connect-src 'self'; frame-src 'self'; frame-ancestors 'self'; base-uri 'none'; form-action 'self'; object-src 'none'")
        if download:
            self.send_header("Content-Disposition", f'attachment; filename="{download}"')
        self.end_headers()

    def _json(self, data: dict | list, status=200):
        body = json.dumps(data, ensure_ascii=False, allow_nan=False).encode()
        self._headers(status, "application/json; charset=utf-8", len(body))
        self.wfile.write(body)

    def _guard(self, mutation=False):
        if self.headers.get("Host") != self.server.host:
            raise WorkbenchError("仅允许通过本机 127.0.0.1 地址访问。", 403)
        if self.headers.get("Origin") not in (None, self.server.origin) or self.headers.get("Sec-Fetch-Site") not in (None, "none", "same-origin"):
            raise WorkbenchError("不接受来自其他站点的请求。", 403)
        if mutation and not secrets.compare_digest(self.headers.get("X-Workbench-Token", ""), self.server.token):
            raise WorkbenchError("页面连接已失效，请刷新后重试。", 403)
        if self.headers.get("Transfer-Encoding") or self.headers.get("Content-Encoding"):
            raise WorkbenchError("不支持的请求编码。", 400)

    def _body(self, maximum: int) -> bytes:
        lengths = self.headers.get_all("Content-Length", [])
        if len(lengths) != 1 or not lengths[0].isdigit():
            raise WorkbenchError("请求缺少明确的内容长度。", 411)
        length = int(lengths[0])
        if length > maximum:
            raise WorkbenchError("文件或请求过大；照片上限为 16 MB。", 413)
        body = self.rfile.read(length)
        if len(body) != length:
            raise WorkbenchError("上传中断，请重新选择照片。")
        return body

    def _json_body(self) -> dict:
        if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
            raise WorkbenchError("请求格式需要 JSON。", 415)
        try:
            value = json.loads(self._body(64 * 1024))
        except (ValueError, UnicodeError) as exc:
            raise WorkbenchError("请求内容无法读取。") from exc
        if not isinstance(value, dict):
            raise WorkbenchError("请求内容应为对象。")
        return value

    def _file(self, path: Path, *, report=False, download=None, embedded=False):
        if path.is_symlink() or not path.is_file() or path.absolute() != path.resolve():
            raise WorkbenchError("文件不存在。", 404)
        if embedded:
            body = path.read_bytes().replace(b"</head>", b"<style>.topbar,.report-nav{display:none}.workspace{padding-top:12px}</style></head>")
            self._headers(200, MIME[".html"], len(body), report=True)
            self.wfile.write(body)
            return
        self._headers(200, MIME.get(path.suffix, "application/octet-stream"), path.stat().st_size, report=report, download=download)
        with path.open("rb") as file:
            while chunk := file.read(65536):
                self.wfile.write(chunk)

    def do_GET(self):
        self._dispatch(False)

    def do_POST(self):
        self._dispatch(True)

    def _dispatch(self, mutation: bool):
        try:
            self._guard(mutation)
            parts = urlsplit(self.path)
            path = parts.path  # No filesystem paths derived from untrusted URL segments.
            workbench = self.server.workbench
            if not mutation:
                if path in ("/", "/index.html", "/app.css", "/app.js"):
                    return self._file(STATIC / ("index.html" if path in ("/", "/index.html") else path[1:]))
                if path == "/api/state":
                    return self._json({"token": self.server.token, "config": workbench.configuration(), "sessions": workbench.sessions(), "busy": workbench.busy})
                if re.fullmatch(r"/(demo|demo-street)/index\.html", path):
                    return self._file(ROOT / "docs" / path[1:], report=True, embedded=parts.query == "embedded=1")
                if (match := re.fullmatch(r"/(demo|demo-street)/assets/([a-z.-]+)", path)) and match[2] in ASSETS:
                    return self._file(ROOT / "docs" / path[1:])
                if match := re.fullmatch(r"/api/sessions/([a-f0-9]{32})", path):
                    return self._json(workbench.get(match[1]))
                if match := re.fullmatch(r"/media/([a-f0-9]{32})/(preview.jpg|original\.(?:jpg|png|webp))", path):
                    return self._file(workbench.directory(match[1]) / match[2], download="photography-original." + match[2].split(".")[-1] if match[2].startswith("original.") else None)
                if match := re.fullmatch(r"/reports/([a-f0-9]{32})/([a-f0-9]{32})/(index.html|assets/[a-z.-]+)", path):
                    if match[3] != "index.html" and match[3].removeprefix("assets/") not in ASSETS:
                        raise WorkbenchError("文件不存在。", 404)
                    return self._file(workbench.directory(match[1]) / match[2] / match[3], report=True, embedded=parts.query == "embedded=1" and match[3] == "index.html")
                if match := re.fullmatch(r"/export/([a-f0-9]{32}).zip", path):
                    return self._file(workbench.export(match[1]), download="photography-coach-report.zip")
            else:
                if path == "/api/photos":
                    if self.headers.get("Content-Type") != "application/octet-stream":
                        raise WorkbenchError("请按照片文件上传。", 415)
                    return self._json(workbench.upload(self._body(MAX_BYTES), unquote(self.headers.get("X-Photo-Name", "照片"))), 201)
                data = self._json_body()
                if path == "/api/config":
                    return self._json(workbench.configure(data))
                if path == "/api/config/clear":
                    workbench.clear_configuration()
                    return self._json({"ok": True})
                if match := re.fullmatch(r"/api/sessions/([a-f0-9]{32})/(critique|question|preview|cancel|archive)", path):
                    session_id, action = match.groups()
                    if action == "cancel":
                        return self._json(workbench.cancel(session_id))
                    if action == "archive":
                        workbench.archive(session_id)
                        return self._json({"ok": True, "message": "记录已移入本机数据目录的 trash 回收区，可恢复；没有永久删除。"})
                    return self._json(workbench.start(session_id, action, data), 202)
            raise WorkbenchError("页面不存在。", 404)
        except (BrokenPipeError, ConnectionResetError, TimeoutError):
            pass
        except WorkbenchError as exc:
            self._json({"error": str(exc)}, exc.status)
        except ValueError:
            self._json({"error": "照片或配置无效。请检查图片格式、尺寸及 HTTPS 模型地址。"}, 400)
        except Exception:
            self._json({"error": "本机处理未完成，未自动重试。请检查数据目录是否可写及剩余磁盘空间。"}, 500)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8768)
    parser.add_argument("--data-dir", type=Path, default=default_data_dir())
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("port must be between 1 and 65535")
    os.umask(0o077)
    try:
        server = LocalServer(args.port, Workbench(args.data_dir))
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    print(f"Photography Coach: {server.origin}", flush=True)
    print(f"私人记录目录: {server.workbench.root}", flush=True)
    print("只在本机开放；模型密钥仅存于进程内存。按 Ctrl+C 关闭。", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
