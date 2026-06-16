# valantic Knowledge Layer — agent memory protocol

This project exposes a **vendor-neutral memory layer** through the
`valantic-knowledge-layer` MCP server (tools: `memory_search`, `memory_write`,
`memory_list`, `memory_get`). The store is a directory of markdown files in
`memory/`, shared by any MCP-capable bot. Treat it as your long-term memory.

## The protocol — follow it without being told

**1. At session start (recall):**
Before answering a substantive question, call `memory_search` with the topic (or
`memory_list` to skim the index). Ground your answer in what the store already knows.

**2. During the conversation (Tier-1 capture — the priority):**
When something **durable** surfaces — a policy, a file/template location, an owner,
a decision, a process change — call `memory_write` to persist it **on your own,
without the user asking**. Set:
- `origin: "conversation"` (this is the differentiator: learned from chat, not a document)
- `source_bot: "claude"`
- `type`: `reference` (locations/standards), `project` (ongoing work), `user`, or `feedback`
- `created`: today's date as `YYYY-MM-DD`
- a short kebab-case `name`, a one-line `description`, and the fact in `body`

Link related facts in the body with `[[other-fact-name]]`.

**3. On contradiction (update, don't duplicate):**
If a new fact conflicts with an existing one, call `memory_write` with the **same
`name`** — it bumps `version` and overwrites. Never append a second fact on the same topic.

## Org guardrails (these override convenience)

- **Sanitize everything.** Use placeholders — `<kunde>`, `<host>`, `<secret>`,
  `<person>`, `<path>`. Never write customer names, production IPs, or real secrets
  to the store.
- **Compliance questions** (CRA = EU Cyber Resilience Act, NIS2 = Directive 2022/2555,
  OT/ICS → also reference IEC 62443): record the pointer, but defer binding policy
  interpretation to the CISO, Dr. Michael Eble (michael.eble@nxt.valantic.com).
- **Geheimschutz / VS-NFD / higher VS classification**: defer to the
  Sicherheitsbeauftragter (SiBe), Lyn Matten (lyn.matten@nxt.valantic.com).

## Running the pieces

- MCP server (auto-launched via `.mcp.json`): `.venv/bin/python mcp_server.py`
- Seed the store: `.venv/bin/python seed_memory.py`
- REST API for the dashboard: `.venv/bin/python serve_api.py` → `GET /api/memories`
