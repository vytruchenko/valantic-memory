# DEPLOY — click-by-click (Azure Portal + Vercel + Claude)

No command line. Everything below is done in a browser. Goal: one **shared** Company Brain that
the team's frontends and **everyone's Claude** use.

- **API + remote MCP → Azure App Service** ([app.py](app.py)) — serves `/api/memories` (for the
  frontends) and `/mcp` (the endpoint Claude/Vally/ChatGPT connect to). Store on Azure Files so it
  persists and is shared.
- **Frontends (dashboard + form) → Vercel.**
- **Access is OPEN for the demo** (no login). Anyone with the URL can read/write. Lock it down
  before real use — see "Hardening" at the end.

> Menu labels in the Azure Portal shift slightly over time; the blade names below are current as
> of writing. If a label differs, use the search bar at the top of the Portal.

---

## Part 1 — Azure: host the API + MCP (≈20 min of clicks)

### 1.1 Create the Web App
1. Go to **portal.azure.com** → top search bar → **App Services** → **+ Create** → **Web App**.
2. **Basics** tab:
   - **Subscription:** your valantic subscription.
   - **Resource Group:** **Create new** → `valantic-brain-rg`.
   - **Name:** `valantic-brain` → this becomes `https://valantic-brain.azurewebsites.net`
     (if taken, pick another; remember it).
   - **Publish:** `Code`
   - **Runtime stack:** `Python 3.12`
   - **Operating System:** `Linux`
   - **Region:** `West Europe`
   - **Pricing plan:** click **Change size** → **Basic B1** (don't use Free F1 — storage mounts
     need Basic+).
3. **Review + create** → **Create**. Wait for "Your deployment is complete" → **Go to resource**.

### 1.2 Create the storage for the shared facts (Azure Files)
1. Portal search → **Storage accounts** → **+ Create**.
2. Same **Resource Group** (`valantic-brain-rg`); **Storage account name:** something unique and
   lowercase like `valanticbrainstore`; **Region:** `West Europe`; **Redundancy:** `LRS`.
3. **Review + create** → **Create** → **Go to resource**.
4. In the storage account left menu → **Data storage → File shares** → **+ File share** →
   **Name:** `memory` → **Create**.
5. Open the **memory** share → **Upload** → upload the fact files from the repo's `memory/` folder
   (all `*.md` including `MEMORY.md`).
   - To get the files without git: on GitHub open the repo → **Code ▾ → Download ZIP**, unzip, and
     upload everything inside the `memory/` folder.

### 1.3 Mount that share into the Web App
1. Back to **App Services → valantic-brain** → left menu **Settings → Configuration** →
   **Path mappings** tab → **+ New Azure Storage Mount**.
2. Fill in:
   - **Name:** `memstore`
   - **Storage account:** `valanticbrainstore`
   - **Storage type:** `Azure Files`
   - **Storage container / Share name:** `memory`
   - **Mount path:** `/mounts/memory`
3. **OK** → **Save** (top of the Configuration page).

### 1.4 Tell the app where the store is + how to start
1. Same **Configuration** page → **Application settings** tab → **+ New application setting**:
   - **Name:** `MEMORY_DIR`  **Value:** `/mounts/memory`  → **OK**
   - Add another: **Name:** `SCM_DO_BUILD_DURING_DEPLOYMENT`  **Value:** `true`  → **OK**
   - **Save**.
2. **Configuration → General settings** tab → **Startup Command:**
   ```
   python -m uvicorn app:app --host 0.0.0.0 --port 8000
   ```
   → **Save**. (One process on purpose — keeps MCP sessions consistent.)

