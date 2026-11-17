# Open the bundled Web application

Use this route only when the user asks to open/start the application, use its upload interface, or view its demo. Ordinary photo feedback stays in conversation. Do not load the photography audit references just to start the app.

## Start or reuse

Resolve the directory containing this skill's `SKILL.md` (including symlinks). Do not assume the caller's current working directory, a particular home directory, or a second checkout. Use Python 3.11+ and quote the resolved absolute script path:

```bash
python3 "/absolute/path/to/photography-coach/scripts/open_workbench.py" --setup --no-browser --json
```

On Windows use `py -3` instead of `python3`. Add `--demo` only if a demo was requested. `--setup` permits installation of the declared image dependencies into this project's `.venv` if no suitable interpreter is available; it does not modify system Python, install Codex/MCP, configure a provider or make a model request. Follow the host's execution/network permissions. If installation is denied or fails, show the actual error and the manual command; do not bypass the restriction.

The command runs the bundled app in the background and returns JSON containing `running`, `url`, `pid`, `reused` and `browser_opened`, or a nonzero exit with `error`. The default search is loopback ports 8768–8788. It reuses only a workbench with this installation and private data directory's health identity; unrelated services are left untouched. If a legacy workbench is recognized without this health endpoint, stop and ask the user to close it first: its data directory cannot be verified. A fixed `--port` disables the fallback. Do not treat a bare HTTP 200 or a static report as an application health check.

After a successful result:

1. Open the returned `url` using the host's available browser capability. If none is available, run the launcher without `--no-browser` to request the system browser. It reuses the same server. A failed browser open is not a failed server launch: always return the actual URL as a clickable link.
2. When the browser can be inspected, confirm the actual workbench renders. A launcher health result proves the service is reachable, not that every interface action or model integration works.
3. Tell the user briefly: the app is open/available locally; they can upload a photo or view the no-key demo; real critique in this app requires their own API configuration and explicit cost/data consent. Do not request an API key in chat, read credentials from host configuration, or claim the app uses the Codex subscription.

Do not upload an attached photograph or start paid analysis just because the application was opened. Let the user choose and confirm within the page.

## Runtime boundaries

- Installation is not autostart: no login item, scheduled task, public deployment or shell profile change is created.
- The launcher does not copy the project or existing photos. Code stays in the installed skill; private records use the workbench's existing repository-external directory.
- The server holds an OS lock for its private data directory before recovering any records. A second current-version service cannot open that directory even on a different port; a crash releases the lock automatically. Do not remove lock files to bypass an active instance.
- The background process remains after closing a browser tab. The returned PID identifies it for the operating system's process manager; do not stop unrelated services or kill by port/name. For terminal-managed use, run `python3 -m app.server` from the skill directory and stop with Ctrl+C.
- `--status --no-browser --json` only checks for a running workbench; it does not install dependencies or start a server. Use the same `--port` / `--data-dir` if custom values were chosen.
- After Python source updates, restart the matching server before validating the new code. Reuse does not hot-reload Python.
- Keep loopback, Host/Origin/token checks, separate API consent and existing private-data boundaries. Do not add `0.0.0.0`, a tunnel, telemetry or automatic model retries.

The standalone app's API protocol, supported photo formats, export and current limitations remain documented in [`app/README.md`](../app/README.md). This launcher does not add live reference retrieval or certify photography quality.
