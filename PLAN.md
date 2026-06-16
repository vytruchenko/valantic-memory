# valantic Knowledge Layer — 90-min Hackathon Plan

## Context

**Goal:** Build valantic's **company brain** — a *persistent, vendor-neutral memory / knowledge layer*
that any assistant can read and write — Claude (primary), Copilot, ChatGPT, and the internal **Vally**
bot.

**The tangible problem (internal delivery & staffing):** valantic delivers transformation end to end —
strategy, security, SAP, data & AI, customer experience. The hard-won knowledge of *how we deliver*
(which migration path worked, who the internal expert is, which accelerator to reuse, what we
under-estimated last time) lives in people's heads and is scattered across four different AI
assistants with **zero shared memory**. So consultants re-solve solved problems. The company brain
captures that knowledge once, in any assistant, and makes it reusable by everyone. The golden-thread
storyline for the live demo is in [`demo-script.md`](./demo-script.md).

**Why the existing repo doesn't get us there:** the current code (`create_agent.py`,
`run_session_*.py`) is built on Claude's **managed Memory tool** — a cloud store at
`/mnt/memory/` that only Anthropic agents can reach. That's vendor-locked. A cross-chatbot
layer needs (1) a store no single vendor owns and (2) one shared access protocol.

**The architecture that wins:** a **markdown + YAML-frontmatter store in git** (human-readable,
diffable, auditable, vendor-neutral source of truth) exposed through **one MCP server**.
MCP is the interop standard: Claude supports it natively, ChatGPT via custom connectors,
Copilot Studio as a tool source, and Vally can call the same endpoint. **One server, every bot
gets the same memory.** We prove it live with Claude and show the rest is just config.

**Decisions locked with the team:** one deep live demo · live bot = Claude Desktop/Code ·
seed with real valantic knowledge, **sanitized to placeholders** (`<kunde>`, `<host>`,
`<secret>` — no customer names, prod IPs, or secrets, per org policy).

---

## Architecture (3 layers)

```
  Claude / ChatGPT / Copilot / Vally          ← any MCP-capable client
                 │  (MCP protocol — the one integration point)
        ┌────────▼─────────┐
        │   MCP server     │  tools: memory_search, memory_write,
        │  (Python, stdio) │         memory_list, memory_get
        └────────┬─────────┘
                 │  reads/writes plain files
        ┌────────▼─────────┐        ┌──────────────────┐
        │  memory/  (git)  │◄───────│  REST: /api/...  │──► Dashboard (web)
        │  *.md + frontmatter        │  (read-only JSON)│     knowledge cards,
        │  MEMORY.md index │        └──────────────────┘     provenance, search
        └──────────────────┘
```

The MCP server and the REST/dashboard read the **same markdown files** — so the dashboard shows,
in real time, whatever any bot writes. That shared store *is* the "cross-chatbot" proof.

### Fact file schema (one fact per file, in `memory/`)
```markdown
---
name: cra-gap-assessment-template
description: Where the CRA gap-assessment template lives and who owns it
metadata:
  type: reference        # user | feedback | project | reference
  source_bot: claude     # claude | chatgpt | copilot | vally  ← provenance
  created: 2026-06-16
  version: 1
---
The CRA (EU Cyber Resilience Act) gap-assessment template is at <path>. Owner: <person>.
Related: [[nis2-scope-checklist]]
```
`MEMORY.md` = one-line index per fact (the lightweight recall layer).
This reuses the exact frontmatter pattern already used in the user's Claude memory — proven format.

---

## Team split (parallel from minute ~10)

**The unblocker:** in the first 10 minutes, freeze two contracts so all three work in parallel:
1. the **fact-file schema** above, and
2. the **REST JSON shape**: `GET /api/memories` → `[{name, description, type, source_bot, created, version, body}]`.
Once those are fixed, the dashboard team mocks against the JSON; the server team builds for real.

