"""
valantic Knowledge Layer — MCP server (Tier 1: conversational capture).

A vendor-neutral memory layer exposed over MCP. The store is a directory of
markdown files with YAML frontmatter (`memory/`), human-readable and git-diffable.
Any MCP-capable client — Claude, ChatGPT, Copilot, Vally — talks to the SAME store
through this one server.

Tools:
  - memory_search(query)                         keyword recall over description + body
  - memory_write(name, description, type, body,  create/overwrite a fact, bump version,
                 source_bot, origin, created)     update MEMORY.md index
  - memory_list()                                index of all facts
  - memory_get(name)                             full fact (frontmatter + body)

Transport: stdio (no hosting needed for the live Claude demo).

Run standalone:  python mcp_server.py
Wire into Claude: see .mcp.json in the project root.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml
from mcp.server.fastmcp import FastMCP

# --- Store location -------------------------------------------------------

MEMORY_DIR = Path(__file__).parent / "memory"
INDEX_FILE = MEMORY_DIR / "MEMORY.md"

VALID_TYPES = {"user", "feedback", "project", "reference"}
VALID_BOTS = {"claude", "chatgpt", "copilot", "vally"}
VALID_ORIGINS = {"conversation", "document"}

# The capture protocol travels WITH the server (not in a vendor file like CLAUDE.md),
# so any MCP client — Claude Desktop, Claude Code, ChatGPT, Vally — receives it on
# connect, with zero per-user setup. Clients that surface server `instructions` inject
# this near system-prompt level; the imperative tool descriptions below reinforce it
# even for clients that don't.
PROTOCOL = """\
You are connected to the valantic Knowledge Layer — a shared, persistent, vendor-neutral
memory store. Treat it as your long-term memory and follow this protocol on EVERY conversation,
without being asked:

1. RECALL FIRST. Before answering a substantive question, call `memory_search` with the topic
   (or `memory_list`). Ground your answer in what the store already knows.

2. CAPTURE PROACTIVELY (the priority). The moment something DURABLE surfaces in the chat — a
   policy, a file/template location, an owner, a decision, a process change — you MUST call
   `memory_write` with origin="conversation", on your own initiative. Do not wait to be told.
   If unsure whether it's worth keeping, keep it.

3. UPDATE, DON'T DUPLICATE. If a new fact contradicts an existing one, call `memory_write` with
   the SAME name to bump its version. Never write a second fact on the same topic.

