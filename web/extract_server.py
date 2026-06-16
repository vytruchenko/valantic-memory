"""
extract_server.py — turns a free-text fact / mini-story into a structured memory fact.

The "tell it, don't fill it" backend for the Add-Fact form. The browser POSTs a
blob of natural language; this server asks Claude to extract the structured
fields (name slug, description, type, practice, body, related[]) and returns
them as JSON. The API key stays here, server-side — it never touches the browser.

Model:  Claude Haiku 4.5 (fast + cheap; a single fact is a fraction of a cent).
        One-line swap below to Sonnet 4.6 or Opus 4.8 if extraction quality needs it.
Output: structured outputs (output_config.format + JSON schema) — the response is
        guaranteed schema-valid, with enums for `type`, so there's nothing to repair.

Run:
    cd web
    cp ../.env.example ../.env   # then put your key in ../.env  (or: export ANTHROPIC_API_KEY=...)
    python extract_server.py     # listens on http://127.0.0.1:8788

Endpoints:
    POST /api/extract   { "text": "..." }  -> { name, description, type, practice, body, related }
    GET  /api/health                       -> { ok: true, model: "..." }

This is intentionally standalone so the form is demoable without Jenny's
serve_api.py. The same handler folds cleanly into serve_api.py as a route.
"""

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

# Load ../.env if present (python-dotenv is in requirements.txt). Optional.
try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except Exception:
    pass

from anthropic import Anthropic

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5")  # fast + cheap for extraction
HOST = os.environ.get("EXTRACT_HOST", "127.0.0.1")
PORT = int(os.environ.get("EXTRACT_PORT", "8788"))

# valantic practice areas — a hint for the model, NOT a hard enum (the list grows).
KNOWN_PRACTICES = [
    "SAP Core Business Services",
    "Strategy & Transformation",
    "Transformation & Security",
    "Customer Experience",
    "Data & AI",
]

SYSTEM = f"""\
You distill a short free-text note or mini-story into ONE durable knowledge fact
for valantic's vendor-neutral company knowledge layer.

Rules:
- name: a short kebab-case slug that reads as the fact's identity (2-6 words),
  e.g. "cra-gap-assessment-template". Lowercase, hyphens only.
- description: one searchable line — the recall hook. No trailing period needed.
- type: one of reference | user | feedback | project.
    reference = a pointer/standard/asset; user = a person/role; project = an
    ongoing process/initiative; feedback = a lesson learned or guidance.
- practice: the valantic practice area this belongs to. Prefer one of:
    {", ".join(KNOWN_PRACTICES)}. If none fit, use the most accurate short name.
- body: rewrite the note as a clean, self-contained fact (1-4 sentences).
    PRESERVE any placeholders exactly: <kunde>, <host>, <secret>, <path>,
    <commerce-platform>, <team-channel>. NEVER invent real customer names, IPs,
    hostnames, or secrets — if the note has a real one, replace it with the
    matching placeholder. Keep internal people's names if given.
- related: kebab-case slugs of other facts clearly implied; otherwise [].

Extract only what the note supports. Do not fabricate owners, paths, or numbers.
"""

SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "description": "kebab-case slug identity"},
        "description": {"type": "string", "description": "one-line recall hook"},
        "type": {"type": "string", "enum": ["reference", "user", "feedback", "project"]},
        "practice": {"type": "string", "description": "valantic practice area"},
        "body": {"type": "string", "description": "clean fact text; preserve placeholders"},
        "related": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["name", "description", "type", "practice", "body", "related"],
    "additionalProperties": False,
}

_client = Anthropic()  # reads ANTHROPIC_API_KEY from env / .env


def extract(text: str) -> dict:
    resp = _client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM,
        messages=[{"role": "user", "content": f"Note / mini-story:\n\n{text.strip()}"}],
        output_config={"format": {"type": "json_schema", "schema": SCHEMA}},
    )
    # structured outputs guarantee the first text block is schema-valid JSON
    raw = next(b.text for b in resp.content if b.type == "text")
    return json.loads(raw)


class Handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json(self, status: int, payload: dict):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self._cors()
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):  # CORS preflight
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        if self.path.rstrip("/") == "/api/health":
            self._json(200, {"ok": True, "model": MODEL})
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self):
        if self.path.rstrip("/") != "/api/extract":
            self._json(404, {"error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            data = json.loads(self.rfile.read(length) or "{}")
            text = (data.get("text") or "").strip()
            if not text:
                self._json(400, {"error": "missing 'text'"})
                return
            self._json(200, extract(text))
        except Exception as e:  # surface a clean error to the form
            self._json(502, {"error": f"{type(e).__name__}: {e}"})

    def log_message(self, *args):  # quieter console
        pass


def main():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("Set ANTHROPIC_API_KEY (in ../.env or the environment) before running.")
    print(f"extract_server: http://{HOST}:{PORT}  (model: {MODEL})")
    print(f"  POST /api/extract   GET /api/health")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