| Who | Workstream | Deliverable |
|-----|-----------|-------------|
| **Jenny** (technical) | Store schema + MCP server + wire into Claude live | `mcp_server.py`, `serve_api.py`, `.mcp.json`/Claude config, seeded `memory/` |
| **Julian** (frontend) | Knowledge dashboard | Card grid, filter by type/`source_bot`, search box, provenance badges, contradiction flag |
| **Maike** (frontend + pitch) | Capture/curate UX + pitch | "Add/edit fact" form, cross-bot config diagram, 3-min demo script, slides (valantic brand colors) |
| **Philip** (floater, optional) | Content + demo QA | Seed/sanitize the valantic facts, run the demo dry-runs, simulate a 2nd bot writing |

### Who does what — minute-by-minute

**All four together (0–10 min):** agree the fact-file schema + the `/api/memories` JSON shape,
and the demo story (which valantic fact gets "taught" live). Then split.

**Jenny — the engine (10–90):**
- 10–35: `mcp_server.py` with `memory_search` / `memory_write` / `memory_list` / `memory_get`.
- 35–50: seed `memory/` with ~6–8 sanitized facts (incl. 1 tagged `chatgpt`, 1 `vally`).
- 50–65: wire server into Claude via `.mcp.json`; teach-a-fact round-trip working.
- 65–80: `serve_api.py` (`GET /api/memories`) so the dashboard has live data.
- 80–90: rehearse the live `memory_write` with Maike.

**Julian — the dashboard (10–90):**
- 10–20: scaffold app, mock against the JSON contract.
- 20–55: card grid + search + filter by `type`/`source_bot` + provenance badges.
- 55–70: swap mock → real `/api/memories`; contradiction flag (two facts, same topic).
- 70–90: valantic-brand polish; make it projector-legible.

**Maike — capture UX + pitch (10–90):**
- 10–35: "Add/edit fact" form writing to the store (or a clean static mock if time-boxed).
- 35–60: cross-bot config diagram + the 3 connector snippets (ChatGPT / Copilot / Vally).
- 60–80: slides + write the 3-min demo script.
- 80–90: drive the run-through with Jenny.

**Philip — content + QA (if available, 10–90):**
- 10–40: draft + sanitize the ~6–8 seed facts (CRA / NIS2 / IEC 62443 / onboarding pointers),
  feed them to Jenny for `memory/`. Compliance specifics → cite "ask CISO", don't invent policy.
- 40–70: be the test user — teach Claude facts, confirm files land, catch rough edges.
- 70–90: own the "second bot" bit — write/seed a `source_bot: chatgpt` fact so the cross-bot
  story is concrete on the dashboard. Backup demo driver if someone's hands are full.
- *If Philip can't join:* Jenny absorbs seeding, Maike absorbs demo QA.

---

## Build steps

### Layer 1 — Store + MCP server (Jenny, critical path)
- **New** `mcp_server.py` using the official `mcp` Python SDK (`pip install mcp`) with FastMCP.
  Tools over the `memory/` dir:
  - `memory_search(query)` — load all `*.md`, rank by keyword overlap on frontmatter
    `description` + body; return top matches. (Keep it simple — no embeddings unless time.)
  - `memory_write(name, description, type, body, source_bot)` — write/overwrite the fact file
    (bump `version` if it exists) and update `MEMORY.md`. Stamp `created` from a passed-in date
    (avoid runtime clock issues).
  - `memory_list()` and `memory_get(name)`.
- Transport: **stdio** (no hosting needed for the live Claude demo).
- `memory/` is **already seeded** with 8 sanitized valantic delivery facts spanning every practice
  area (SAP, Strategy & Transformation, Transformation & Security, Data & AI, Customer Experience) and
  every assistant as provenance (`claude`/`copilot`/`chatgpt`/`vally`/`human`), plus `MEMORY.md`. These
  are the cards the dashboard shows in the demo; `web/sample-memories.json` mirrors them for frontend
  dev. The **one fact written live** in the demo (`sap-order-integration-peak-sizing`) is intentionally
  *not* seeded — Claude writes it on stage. Reshape the source docs in `synthetic-data/round1`–`round2`
  if you want to regenerate seeds.
