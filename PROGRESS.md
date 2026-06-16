# PROGRESS — engine workstream (branch `engine`)

What we built so far for the valantic Knowledge Layer (Jenny / the engine, the
critical path in [PLAN.md](PLAN.md)). Status: **Layers 1–2 done, REST done.**

## Done

### 1. MCP server — [mcp_server.py](mcp_server.py)
Vendor-neutral memory layer over a git-backed markdown store (`memory/`), using the
official `mcp` Python SDK (FastMCP, **stdio** transport). Four tools:
- `memory_search(query)` — keyword recall over frontmatter `description` + body, ranked.
- `memory_write(name, description, body, type, source_bot, origin, created)` — create/
  overwrite a fact, **bump `version`** on update, rebuild `MEMORY.md`. `origin` records
  Tier-1 conversational capture vs document ingestion; `created` is passed in (no runtime clock).
- `memory_list()` — index without bodies.
- `memory_get(name)` — one full fact.

Verified: all four tools register and run; search ranks correctly; update bumps version.

### 2. Seeded store — [memory/](memory/) (8 facts) + [seed_memory.py](seed_memory.py)
8 sanitized facts (placeholders only — `<kunde>`, `<host>`, `<person>`, `<path>`):
CRA template, NIS2 scope, IEC 62443 OT baseline, prod-access flow, on-call owner,
onboarding pointers, VS-NFD contact, incident comms. **2 are cross-bot** — one
`source_bot: chatgpt`, one `vally` — so the dashboard proves the store is bot-neutral.
Compliance facts defer to the CISO / SiBe rather than inventing policy.
`MEMORY.md` index auto-generated.

### 3. Wired into Claude + capture protocol — [.mcp.json](.mcp.json) + [CLAUDE.md](CLAUDE.md)
- `.mcp.json` registers the server for Claude Code (absolute venv path → launches on open).
- `CLAUDE.md` is **the Tier-1 enabler**: the protocol that makes capture autonomous —
  recall at session start, `memory_write(origin: conversation)` mid-chat *without being
  asked*, update-don't-duplicate on contradiction, plus the org sanitization/CISO/SiBe guardrails.

### 4. REST API — [serve_api.py](serve_api.py)
Stdlib `http.server` (no extra deps), reads the **same** `memory/` files the MCP server
writes. Endpoints: `GET /api/memories`, `GET /api/memories/<name>`, `GET /health`. CORS open
for the dashboard. Returns the frozen JSON contract:
`[{name, description, type, source_bot, origin, created, version, body}]`.

Verified: `/health` → 8; list returns the contract; single fetch + 404 work; a live
`origin: conversation` write appeared in the API with **no restart** (8→9, then cleaned to 8).

## Environment note
System Python is 3.9, too old for the `mcp` SDK (needs 3.10+). Created a `.venv` via `uv`
(Python 3.12). Run everything with `.venv/bin/python`. `requirements.txt` updated.

## How to run
```bash
uv venv --python 3.12 && uv pip install mcp pyyaml   # one-time setup
.venv/bin/python seed_memory.py                       # seed the store
.venv/bin/python serve_api.py                         # REST for dashboard (:8000)
# MCP server auto-launches in Claude Code via .mcp.json
```

## Next / handoff
- **Live demo wiring:** open this folder in Claude Code, confirm the `memory_*` tools
  appear, run the teach-a-fact round-trip end to end (rehearse with Maike).
- **Dashboard (Julian):** point at `http://127.0.0.1:8000/api/memories` — contract is frozen.
- **Cut-line fallback:** if MCP wiring stalls, a thin CLI wrapper around `memory_write`
  gives the same end-to-end demo (PLAN.md risks section).