### 1.5 Deploy the code straight from GitHub (auto-builds on every push)
1. App Service left menu → **Deployment → Deployment Center**.
2. **Source:** `GitHub` → **Authorize** (sign in to GitHub if asked).
3. **Organization:** your account · **Repository:** `valantic-memory` ·
   **Branch:** `main` (after PR #1 is merged) — or `engine` to deploy now.
4. **Save**. Azure adds a GitHub Action that installs `requirements.txt` and deploys.
5. Watch **Deployment Center → Logs** until the run succeeds (first build ~3–5 min).

### 1.6 Verify it's live
Open these in the browser (replace the name if you changed it):
- `https://valantic-brain.azurewebsites.net/health` → should show `{"status": "ok", "count": 8}`
- `https://valantic-brain.azurewebsites.net/api/memories` → the 8 facts as JSON

If `/health` works, the MCP endpoint at `/mcp` is live too.

---

## Part 2 — Vercel: host the frontends (≈5 min)

1. Go to **vercel.com** → **Sign up / Log in with GitHub**.
2. **Add New… → Project** → **Import** the `valantic-memory` repo.
3. In project setup:
   - **Framework Preset:** `Other`
   - **Root Directory:** click **Edit** → choose the frontend folder
     (`web` for Maike's form; do a second project with `dashboard` for Julian's dashboard).
   - Leave Build Command empty (these are static).
4. **Deploy** → you'll get a `https://<project>.vercel.app` URL.

**Point the frontend at the Azure API** (so it shows live shared data):
- **Form** (no code change needed): open it as
  `https://<form>.vercel.app/add-fact.html?api=https://valantic-brain.azurewebsites.net`
- **Dashboard:** one-line edit (Julian) — set
  `API_URL = 'https://valantic-brain.azurewebsites.net/api/memories'` and `USE_MOCK = false` in
  `dashboard/index.html`, commit, and Vercel redeploys automatically.

---

## Part 3 — Connect it to YOUR Claude (the payoff)

Once Part 1 shows `/health` working, add the connector. **Everyone who adds the same URL shares
the same brain** — so you and Maike both do this.

### Claude Desktop
1. Open **Claude Desktop** → **Settings** (bottom-left, your name) → **Connectors**.
2. Click **Add custom connector**.
3. Fill in:
   - **Name:** `valantic-brain`
   - **URL:** `https://valantic-brain.azurewebsites.net/mcp`
4. **Add**. The `memory_*` tools appear. The first time Claude uses one, click **Allow**.
5. Test: ask *"search the valantic brain — what do we know about S/4HANA?"* → it calls
   `memory_search` and answers from the shared store. Mention a durable fact in chat and it will
   save it on its own (Tier-1).

> **If the custom-connector dialog requires OAuth / won't accept a plain URL**, use the bridge
> instead: Claude Desktop → Settings → Developer → **Edit Config**, and add this, then fully quit
> (⌘Q) and reopen Claude:
> ```json
> {
>   "mcpServers": {
>     "valantic-brain": {
>       "command": "npx",
>       "args": ["-y", "mcp-remote", "https://valantic-brain.azurewebsites.net/mcp"]
>     }
>   }
> }
> ```
> (Requires Node.js installed — `npx` comes with it.)

### Maike's Claude / Vally / ChatGPT
Exactly the same: add `https://valantic-brain.azurewebsites.net/mcp` as a custom connector /
remote MCP server. Same URL = same shared store.

---

## No-deploy shortcut (if Azure isn't ready by demo time)
Run the app on one laptop and expose it with a tunnel — no Portal needed:
`cloudflared tunnel --url http://localhost:8787` gives a public `https://…trycloudflare.com` URL.
Use that URL in Part 2 and Part 3. Same code, zero infra (that laptop just has to stay on).

---

## Hardening (do before using it for real — not for the demo)
- **Auth:** App Service → **Settings → Authentication → Add identity provider → Microsoft (Entra
  ID)** so only valantic logins reach the app. This is the main thing to add.
- **Audit:** optionally make the store a git repo and commit on write for full history.
- **Secrets:** the API/MCP use none. If you later deploy `web/extract_server.py`, put
  `ANTHROPIC_API_KEY` in **Configuration → Application settings** (server-side; never in frontend code).