- Set aside (do not delete) the managed-memory scripts — out of scope for the portable layer.

### Layer 2 — Wire into Claude LIVE (Jenny)
- Add the server to Claude Code via `.mcp.json` in the project root (or Claude Desktop's
  `claude_desktop_config.json`). Verify tools appear, then **teach it a fact in chat** →
  confirm a new file lands in `memory/`.

### Layer 3 — REST + Dashboard (Julian, Maike)
- **New** `serve_api.py` (FastAPI or stdlib `http.server`) — read-only `GET /api/memories`
  returning the JSON contract above. Decouples the frontend from MCP internals.
- Dashboard (their stack of choice — Vite/React, or zero-build HTML + Tailwind CDN for speed):
  card grid, search, filter by `type` and `source_bot`, **provenance badge per card**
  (claude/chatgpt/copilot/vally), and a flag when two facts share a `name`/topic (contradiction).
- "Add fact" form POSTs to the same store — proves humans + any bot edit one source of truth.

### The cross-bot moment (Maike)
- We only wire Claude live, but to make portability *visceral*: write one seed fact with
  `source_bot: chatgpt` and one with `source_bot: vally`. The dashboard renders all sources
  uniformly → the layer is genuinely bot-neutral.
- Slide/diagram: "Point any MCP client at this one server." Show the 3 config snippets
  (ChatGPT custom connector, Copilot Studio tool, Vally MCP client) as evidence it's *just config*.

---

## Demo script (3 min) — golden thread

Full presenter version with exact lines in [`demo-script.md`](./demo-script.md). The beats:

1. **Frame the pain (one slide):** four assistants across the firm, zero shared memory, every
   project's lessons die in a project channel. Show the populated dashboard — "valantic's company brain."
2. **Recall —** *Lena* is scoping an S/4HANA + commerce retail engagement. In **Claude** she asks
   "has valantic done this before, who do I pull in, what can I reuse?" → `memory_search` returns three
   colleagues' past-engagement facts (brownfield playbook, the integration expert, the estimate
   contingency). *Knowledge she'd otherwise spend days chasing.*
3. **Capture —** she tells Claude to remember a new lesson (size SAP order-integration for peak load).
   → `memory_write`. Refresh dashboard → new card, badge **"taught by Claude,"** by Lena.
4. **Cross-bot —** point to seeded cards from **Copilot / ChatGPT / Vally**: "four assistants, one
   brain — vendor-neutral by design."
5. **Govern —** a lead edits the `sap-commerce-integration-expert` card (post-re-org: Marco → Priya);
   a fresh Claude session recalls Priya. **Persistent, shared, governed.**
6. **Close —** config diagram: Copilot/ChatGPT/Vally = config, not rebuild. "Every engagement,
   captured once, reusable by everyone, through whatever assistant they already use."

---

## Verification
- **MCP live:** in Claude, run a prompt that triggers `memory_write`; confirm a new `memory/*.md`
  file with correct frontmatter, and a new line in `MEMORY.md`.
- **Recall:** new Claude session → `memory_search` returns the seeded/written fact.
- **Dashboard:** `GET /api/memories` returns all facts; cards render with correct
  `source_bot` badges; filter + search work; human-added fact appears in the store on disk.
- **Round-trip:** human edits a fact in dashboard → Claude session reflects the edit.

## Risks / cut-lines (protect the live demo)
- If MCP wiring stalls >20 min: fall back to a CLI `teach.py` that calls `memory_write` directly,
  and present MCP as "the same function, exposed to bots." Demo still works end-to-end.
- Keep search trivial (keyword). No embeddings, no DB, no auth — out of scope for 90 min.
- Sanitize as you seed: placeholders only. Compliance specifics → defer to CISO, not invented policy.
