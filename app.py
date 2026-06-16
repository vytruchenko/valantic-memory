"""
valantic Knowledge Layer — unified ASGI app for remote hosting (Azure).

ONE deployable that serves both front doors to the same `memory/` store:
  • /mcp            Streamable-HTTP MCP endpoint  → Claude Desktop, Vally, ChatGPT connect here
  • /api/memories   REST (GET list/detail, POST add/update) → the Vercel dashboard + form
  • /health         liveness probe

Local stdio mode for Claude Code/Desktop on one machine still lives in mcp_server.py
(`python mcp_server.py`). This file is for the SHARED, network-hosted deployment.

Run locally:   .venv/bin/python -m uvicorn app:app --host 0.0.0.0 --port 8787
Azure startup: python -m uvicorn app:app --host 0.0.0.0 --port $PORT
               (or: gunicorn -k uvicorn.workers.UvicornWorker app:app)

The store path comes from MEMORY_DIR (env). On Azure, point it at a mounted Azure Files
share so writes persist and are shared across instances; the file-based code is unchanged.

No secrets are used here. Access is open for the demo — add Entra ID / a token before
exposing it long-term.
"""

from __future__ import annotations

import json

from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

# Reuse the one write path + parsing that the stdio MCP server uses.
from mcp_server import (
    mcp,
    _all_facts,
    _flatten,
    _parse_fact,
    _slugify,
    memory_write,
    MEMORY_DIR,
)


# --- shared store helpers (same shape as serve_api.py) --------------------

def list_memories() -> list[dict]:
    return [_flatten(f) for f in _all_facts()]


def get_memory(name: str) -> dict | None:
    path = MEMORY_DIR / f"{_slugify(name)}.md"
    if not path.exists():
        return None
    return _flatten(_parse_fact(path))


# --- REST handlers --------------------------------------------------------

async def health(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "count": len(list_memories())})


async def memories(request: Request) -> Response:
    if request.method == "GET":
        return JSONResponse(list_memories())

    # POST — add/update a fact (form + bots share this path; server owns version).
    try:
        data = await request.json()
    except (ValueError, json.JSONDecodeError) as exc:
        return JSONResponse({"error": f"bad JSON: {exc}"}, status_code=400)

    name = (data.get("name") or "").strip()
    if not name or not (data.get("body") or "").strip():
        return JSONResponse({"error": "name and body are required"}, status_code=400)

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
    return JSONResponse(get_memory(name), status_code=201)


async def memory_detail(request: Request) -> JSONResponse:
    fact = get_memory(request.path_params["name"])
    if fact is None:
        return JSONResponse({"error": "not found"}, status_code=404)
    return JSONResponse(fact)


# --- app: FastMCP's Streamable-HTTP app, with REST routes + CORS added -----
# Using the FastMCP app object directly keeps its lifespan (the MCP session
# manager) wired correctly; mounting it as a sub-app would not run that lifespan.

app = mcp.streamable_http_app()  # serves the MCP endpoint at /mcp

app.add_route("/health", health, methods=["GET"])
app.add_route("/api/memories", memories, methods=["GET", "POST"])
app.add_route("/api/memories/{name}", memory_detail, methods=["GET"])

# Open CORS so the Vercel dashboard/form (different origin) can read + write.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


if __name__ == "__main__":
    import os
    import uvicorn

    port = int(os.environ.get("PORT", os.environ.get("WEBSITES_PORT", "8787")))
    uvicorn.run(app, host="0.0.0.0", port=port)
