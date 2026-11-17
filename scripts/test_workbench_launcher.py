"""Local launcher behavior and real HTTP readiness; no provider calls or browser popups."""

from __future__ import annotations

import contextlib
import io
import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import launcher
from app.server import LocalServer
from app.workbench import Workbench


def unused_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


class WorkbenchLauncherTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.data = Path(self.temp.name).resolve() / "private"
        self.servers = []
        self.processes = []

    def tearDown(self):
        for process in self.processes:
            if process.poll() is None:
                process.terminate()
            process.wait(timeout=5)
        for server, thread in self.servers:
            server.shutdown()
            server.server_close()
            thread.join(2)
        self.temp.cleanup()

    def serve(self, data=None) -> LocalServer:
        server = LocalServer(0, Workbench(data or self.data))
        thread = threading.Thread(target=lambda: server.serve_forever(poll_interval=.02), daemon=True)
        thread.start()
        self.servers.append((server, thread))
        return server

    def main_result(self, *arguments):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = launcher.main(["--json", "--no-browser", "--data-dir", str(self.data), *arguments])
        return code, json.loads(output.getvalue())

    def test_health_identifies_app_without_exposing_private_data_or_config(self):
        server = self.serve()
        result = launcher.health(server.server_port)
        self.assertEqual(result["product"], launcher.PRODUCT)
        self.assertEqual(result["workbench_id"], launcher.workbench_id(self.data))
        self.assertEqual(result["pid"], os.getpid())
        self.assertNotIn(str(self.data), json.dumps(result))
        self.assertNotIn("token", result)
        self.assertNotIn("config", result)

    def test_reopening_reuses_matching_server_without_install_or_spawn(self):
        server = self.serve()
        with patch.object(launcher, "find_interpreter") as dependencies, patch.object(launcher.subprocess, "Popen") as spawn:
            result = launcher.launch([server.server_port], self.data, setup=True)
        self.assertTrue(result["reused"])
        self.assertEqual(result["url"], server.origin + "/")
        dependencies.assert_not_called()
        spawn.assert_not_called()

    def test_other_private_directory_or_installation_is_not_reused(self):
        server = self.serve()
        self.assertIsNone(launcher.existing([server.server_port], self.data.parent / "other"))
        with patch.object(launcher, "ROOT", self.data.parent / "another-installation"):
            self.assertIsNone(launcher.existing([server.server_port], self.data))

    def test_legacy_workbench_blocks_a_second_server_for_unknown_data(self):
        server = self.serve()
        from app.server import Handler
        original = Handler._dispatch

        def old_routes(handler, mutation):
            if handler.path == "/api/health":
                handler._json({"error": "legacy test server"}, 404)
            else:
                original(handler, mutation)

        with patch.object(Handler, "_dispatch", old_routes), patch.object(launcher.subprocess, "Popen") as spawn:
            with self.assertRaisesRegex(launcher.LaunchError, "旧版"):
                launcher.launch([server.server_port, unused_port()], self.data)
        spawn.assert_not_called()

    def test_data_directory_lock_blocks_duplicates_and_is_released(self):
        # The lock covers data, not a port or checkout, and leaves photo records untouched.
        with launcher.single_instance(self.data):
            with self.assertRaisesRegex(launcher.LaunchError, "已由另一个"):
                with launcher.single_instance(self.data):
                    self.fail("duplicate lock was acquired")
            with launcher.single_instance(self.data.parent / "other"):
                pass
        with launcher.single_instance(self.data):
            pass
        self.assertFalse(self.data.exists())

    def test_status_is_read_only_and_does_not_open_a_browser(self):
        port = unused_port()
        with patch.object(launcher, "find_interpreter") as dependencies, patch.object(launcher, "launch") as start, patch.object(launcher.webbrowser, "open") as browser:
            code, result = self.main_result("--status", "--setup", "--port", str(port))
        self.assertEqual((code, result), (0, {"running": False}))
        self.assertFalse(self.data.exists())
        dependencies.assert_not_called()
        start.assert_not_called()
        browser.assert_not_called()

    def test_demo_url_and_client_open_mode_do_not_start_a_model(self):
        server = self.serve()
        with patch.object(launcher.webbrowser, "open") as browser:
            code, result = self.main_result("--demo", "--port", str(server.server_port))
        self.assertEqual(code, 0, result)
        self.assertEqual(result["url"], server.origin + "/?demo=1")
        self.assertFalse(result["browser_opened"])
        browser.assert_not_called()
        self.assertFalse(server.workbench.configuration()["configured"])
        self.assertEqual(server.workbench.sessions(), [])

    def test_missing_dependency_is_explicit_not_automatic_pip_install(self):
        with patch.object(launcher, "dependencies_ready", return_value=False), patch.object(launcher.subprocess, "run") as install:
            with self.assertRaisesRegex(launcher.LaunchError, "--setup"):
                launcher.find_interpreter(setup=False)
        install.assert_not_called()

    def test_setup_refuses_to_overwrite_an_unrelated_venv_directory(self):
        root = Path(self.temp.name).resolve()
        (root / ".venv").mkdir()
        with patch.object(launcher, "ROOT", root), patch.object(launcher, "dependencies_ready", return_value=False), patch.object(launcher.subprocess, "run") as install:
            with self.assertRaisesRegex(launcher.LaunchError, "未覆盖"):
                launcher.find_interpreter(setup=True)
        install.assert_not_called()

    def test_setup_installs_only_the_bundled_requirements_in_a_project_venv(self):
        root = Path(self.temp.name).resolve()
        expected = launcher.interpreter_path(root / ".venv")
        with patch.object(launcher, "ROOT", root), patch.object(launcher, "dependencies_ready", side_effect=[False, False, True]), patch.object(launcher.subprocess, "run") as install:
            executable = launcher.find_interpreter(setup=True)
        self.assertEqual(executable, expected)
        self.assertEqual(install.call_args_list[0].args[0], [sys.executable, "-m", "venv", str(root / ".venv")])
        self.assertEqual(install.call_args_list[1].args[0], [str(expected), "-m", "pip", "install", "-r", str(root / "app/requirements.txt")])

    def test_fixed_occupied_port_is_not_killed_or_replaced(self):
        with socket.socket() as occupied:
            occupied.bind(("127.0.0.1", 0))
            occupied.listen()
            port = occupied.getsockname()[1]
            with patch.object(launcher, "find_interpreter") as dependencies, patch.object(launcher.subprocess, "Popen") as spawn:
                with self.assertRaisesRegex(launcher.LaunchError, "--port"):
                    launcher.launch([port], self.data)
            self.assertEqual(occupied.getsockname()[1], port)
        dependencies.assert_not_called()
        spawn.assert_not_called()

    def test_launch_starts_real_service_and_skips_an_unrelated_port(self):
        real_spawn = subprocess.Popen

        def tracked_spawn(*args, **kwargs):
            process = real_spawn(*args, **kwargs)
            if "app.server" in args[0]:
                self.processes.append(process)
            return process

        with socket.socket() as occupied:
            occupied.bind(("127.0.0.1", 0))
            occupied.listen()
            blocked, free = occupied.getsockname()[1], unused_port()
            with patch.object(launcher.subprocess, "Popen", side_effect=tracked_spawn):
                result = launcher.launch([blocked, free], self.data)
        self.assertEqual(result["url"], f"http://127.0.0.1:{free}/")
        self.assertFalse(result["reused"])
        self.assertEqual(result["pid"], self.processes[0].pid)
        again = launcher.launch([free], self.data)
        self.assertTrue(again["reused"])
        self.assertEqual(again["pid"], result["pid"])
        self.assertEqual(len(self.processes), 1)

        # A second server on another port must fail before recovery can rewrite a live record.
        record = self.data / "sessions" / ("a" * 32)
        record.mkdir(mode=0o700)
        frozen = b'{"id": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "state": "running"}'
        (record / "session.json").write_bytes(frozen)
        duplicate = subprocess.run([sys.executable, "-m", "app.server", "--port", str(unused_port()),
                                    "--data-dir", str(self.data)], cwd=launcher.ROOT,
                                   capture_output=True, timeout=10)
        self.assertNotEqual(duplicate.returncode, 0)
        self.assertIn("已由另一个", duplicate.stderr.decode())
        self.assertEqual((record / "session.json").read_bytes(), frozen)

    def test_skill_script_works_through_a_symlink_from_another_cwd(self):
        server = self.serve()
        alias = Path(self.temp.name) / "installed skill"
        try:
            alias.symlink_to(launcher.ROOT, target_is_directory=True)
        except OSError:
            self.skipTest("This host cannot create directory symlinks")
        result = subprocess.run([sys.executable, str(alias / "scripts/open_workbench.py"),
                                 "--status", "--json", "--port", str(server.server_port), "--data-dir", str(self.data)],
                                cwd=self.temp.name, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)
        self.assertTrue(output["running"])
        self.assertEqual(output["url"], server.origin + "/")

    def test_browser_failure_still_returns_the_reachable_url(self):
        server = self.serve()
        for failure in (None, OSError("test-only opener failure"), launcher.webbrowser.Error("test-only opener failure")):
            with self.subTest(failure=failure):
                output = io.StringIO()
                with patch.object(launcher.webbrowser, "open", return_value=False, side_effect=failure), contextlib.redirect_stdout(output):
                    code = launcher.main(["--json", "--port", str(server.server_port), "--data-dir", str(self.data)])
                self.assertEqual(code, 0, output.getvalue())
                result = json.loads(output.getvalue())
                self.assertEqual(result["url"], server.origin + "/")
                self.assertFalse(result["browser_opened"])

    def test_startup_error_preserves_the_actual_error(self):
        # Deliberately invalid: a server must not claim the user's broad home folder.
        with self.assertRaisesRegex(launcher.LaunchError, "专用数据目录"):
            launcher.launch([unused_port()], Path.home())

    def test_startup_timeout_stops_only_its_own_process(self):
        process = unittest.mock.Mock()
        process.poll.return_value = None
        with patch.object(launcher, "existing", return_value=None), patch.object(launcher, "port_available", return_value=True), \
                patch.object(launcher, "find_interpreter", return_value=Path(sys.executable)), \
                patch.object(launcher.subprocess, "Popen", return_value=process):
            with self.assertRaisesRegex(launcher.LaunchError, "已停止本次"):
                launcher.launch([unused_port()], self.data, timeout=0)
        process.terminate.assert_called_once()
        process.wait.assert_called_once_with(timeout=3)
        process.kill.assert_not_called()

    def test_json_failure_and_invalid_port_are_not_claimed_as_success(self):
        with patch.object(launcher, "launch", side_effect=launcher.LaunchError("test-only failure")):
            code, result = self.main_result()
        self.assertEqual(code, 1)
        self.assertEqual(result, {"error": "test-only failure"})
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            launcher.main(["--port", "0"])
        self.assertEqual(error.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
