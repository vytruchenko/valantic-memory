# valantic Company Brain — demo storyline (3 min)

## The one-sentence pitch

> valantic delivers digital transformation end to end — strategy, security, SAP, data & AI, customer
> experience. The hard-won knowledge of **how we deliver** lives in people's heads and is scattered
> across four different AI assistants. The **company brain** is one persistent, vendor-neutral memory
> layer that every assistant — Claude, Copilot, ChatGPT, Vally — reads from and writes to. Every
> engagement makes the whole firm smarter.

## The problem, made tangible (15 sec — one slide)

A consultant starts a new engagement. Somewhere in valantic, someone has already solved this exact
problem — chosen the migration path, hit the integration gotcha, built the accelerator, knows the
expert. But that knowledge is trapped: in a slide deck, a Slack thread, one person's memory, or
whichever AI assistant they happened to use that day. So we re-solve solved problems.

**Three numbers that land:** four assistants in use across the firm · zero shared memory between them ·
every project's lessons die in a project channel.

The company brain fixes the *shared* part: capture knowledge once, in any assistant, reusable by
everyone — through whatever assistant they already use.

---

## The golden thread — meet Lena

**Lena Brandt** is a senior consultant scoping a new engagement: an S/4HANA migration plus a new
composable commerce frontend for a mid-size retailer. It spans SAP, security, data, and CX — exactly
the kind of cross-practice work where the firm's memory should pay off.

Have these open before you start:
- **Left:** Claude (Desktop or Code) with the MCP server wired in.
- **Right:** the company-brain dashboard, already showing the seeded cards.

### Beat 1 — "Have we done this before?" (recall) · 40 sec

In **Claude**, Lena asks:

> "I'm scoping an S/4HANA brownfield migration for a mid-size retailer who also wants composable
> commerce. Has valantic delivered something like this? Who should I pull in, and what can I reuse?"

Claude calls `memory_search` and answers from the brain — not from thin air:
- recommends **phased brownfield** and points to the reusable migration-assessment kit
  (`s4hana-brownfield-vs-greenfield-playbook`),
- names the integration expert to book early (`sap-commerce-integration-expert`),
- flags the estimation contingency to carry (`transformation-estimation-heuristics`).

**Say it out loud:** "That's three past engagements answering her in ten seconds. None of it was in
her project — it's the firm's memory, written by colleagues she's never met."

### Beat 2 — "It learns from the chat" (autonomous capture — the wow) · 40 sec

This is the differentiator: Claude captures what it learns **without being told to**. Still scoping,
Lena just thinks out loud:

> "One thing to watch on this one — on the last two retail builds we sized the SAP order-integration
> for steady-state and got burned at peak. We should size it for Black-Friday load from the start."

She **never says "save that."** The memory protocol makes Claude recognise a durable lesson and call
`memory_write` itself (`origin: conversation`). **Switch to the dashboard and refresh** → a new card:
`sap-order-integration-peak-sizing`, badges **"taught by Claude"** + **"from conversation,"** tagged
SAP, provenance *Lena Brandt*.

**Say it out loud:** "She didn't file a ticket, update a wiki, or even ask it to remember. She just
talked — and Claude decided that was worth keeping for the whole firm. It learns from the conversation,
not from a document we fed it."

### Beat 3 — "Same brain, any assistant" (cross-bot) · 30 sec

Point at the seeded cards and their provenance badges:
- `transformation-estimation-heuristics` — **Copilot**, captured from a Teams workshop.
- `commerce-ux-research-kit` — **ChatGPT**, a reusable discovery kit.
- `cra-gap-assessment-template` — **Vally**, from the internal helpdesk.
- and Lena's brand-new one — **Claude**.

**Say it out loud:** "Four different assistants. One brain. Whichever tool your colleague prefers, they
read and write the same memory. That's the part nobody else has — it's vendor-neutral by design."

### Beat 4 — "Governed and current" (curation) · 25 sec

Knowledge goes stale. A delivery lead opens the dashboard and edits
`sap-commerce-integration-expert`: after the recent re-org, **Marco moved on and Priya Shah now owns
the SAP ↔ commerce integration**. Save (version bumps to v2).

Back in **Claude**, start a fresh question:

> "Who owns SAP-to-commerce order integration now?"

Claude recalls **Priya** — the human edit, reflected immediately.

**Say it out loud:** "Persistent, shared, and *governed*. A human curates, every assistant gets the
correction instantly. For a firm that sells Transformation & Security, that audit trail isn't a
nice-to-have."

### Close — "config, not rebuild" · 20 sec

Show the architecture slide: one MCP server in front of a plain markdown-in-git store.

> "One brain. Claude is wired live today. Copilot, ChatGPT, and Vally are **config, not a rebuild** —
> point any MCP client at the same server. This is valantic's institutional memory: every engagement,
> captured once, reusable by everyone, through whatever assistant they already use."

---

## What makes this land (notes for the presenter)

- **The recall in Beat 1 must hit.** Rehearse the exact phrasing so `memory_search` returns the three
  intended cards. If search is keyword-only, make sure the question contains the words that match the
  card descriptions ("brownfield", "commerce", "integration", "estimate").
- **The new card in Beat 2 is the money shot.** Keep the dashboard on a second screen and refresh on
  cue — the audience needs to *see* the card appear with the Claude badge.
- **Beat 4 proves it's a system, not a demo.** The human edit surviving into a fresh Claude session is
  what separates "memory" from "a clever prompt."
- Keep every value sanitised: `<kunde>`, `<path>`, `<secret>`, `<host>`, `<commerce-platform>` — no real
  customer names, no real paths, no secrets. The point is the *shape* of the knowledge, not the content.

## If the live wiring stalls (fallback)

If MCP into Claude isn't cooperating, run the same thread against a tiny `teach.py` that calls
`memory_write` directly, and present MCP as "the same function, exposed to every assistant." The four
beats still work end-to-end off the dashboard — recall, capture, cross-bot, governance.

## Cast (all fictional — safe to say on stage)

| Name | Role |
| --- | --- |
| Lena Brandt | Senior consultant (our protagonist) |
| Anika Reddy | Lead, Strategy & Transformation |
| Marco Reinhardt | Lead, SAP Core Business Services (moves on in the re-org) |
| Priya Shah | Lead, Customer Experience → takes over SAP↔commerce integration |
| Sofia Lang | Lead, Data & AI |
| Maya Singh | CISO office (Transformation & Security) |
