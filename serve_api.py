"""
valantic Knowledge Layer — read-only REST API for the dashboard.

Decouples the frontend from MCP internals: it reads the SAME markdown files in
`memory/` that the MCP server writes, so the dashboard shows in real time whatever
any bot has written.

Stdlib only (http.server) — no extra deps, no build step.

Endpoints:
  GET /api/memories        -> [{name, description, type, source_bot, origin, created, version, body}]
  GET /api/memories/<name> -> single fact (404 if unknown)
  GET /health              -> {"status": "ok", "count": N}

JSON contract (frozen with the team):
  [{name, description, type, source_bot, origin, created, version, body}]

Run:  .venv/bin/python serve_api.py   (defaults to port 8000)
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

# Reuse the exact same parsing the MCP server uses — one source of truth.
from mcp_server import _all_facts, _flatten, _parse_fact, MEMORY_DIR, _slugify

PORT = 8000


def list_memories() -> list[dict]:
    return [_flatten(f) for f in _all_facts()]


def get_memory(name: str) -> dict | None:
    path = MEMORY_DIR / f"{_slugify(name)}.md"
    if not path.exists():
        return None
    return _flatten(_parse_fact(path))


class Handler(BaseHTTPRequestHandler):
    def _send(self, payload, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        # CORS so a dashboard on any localhost port can fetch live.
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = urlparse(self.path).path.rstrip("/")

        if path == "/health":
            self._send({"status": "ok", "count": len(list_memories())})
            return

        if path == "/api/memories":
            self._send(list_memories())
            return

        if path.startswith("/api/memories/"):
            name = path.rsplit("/", 1)[-1]
            fact = get_memory(name)
            if fact is None:
                self._send({"error": f"no fact named '{name}'"}, status=404)
            else:
                self._send(fact)
            return

        self._send({"error": "not found", "path": path}, status=404)

    def log_message(self, fmt, *args) -> None:  # quieter console
        return


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"valantic Knowledge Layer API → http://127.0.0.1:{PORT}/api/memories")
    print("Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped.")
        server.shutdown()


if __name__ == "__main__":
    main()
