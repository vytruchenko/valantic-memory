# DEPLOY — shared hosting (Vercel frontend + Azure API/MCP)

Goal: one **shared** Company Brain that the team's frontends and **everyone's Claude** use.

- **Frontends → Vercel** (dashboard + add-fact form). Static, no secrets.
- **API + MCP → Azure App Service** (Jenny has admin). One app ([app.py](app.py)) serves:
  - `GET/POST /api/memories` — for the Vercel frontends
  - `/mcp` — the **remote Streamable-HTTP MCP endpoint** any Claude/Vally/ChatGPT connects to
  - store on **Azure Files** (persistent + shared) so the file-based code runs unchanged
- **Access is OPEN for the demo** (no auth). Anyone with the URL can read/write. Add Entra ID or a
  token before exposing it beyond the demo — see "Hardening" at the bottom.

Local stdio mode (`python mcp_server.py`, one machine) is unaffected — this is the shared deploy.

---

## A. Azure — API + remote MCP (`app.py`)

Prereqs: `az login`, and pick names. The app listens on port 8000 (uvicorn, single process —
keep it one worker so MCP sessions stay consistent).

```bash
# --- variables ---
RG=valantic-brain-rg
LOC=westeurope
PLAN=valantic-brain-plan
APP=valantic-brain            # → https://valantic-brain.azurewebsites.net
STG=valantcibrainstore$RANDOM # storage acct (lowercase, globally unique)
SHARE=memory

# --- resource group + Linux plan + Python web app ---
az group create -n $RG -l $LOC
az appservice plan create -g $RG -n $PLAN --is-linux --sku B1
az webapp create -g $RG -p $PLAN -n $APP --runtime "PYTHON:3.12"

# --- persistent, shared store via Azure Files ---
az storage account create -g $RG -n $STG -l $LOC --sku Standard_LRS
KEY=$(az storage account keys list -g $RG -n $STG --query "[0].value" -o tsv)
az storage share create --account-name $STG --account-key "$KEY" -n $SHARE
az webapp config storage-account add -g $RG -n $APP \
  --custom-id memstore --storage-type AzureFiles \
  --account-name $STG --share-name $SHARE --access-key "$KEY" \
  --mount-path /mounts/memory

# --- app config: where the store lives + startup command ---
az webapp config appsettings set -g $RG -n $APP --settings \
  MEMORY_DIR=/mounts/memory SCM_DO_BUILD_DURING_DEPLOYMENT=true
az webapp config set -g $RG -n $APP \
  --startup-file "python -m uvicorn app:app --host 0.0.0.0 --port 8000"

# --- deploy the code (from the repo root, on branch engine) ---
az webapp up -g $RG -n $APP --runtime "PYTHON:3.12"   # builds requirements.txt via Oryx
```

**Seed the shared store once** (the mounted share starts empty). Easiest: copy the repo's
`memory/*.md` into the share, e.g. via the Portal's storage browser, or:

```bash
az storage file upload-batch --account-name $STG --account-key "$KEY" \
  -d $SHARE -s ./memory --pattern "*.md"
```

**Verify:**
```bash
curl https://$APP.azurewebsites.net/health          # {"status":"ok","count":8}
curl https://$APP.azurewebsites.net/api/memories     # the 8 facts
```

Notes
- Keep **one worker** (the uvicorn startup above). Multiple gunicorn workers would split the
  in-memory MCP session manager. B1 is plenty for the demo.
- CORS is open in `app.py`, so the Vercel frontends can read + write cross-origin.

---

## B. Vercel — the frontends

Two static files, both currently point at `http://127.0.0.1:8787`. Repoint them at Azure
(edit the constant, or pass `?api=` at runtime):

- Dashboard: `dashboard/index.html` (on `feature/dashboard`) — set
  `const API_URL = 'https://valantic-brain.azurewebsites.net/api/memories'` and `USE_MOCK = false`.
- Form: [web/add-fact.html](web/add-fact.html) — set
  `MEMORIES_BASE = 'https://valantic-brain.azurewebsites.net'` (or open with
  `?api=https://valantic-brain.azurewebsites.net`).

Deploy (each is a static site — no build):
```bash
npm i -g vercel
vercel --prod            # run in the folder containing index.html; set output dir to that folder
```
No environment variables / secrets needed on Vercel — these are read-only-to-the-key frontends;
the only POST goes to the open Azure API.

---

## C. Connect Claude (and Vally/ChatGPT) — the shared brain

Once `/mcp` is live on Azure, **each person** adds the same URL. Both Jenny and Maike doing this
= both Claudes read/write the one store.

**Claude Desktop — native custom connector (try first):**
Settings → **Connectors** → **Add custom connector** →
URL: `https://valantic-brain.azurewebsites.net/mcp` → name it `valantic-brain`.
The `memory_*` tools appear; the server's instructions enable Tier-1 capture automatically.

**Fallback — if the native UI insists on OAuth**, use the `mcp-remote` bridge in
`claude_desktop_config.json` (then fully quit + reopen Claude):
```json
{
  "mcpServers": {
    "valantic-brain": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://valantic-brain.azurewebsites.net/mcp"]
    }
  }
}
```

**Vally / ChatGPT:** same URL as a remote MCP / custom connector — identical store, any client.

**Quick shared option without deploying** (if Azure isn't ready for the demo): run `app.py`
locally and expose it — `cloudflared tunnel --url http://localhost:8787` — then use that public
URL everywhere above. Same code, zero infra.

---

## Hardening (after the demo — do NOT ship open long-term)
- **Auth:** turn on App Service **Easy Auth (Entra ID)** so only valantic identities reach the
  app; issue the bots a token. This is the main thing to add before real use.
- **Audit:** make `/mounts/memory` a git repo and commit on write for full history (optional).
- **Secrets:** the store/API/MCP use none. If you later deploy `web/extract_server.py`, put
  `ANTHROPIC_API_KEY` in App Service settings (server-side env, never in frontend code).
