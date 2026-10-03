#!/usr/bin/env python3
"""Local-only page in front of check.py.

Run: python3 serve.py
Open: http://127.0.0.1:8765/

The process binds to loopback only. It will not listen on 0.0.0.0.
The browser sends a folder path (and an optional config path). This
process reads those paths and nothing else, then returns the same
present / missing / wake-up result as the command-line checker.
"""

from __future__ import annotations

import ipaddress
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import check

HOST = "127.0.0.1"
PORT = 8765
PAGE_FILE = Path(__file__).with_name("page.html")
MAX_BODY = 8192


def refuse_unless_loopback(host: str, port: int) -> tuple[str, int]:
    """Reject any address that is not this machine's loopback."""
    if host in {"0.0.0.0", "::", ""}:
        print("error: refusing to listen on all interfaces", file=sys.stderr)
        raise SystemExit(2)
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        print(f"error: refusing to listen on {host}", file=sys.stderr)
        raise SystemExit(2)
    if not address.is_loopback or port != PORT:
        print(f"error: refusing to listen on {host}:{port}", file=sys.stderr)
        raise SystemExit(2)
    return host, port


def evaluate(folder_text: str, config_text: str | None) -> dict:
    """Run the checker on a typed folder. Never lists a directory."""
    folder = Path(folder_text).expanduser()
    if not folder.is_dir():
        return {"code": 2, "error": "That path is not a folder."}

    config_path = None
    if config_text:
        config_path = Path(config_text).expanduser()
        if not config_path.is_file():
            return {"code": 2, "error": "That config path is not a file."}

    try:
        expected = check.load_expected(config_path)
    except check.ConfigError as exc:
        return {"code": 2, "error": str(exc)}

    present, missing = check.collect(folder, expected)
    return {
        "code": 0 if not missing else 1,
        "folder": str(folder),
        "present": [{"name": name, "lines": lines} for name, lines in present],
        "missing": missing,
    }


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args) -> None:
        # Request line only. Do not log folder paths from the body.
        sys.stderr.write("%s %s\n" % (self.address_string(), fmt % args))

    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0]
        if path != "/":
            self._send(404, b"This server only has the one page.\n", "text/plain; charset=utf-8")
            return
        try:
            body = PAGE_FILE.read_bytes()
        except OSError:
            self._send(500, b"page.html is missing next to serve.py.\n", "text/plain; charset=utf-8")
            return
        self._send(200, body, "text/html; charset=utf-8")

    def do_POST(self) -> None:
        if self.path.split("?", 1)[0] != "/check":
            self._send(404, b"Not found.\n", "text/plain; charset=utf-8")
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = -1
        if length < 0 or length > MAX_BODY:
            self._json(400, {"code": 2, "error": "Request is empty or too large."})
            return
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._json(400, {"code": 2, "error": "Send JSON with a folder path."})
            return
        if not isinstance(payload, dict):
            self._json(400, {"code": 2, "error": "Send JSON with a folder path."})
            return
        folder_text = payload.get("folder")
        config_text = payload.get("config")
        if not isinstance(folder_text, str) or not folder_text.strip():
            self._json(400, {"code": 2, "error": "Type a folder path."})
            return
        if config_text is None:
            config_value = None
        elif isinstance(config_text, str):
            config_value = config_text.strip() or None
        else:
            self._json(400, {"code": 2, "error": "Config path must be text."})
            return
        self._json(200, evaluate(folder_text.strip(), config_value))

    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self._send(status, body, "application/json; charset=utf-8")

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; "
            "form-action 'self'; base-uri 'none'",
        )
        self.end_headers()
        self.wfile.write(body)


class LocalServer(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True

    def server_bind(self) -> None:
        super().server_bind()
        host, port = self.server_address[:2]
        bound = ipaddress.ip_address(host)
        if not bound.is_loopback or host == "0.0.0.0" or port != PORT:
            self.server_close()
            print(f"error: refusing to listen on {host}:{port}", file=sys.stderr)
            raise SystemExit(2)


def main() -> int:
    if len(sys.argv) > 1:
        print("error: serve.py takes no arguments. It only listens on 127.0.0.1:8765.", file=sys.stderr)
        return 2
    host, port = refuse_unless_loopback(HOST, PORT)
    if not PAGE_FILE.is_file():
        print(f"error: missing {PAGE_FILE}", file=sys.stderr)
        return 2
    server = LocalServer((host, port), Handler)
    print(f"continuity check page: http://{host}:{port}/")
    print("Only this computer can open it. Ctrl-C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print()
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
