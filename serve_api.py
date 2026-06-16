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
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

# Reuse the exact same code the MCP server uses — one write path for bots AND humans.
from mcp_server import _all_facts, _flatten, _parse_fact, MEMORY_DIR, _slugify, memory_write

# Default 8787 to match the add-fact form (web/add-fact.html) and .env.example.
HOST = os.environ.get("API_HOST", "127.0.0.1")
PORT = int(os.environ.get("API_PORT", "8787"))


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
        # CORS so the form/dashboard on any localhost port (or file://) can read + write.
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        # CORS preflight for the form's POST (Content-Type: application/json triggers it).
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_POST(self) -> None:
        path = urlparse(self.path).path.rstrip("/")
        if path != "/api/memories":
            self._send({"error": "not found", "path": path}, status=404)
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(length) or b"{}")
        except (ValueError, json.JSONDecodeError) as exc:
            self._send({"error": f"bad JSON: {exc}"}, status=400)
            return

        name = (data.get("name") or "").strip()
        if not name or not (data.get("body") or "").strip():
            self._send({"error": "name and body are required"}, status=400)
            return

        # Same write path as the MCP memory_write tool — humans and bots, one source of truth.
        # The server is authoritative on version (bumps if the fact already exists).
        memory_write(
            name=name,
            description=data.get("description", ""),
            body=data.get("body", ""),
            type=data.get("type", "reference"),
            source_bot=data.get("source_bot", "human"),
            origin=data.get("origin", "manual"),
            created=data.get("created", ""),
            practice=data.get("practice", ""),
        )
        saved = get_memory(name)
        self._send(saved, status=201)

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
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"valantic Knowledge Layer API → http://{HOST}:{PORT}/api/memories")
    print(f"  GET  /api/memories        list facts")
    print(f"  POST /api/memories        add/update a fact (form + bots, shared write path)")
    print("Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped.")
        server.shutdown()


if __name__ == "__main__":
    main()
