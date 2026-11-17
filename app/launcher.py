"""Start or find the local workbench without importing its image dependencies."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import http.client
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRODUCT = "photography-coach-workbench"
PROTOCOL = 1
DEFAULT_PORTS = range(8768, 8789)


class LaunchError(ValueError):
    pass


def default_data_dir() -> Path:
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Photography Coach" / "workbench"
    if os.name == "nt":
        return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "Photography Coach" / "workbench"
    return Path.home() / ".local" / "share" / "photography-coach" / "workbench"


def workbench_id(data_dir: Path) -> str:
    # Distinguish another checkout or private data folder without publishing either path.
    value = str(ROOT) + "\0" + str(data_dir.expanduser().resolve())
    return hashlib.sha256(value.encode()).hexdigest()


@contextlib.contextmanager
def single_instance(data_dir: Path):
    """Hold an OS-released lock before loading or recovering private records."""
    user = hashlib.sha256(str(Path.home()).encode()).hexdigest()[:16]
    directory = Path(tempfile.gettempdir()).resolve() / ("photography-coach-" + user)
    if directory.is_symlink():
        raise LaunchError("工作台运行锁目录不能是符号链接。")
    directory.mkdir(mode=0o700, exist_ok=True)
    if os.name != "nt" and (directory.stat().st_mode & 0o077 or directory.stat().st_uid != os.getuid()):
        raise LaunchError("工作台运行锁目录须仅限当前用户访问。")
    identity = hashlib.sha256(str(data_dir.expanduser().resolve()).encode()).hexdigest()
    descriptor = os.open(directory / (identity + ".lock"), os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0), 0o600)
    with os.fdopen(descriptor, "r+b") as lock:
        try:
            if os.name == "nt":
                import msvcrt
                if not lock.read(1):
                    lock.write(b"0")
                    lock.flush()
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise LaunchError("此私人数据目录已由另一个工作台使用。请打开原服务，或先停止它；未读取或重写照片记录。") from exc
        # Closing the file releases the OS lock even after a crash; no PID-file deletion is needed.
        yield


def health(port: int) -> dict | None:
    # Use a direct loopback connection: no proxy environment, redirects or remote requests.
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=1)
    try:
        connection.request("GET", "/api/health")
        response = connection.getresponse()
        if response.status == 404:
            response.read(4097)
            connection.close()
            connection.request("GET", "/api/state")
            legacy = connection.getresponse()
            if legacy.status == 200:
                raw = legacy.read(4097)
                try:
                    value = json.loads(raw)
                except ValueError:
                    # Old state payloads list every session and can exceed this bounded read.
                    # Conservatively block the recognizable prefix rather than start a second writer.
                    if raw.lstrip().startswith(b'{"token":') and b'"config":' in raw:
                        return {"product": PRODUCT, "protocol": 0}
                    return None
                if (isinstance(value, dict) and isinstance(value.get("token"), str)
                        and isinstance(value.get("config"), dict) and isinstance(value.get("sessions"), list)
                        and "busy" in value):
                    return {"product": PRODUCT, "protocol": 0}
            return None
        if response.status != 200:
            return None
        result = json.loads(response.read(4097))
        if isinstance(result, dict) and result.get("product") == PRODUCT and result.get("protocol") == PROTOCOL:
            return result
    except (OSError, ValueError, http.client.HTTPException):
        pass
    finally:
        connection.close()
    return None


def port_available(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        if os.name != "nt":
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            probe.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


def interpreter_path(directory: Path) -> Path:
    return directory / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def dependencies_ready(executable: Path) -> bool:
    if not executable.is_file():
        return False
    check = ("import sys; from PIL import Image, ImageCms, ImageOps; import PIL; "
             "v=tuple(int(n) for n in PIL.__version__.split('.')[:3]); "
             "sys.exit(not (sys.version_info >= (3, 11) and (12, 1, 1) <= v < (13,)))")
    try:
        return subprocess.run([str(executable), "-c", check], capture_output=True, timeout=15).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def find_interpreter(*, setup: bool) -> Path:
    environment = ROOT / ".venv"
    for executable in (interpreter_path(environment), Path(sys.executable)):
        if dependencies_ready(executable):
            return executable
    if not setup:
        raise LaunchError("缺少工作台依赖。请再次运行本命令并加 --setup；只会在项目 .venv 中安装 app/requirements.txt。")
    if environment.is_symlink() or (environment.exists() and not (environment / "pyvenv.cfg").is_file()):
        raise LaunchError("项目 .venv 不是普通虚拟环境，未覆盖。请检查该目录后手动安装依赖。")
    try:
        print("准备项目虚拟环境与图像依赖；不会配置模型或调用 API。", file=sys.stderr, flush=True)
        if not environment.exists():
            subprocess.run([sys.executable, "-m", "venv", str(environment)], check=True, timeout=120,
                           stdout=sys.stderr, stderr=sys.stderr)
        executable = interpreter_path(environment)
        subprocess.run([str(executable), "-m", "pip", "install", "-r", str(ROOT / "app/requirements.txt")],
                       check=True, timeout=180, stdout=sys.stderr, stderr=sys.stderr)
    except (OSError, subprocess.SubprocessError) as exc:
        raise LaunchError("依赖安装未完成。请检查 Python venv/pip 与网络，再运行 --setup；未修改系统 Python。") from exc
    if not dependencies_ready(executable):
        raise LaunchError("项目虚拟环境仍无法加载所需图像依赖，请按 app/README.md 手动安装。")
    return executable


def existing(ports: list[int], data_dir: Path) -> dict | None:
    identity = workbench_id(data_dir)
    for port in ports:
        result = health(port)
        if result and result.get("protocol") == 0:
            raise LaunchError(f"发现旧版摄影工作台 http://127.0.0.1:{port}/，无法核实其记录目录。请先停止旧工作台再打开；未自动关闭它。")
        if result and result.get("workbench_id") == identity:
            return {"url": f"http://127.0.0.1:{port}/", "pid": result.get("pid"), "reused": True}
    return None


def launch(ports: list[int], data_dir: Path, *, setup: bool = False, timeout: float = 15) -> dict:
    if data_dir.expanduser().absolute() != data_dir.expanduser().resolve():
        raise LaunchError("请选择非符号链接的专用数据目录。")
    running = existing(ports, data_dir)
    if running:
        return running
    available = [port for port in ports if port_available(port)]
    if not available:
        raise LaunchError("可用端口均被其他服务占用，未关闭或替换它们。请用 --port 指定另一个端口。")
    executable = find_interpreter(setup=setup)
    command = [str(executable), "-m", "app.server", "--data-dir", str(data_dir)]
    for port in available:
        options = {"start_new_session": True} if os.name != "nt" else {
            "creationflags": subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
        }
        with tempfile.TemporaryFile() as log:
            process = subprocess.Popen(command + ["--port", str(port)], cwd=ROOT,
                                       stdin=subprocess.DEVNULL, stdout=log, stderr=log, **options)
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                running = existing([port], data_dir)
                if running:
                    running["reused"] = running["pid"] != process.pid
                    return running
                if process.poll() is not None:
                    break
                time.sleep(.1)
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=3)
                raise LaunchError("工作台未在等待时间内就绪，已停止本次启动的进程；未打开未确认的页面。")
            log.seek(0)
            error = log.read(4096).decode("utf-8", errors="replace").strip()
            # A concurrent opener may win the same port. Find it instead of starting a duplicate.
            running = existing(ports, data_dir)
            if running:
                return running
            if port_available(port):
                raise LaunchError("工作台启动失败：" + (error or "请检查私人数据目录及依赖。"))
    raise LaunchError("端口在启动时被其他服务占用，请重试或用 --port 指定空闲端口。")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="打开摄影教练的本机 Web 应用；不会调用模型。")
    parser.add_argument("--port", type=int, help="固定端口；默认在 8768–8788 中查找或启动")
    parser.add_argument("--data-dir", type=Path, default=default_data_dir())
    parser.add_argument("--setup", action="store_true", help="依赖缺失时，在项目 .venv 中安装")
    parser.add_argument("--demo", action="store_true", help="直接打开免密钥演示")
    parser.add_argument("--no-browser", action="store_true", help="只返回地址，由客户端打开")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出启动结果或错误")
    parser.add_argument("--status", action="store_true", help="仅查找现有工作台，不启动或安装")
    args = parser.parse_args(argv)
    if args.port is not None and not 1 <= args.port <= 65535:
        parser.error("port must be between 1 and 65535")
    os.umask(0o077)
    ports = [args.port] if args.port is not None else list(DEFAULT_PORTS)
    data_dir = args.data_dir.expanduser().absolute()
    try:
        if sys.version_info < (3, 11):
            raise LaunchError("工作台需要 Python 3.11 或更新版本。")
        result = existing(ports, data_dir) if args.status else launch(ports, data_dir, setup=args.setup)
        if result is None:
            result = {"running": False}
        else:
            result["running"] = True
            if args.demo:
                result["url"] += "?demo=1"
            result["browser_opened"] = False
            if not args.status and not args.no_browser:
                try:
                    result["browser_opened"] = bool(webbrowser.open(result["url"], new=2))
                except (webbrowser.Error, OSError):
                    pass
        if args.json:
            print(json.dumps(result, ensure_ascii=False))
        elif result["running"]:
            print(f"摄影教练{'已在运行' if result['reused'] else '已启动'}：{result['url']}")
            print(f"后台服务进程：{result['pid']}；关闭标签页不会停止服务。")
            print("打开页面不调用模型；使用自己的照片时，在页面中配置 API 并确认费用。")
        else:
            print("未找到本项目、此数据目录对应的工作台。")
        return 0
    except (LaunchError, OSError) as exc:
        if args.json:
            print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        else:
            print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
