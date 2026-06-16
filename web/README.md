# Add / Edit Fact form (Maike)

A zero-build, single-file form for **humans to add or correct facts** in the vendor-neutral
knowledge store — the "humans + any bot edit one source of truth" path from [`../PLAN.md`](../PLAN.md).

## Files

| File                   | What it is                                                        |
|------------------------|-------------------------------------------------------------------|
| `add-fact.html`        | The form. Open it directly or serve it — no build step.           |
| `sample-memories.json` | Mock data matching the `GET /api/memories` contract. Julian can reuse this for the dashboard. |

## Run it

```bash
# simplest: just open it
open web/add-fact.html

# or serve (needed for the real API + clean fetch of sample data)
python3 -m http.server 5500 --directory web   # then visit http://127.0.0.1:5500/add-fact.html
```

The form probes `http://127.0.0.1:8787/api/memories` (from `.env.example`: `API_HOST`/`API_PORT`).
- **API up** → green pill, loads real facts, `Save` POSTs to the store.
- **API down** → amber "preview mode": still fully usable; `Save` falls back to **Download .md** /
  **Copy markdown** so nothing is lost, and you can drop the file into `memory/` by hand.
- Override the endpoint with `?api=http://host:port`.

## What it does

- **Add / Edit modes.** Edit loads an existing fact, locks the `name` (it's the identity), and
  **bumps `version`** on save. Typing an existing name in Add mode flags the collision.
- **Title → auto-slug** `name` (editable). Live preview of the exact `memory/<name>.md` file and
  the `MEMORY.md` index line it appends.
- **Schema fields** per `PLAN.md`: `name`, `description`, `metadata.{type, source_bot, origin,
  created, version}`, body with `[[related]]` links.
- **Validation**: required title/description/body, kebab-case slug.

## ⚠️ Two shared-contract values to confirm with the team

The form needs to represent **human curation**, which doesn't fit the bot/origin enums. It adds:

- `source_bot: **human**`  (alongside claude | chatgpt | copilot | vally)
- `origin: **manual**`      (alongside conversation | document)

Both are 1-value extensions to the frozen schema. **Quick OK needed** so the dashboard badges and
`memory_write` agree. If rejected, they're one-line changes in the two `<select>`s.

## 🔧 Write route needed from Jenny (`serve_api.py`)

`serve_api.py` is currently read-only `GET`. The form needs a write route:

```
POST /api/memories
Content-Type: application/json

{ "name", "description", "type", "source_bot", "origin", "body", "created", "version" }
```

Behavior: write/overwrite `memory/<name>.md` with the frontmatter above, bump `version` if it
exists, append/update the `MEMORY.md` line. Return 2xx (the saved fact, or `{ "ok": true }`).
This is the same operation as the MCP `memory_write` tool — ideally share that code path.

Until it exists, the form's offline fallback keeps the demo working.

## Branding

Palette is approximate valantic magenta — see `tailwind.config` at the top of `add-fact.html`.
Swap the `brand` hexes for the exact brand values when available.
