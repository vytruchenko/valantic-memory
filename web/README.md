# Capture-a-Fact form (Maike)

A zero-build form for **humans to add or correct facts** in the vendor-neutral
knowledge store — the "humans + any bot edit one source of truth" path from
[`../PLAN.md`](../PLAN.md). You **tell it a fact in plain language**; Claude
extracts the structured fields; you review and save.

## Files

| File                   | What it is                                                            |
|------------------------|-----------------------------------------------------------------------|
| `add-fact.html`        | The form — zero-build, single file. Open directly or serve it.        |
| `extract_server.py`    | Local backend: `POST /api/extract` → Claude → structured fields. Keeps the API key server-side. |
| `sample-memories.json` | Mock matching the `GET /api/memories` contract (Julian can reuse).    |

## Run it

```bash
# 1. extraction server (key stays here, never in the browser)
cd web
cp ../.env.example ../.env          # then put your key in ../.env
../.venv/bin/python extract_server.py   # http://127.0.0.1:8788

# 2. the form — open directly, or serve for clean cross-origin fetch
open add-fact.html
# or:  python3 -m http.server 5500   →  http://127.0.0.1:5500/add-fact.html
```

Two status pills (top-right):
- **extraction ready / offline** — is `extract_server.py` up? Offline ⇒ ✨ button
  disabled, manual entry still works.
- **store connected / offline** — is Jenny's `serve_api.py` up? Offline ⇒ Save
  falls back to **Download .md** / **Copy markdown** so nothing is lost.

Endpoint overrides: `?extract=http://host:port` and `?api=http://host:port`.

## The flow

1. **Type a fact or mini-story** in the big box (placeholders for anything sensitive).
2. **✨ Extract fields** → Claude returns `name` slug, `description`, `type`,
   `practice`, `body`, and `related[]`; the review fields fill in.
3. **Review & save** — glance, tweak, hit Save. `source_bot`/`origin` default to
   `human`/`manual` for form capture (editable). Editing an existing slug bumps `version`.
4. Live preview shows the exact `memory/<name>.md` file and the `MEMORY.md` line.

## Extraction (`extract_server.py`)

- **Model: Claude Haiku 4.5** (`claude-haiku-4-5`) — fast + cheap; ~a fraction of a
  cent per fact. One-line swap via `EXTRACT_MODEL` (its own var, independent of
  the agent's `ANTHROPIC_MODEL`) to Sonnet 4.6 / Opus 4.8 if quality needs it.
- **Structured outputs** (`output_config.format` + JSON schema, enums for `type`) —
  the response is guaranteed schema-valid; no parsing or repair.
- **Key stays server-side.** The form never holds an API key. (The API *can* be
  called from the browser with `anthropic-dangerous-direct-browser-access`, but
  that exposes the key — not used here.)
- Standalone for the demo; the handler folds cleanly into Jenny's `serve_api.py`.

## Schema fields

Per `PLAN.md` + the upgraded sample data: `name`, `description`, and under
`metadata`: `type`, **`practice`** (valantic practice area — SAP Core Business
Services, Strategy & Transformation, Transformation & Security, Customer
Experience, Data & AI, …), `source_bot`, `origin`, `created`, `version`. Body
carries `[[related]]` links.

## ⚠️ Shared-contract values to confirm with the team

The form represents **human curation**, which doesn't fit the bot/origin enums:

- `source_bot: **human**` (alongside claude | chatgpt | copilot | vally)
- `origin: **manual**` (alongside conversation | document)

Both are 1-value enum extensions — quick OK needed so badges + `memory_write` agree.

## 🔧 Write route needed from Jenny (`serve_api.py`)

`serve_api.py` is read-only `GET`. The form needs:

```
POST /api/memories
Content-Type: application/json

{ "name", "description", "type", "practice", "source_bot", "origin", "body", "created", "version" }
```

Write/overwrite `memory/<name>.md` with the frontmatter above (note `practice`
under `metadata`), bump `version` if it exists, update the `MEMORY.md` line,
return 2xx. Same operation as the MCP `memory_write` tool — ideally one code path.
Until it exists, the form's offline fallback keeps the demo working.

## Branding

Palette is approximate valantic magenta — see `tailwind.config` at the top of
`add-fact.html`. Swap the `brand` hexes for the exact brand values.