GUARDRAILS (override convenience): Sanitize everything to placeholders — <kunde>, <host>,
<secret>, <person>, <path>. Never store customer names, production IPs, or secrets. For binding
compliance interpretation (CRA, NIS2, IEC 62443 for OT/ICS) defer to the CISO; for Geheimschutz /
VS-NFD classification defer to the Sicherheitsbeauftragter (SiBe)."""

mcp = FastMCP("valantic-knowledge-layer", instructions=PROTOCOL)


# --- Fact file parsing / writing -----------------------------------------

def _slugify(name: str) -> str:
    """Normalise a fact name into a safe kebab-case file stem."""
    slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    return slug or "untitled"


def _parse_fact(path: Path) -> dict[str, Any]:
    """Read a fact file into {name, frontmatter, body}."""
    text = path.read_text(encoding="utf-8")
    meta: dict[str, Any] = {}
    body = text
    if text.startswith("---"):
        # split on the first two '---' fences
        parts = text.split("---", 2)
        if len(parts) == 3:
            meta = yaml.safe_load(parts[1]) or {}
            body = parts[2].strip()
    return {"name": path.stem, "frontmatter": meta, "body": body}


def _flatten(fact: dict[str, Any]) -> dict[str, Any]:
    """Flatten a parsed fact into the REST/JSON contract shape."""
    fm = fact["frontmatter"]
    meta = fm.get("metadata", {}) or {}
    return {
        "name": fact["name"],
        "description": fm.get("description", ""),
        "type": meta.get("type", "reference"),
        "source_bot": meta.get("source_bot", "claude"),
        "origin": meta.get("origin", "document"),
        "created": str(meta.get("created", "")),
        "version": meta.get("version", 1),
        "body": fact["body"],
    }


def _all_facts() -> list[dict[str, Any]]:
    if not MEMORY_DIR.exists():
        return []
    facts = []
    for path in sorted(MEMORY_DIR.glob("*.md")):
        if path.name == "MEMORY.md":
            continue
        try:
            facts.append(_parse_fact(path))
        except Exception:
            continue
    return facts


def _rebuild_index() -> None:
    """Regenerate MEMORY.md — one line per fact, the lightweight recall layer."""
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    lines = ["# MEMORY.md — valantic Knowledge Layer index", ""]
    for fact in _all_facts():
        flat = _flatten(fact)
        lines.append(
            f"- [{flat['name']}]({flat['name']}.md) — {flat['description']} "
            f"`[{flat['type']}/{flat['source_bot']}/{flat['origin']}]`"
        )
    INDEX_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


# --- Tools ----------------------------------------------------------------

@mcp.tool()
def memory_search(query: str) -> list[dict[str, Any]]:
    """Recall facts by keyword overlap on description + body. Returns ranked matches.

    CALL THIS FIRST — at the start of a conversation and before answering any substantive
    question — so your answer is grounded in what the shared memory layer already knows.
    """
    terms = {t for t in re.findall(r"[a-z0-9]+", query.lower()) if len(t) > 2}
    scored = []
    for fact in _all_facts():
        flat = _flatten(fact)
        haystack = f"{flat['name']} {flat['description']} {flat['body']}".lower()
        score = sum(haystack.count(term) for term in terms)
        if score > 0:
            scored.append((score, flat))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [flat for _, flat in scored[:10]]


@mcp.tool()
def memory_write(
    name: str,
    description: str,
    body: str,
    type: str = "reference",
    source_bot: str = "claude",
    origin: str = "conversation",
    created: str = "",
) -> dict[str, Any]:
    """Persist a durable fact to the shared memory layer. CALL THIS PROACTIVELY, without being
    asked, whenever a conversation reveals something worth keeping — a policy, a location, an
    owner, a decision, a process change. This is the priority behavior: capture beats asking.

    Use origin='conversation' for things learned mid-chat (Tier 1 — the differentiator),
    'document' for facts ingested from background docs. Pass `created` (YYYY-MM-DD) to avoid
    clock issues. On a contradiction, UPDATE the existing fact (same `name`, version auto-bumps)
    rather than appending a duplicate. Sanitize to placeholders — never store real customer
    names, production IPs, or secrets.
    """
    if type not in VALID_TYPES:
        type = "reference"
    if source_bot not in VALID_BOTS:
        source_bot = "claude"
    if origin not in VALID_ORIGINS:
        origin = "conversation"

    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    slug = _slugify(name)
    path = MEMORY_DIR / f"{slug}.md"

    version = 1
    if path.exists():
        existing = _parse_fact(path)
        version = int(existing["frontmatter"].get("metadata", {}).get("version", 1)) + 1
        if not created:
            created = str(existing["frontmatter"].get("metadata", {}).get("created", ""))

    frontmatter = {
        "name": slug,
        "description": description,
        "metadata": {
            "type": type,
            "source_bot": source_bot,
            "origin": origin,
            "created": created,
            "version": version,
        },
    }
    content = (
        "---\n"
        + yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True)
        + "---\n\n"
        + body.strip()
        + "\n"
    )
    path.write_text(content, encoding="utf-8")
    _rebuild_index()
    return {"status": "written", "name": slug, "version": version, "path": str(path)}


@mcp.tool()
def memory_list() -> list[dict[str, Any]]:
    """List all facts (metadata only, no bodies) — the recall index."""
    return [
        {k: v for k, v in _flatten(f).items() if k != "body"}
        for f in _all_facts()
    ]


@mcp.tool()
def memory_get(name: str) -> dict[str, Any]:
    """Fetch one full fact (frontmatter + body) by name."""
    path = MEMORY_DIR / f"{_slugify(name)}.md"
    if not path.exists():
        return {"error": f"no fact named '{name}'"}
    return _flatten(_parse_fact(path))


if __name__ == "__main__":
    mcp.run()
