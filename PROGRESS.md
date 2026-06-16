# PROGRESS — engine workstream (branch `engine`)

What we built for the valantic Knowledge Layer (Jenny / the engine — the critical path in
[PLAN.md](PLAN.md)). Status: **MCP server, store, REST read+write all done and verified;
Maike's form + Julian's dashboard run live against it. Next: host it (Vercel + Azure) so it's shared.**

## Done

### 1. MCP server — [mcp_server.py](mcp_server.py)
Vendor-neutral memory layer over a git-backed markdown store (`memory/`), using the official
`mcp` Python SDK (FastMCP, **stdio** transport). Four tools:
- `memory_search(query)` — keyword recall over `description` + body, ranked.
- `memory_write(name, description, body, type, source_bot, origin, created, practice)` —
  create/overwrite a fact, **auto-bump `version`** on update, rebuild `MEMORY.md`.
- `memory_list()` — index without bodies. · `memory_get(name)` — one full fact.

**Tier-1 capture protocol baked into the server** (not a vendor file, so it's portable to any
client with zero per-user setup): the FastMCP `instructions` field carries the full
recall → capture → update protocol + sanitization/CISO/SiBe guardrails, and the tool
descriptions are imperative (`memory_search`: "CALL THIS FIRST"; `memory_write`: "CALL THIS
PROACTIVELY, without being asked"). [CLAUDE.md](CLAUDE.md) is a Claude-Code-only mirror, not required.

Verified: 4 tools register; MCP `initialize` handshake returns `instructions` populated;
search ranks; update bumps version. **Proven live in Claude Desktop** — from a normal chat it
autonomously updated an existing fact (version bump + `origin: conversation`), the
update-don't-duplicate path, with no global config.

### 2. Store content — [memory/](memory/) (8 facts) + [memory/MEMORY.md](memory/MEMORY.md)
Adopted **Maike's "valantic Company Brain"** seed set (merged from `storyline`): S/4HANA
playbook, transformation estimation, CRA template, NIS2 scoping, commerce UX kit, data-platform
architecture, SAP-commerce expert, engagement-retro. All sanitized to placeholders
(`<kunde>`, `<host>`, `<path>`). Cross-bot provenance across `claude / chatgpt / copilot /
vally / human`. `MEMORY.md` is **machine-generated** in the Company Brain style
(`name — description (Practice · bot)`) so any bot/form write keeps it current.
My earlier generic security/SRE seed facts were dropped (storyline is canon).

### 3. Wired into Claude — [.mcp.json](.mcp.json) + Claude Desktop config
Registered for Claude Code (`.mcp.json`) and Claude Desktop (`claude_desktop_config.json`),
absolute venv path → launches on open. Tier-1 capture verified end-to-end (see §1).

### 4. REST API (read + write) — [serve_api.py](serve_api.py)
Stdlib `http.server`, reads/writes the **same** `memory/` files as the MCP server — one write
path for bots AND humans. Port **8787** (matches the form + `.env.example`), host/port from env.
- `GET /api/memories`, `GET /api/memories/<name>`, `GET /health`
- `POST /api/memories` — add/update a fact (Maike's form saves through this); server is
  authoritative on `version`. CORS + `OPTIONS` preflight so the browser can write cross-origin.
- Contract: `[{name, description, type, practice, source_bot, origin, created, version, body}]`

Verified: GET 200; OPTIONS preflight 204; POST creates a fact (preserving `practice` +
`human`/`manual`) and re-POST bumps version 1→2.

### 5. Schema extensions for human curation
Added the two enum values Maike's add-fact form needs (so form + dashboard + `memory_write`
agree): `source_bot: human` and `origin: manual`. Added a `practice` field to the schema,
contract, and index; backfilled `practice` into all 8 facts (it had only lived in the index).

### 6. Frontends verified live against the engine
- **Julian's dashboard** (`dashboard/index.html`, on `feature/dashboard`) — renders the 8 live
  facts from `GET /api/memories` with practice/source_bot badges (flip `USE_MOCK = false`).
- **Maike's add-fact form** ([web/add-fact.html](web/add-fact.html)) — green pill, `Save`
  writes a real `memory/*.md` via `POST`. (Her optional `web/extract_server.py` auto-fill helper
  is the **only** component that uses the Anthropic key; the store + dashboard use no secrets.)

## Hosting plan (decided, not yet built)
- **Frontends (dashboard + form) → Vercel** — static, no secrets.
- **API + MCP → Azure** (Jenny has admin) — one app serving `GET/POST /api/memories` for the
  frontend AND a **remote HTTP MCP endpoint** (`/mcp`) for bots. Store on Azure Files
  (persistent, shared) so the existing file code runs unchanged. **No Entra/auth for now** —
  open read/write for the demo; harden later.
- **Shared Claude access:** once `/mcp` is remote (HTTP), Jenny's and Maike's Claude Desktop
  (and Vally/ChatGPT) add the **same Azure `/mcp` URL** as a custom connector → one shared brain.

### Code changes still needed for Azure (small)
1. MCP server: add **Streamable-HTTP transport** option (`streamable_http_app()` is available)
   alongside the local stdio mode.
2. Single deployable that mounts `/mcp` (FastMCP) + `/api/memories` (REST) under one ASGI app
   (uvicorn). `MEMORY_DIR` already reads from env.
3. `DEPLOY.md` with the `az` steps + how each person adds the connector to Claude Desktop.

## Environment note
System Python is 3.9 (too old for the `mcp` SDK, needs 3.10+). Created a `.venv` via `uv`
(Python 3.12). Run everything with `.venv/bin/python`.

## How to run locally
```bash
uv venv --python 3.12 && uv pip install mcp pyyaml      # one-time
.venv/bin/python serve_api.py                            # REST + write API on :8787
.venv/bin/python -m http.server 5500 --directory web     # Maike's form  → :5500/add-fact.html
# Julian's dashboard lives on the feature/dashboard branch (dashboard/index.html)
# MCP server auto-launches in Claude Code / Desktop via the registered config
```
