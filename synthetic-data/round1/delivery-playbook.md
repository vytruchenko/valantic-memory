# valantic Delivery Playbook — Retail Transformation (excerpt)

*Internal. Version 3.1 — effective February 2026. Owner: Anika Reddy (Strategy & Transformation).*

This is the working reference for how we scope and staff an end-to-end transformation for a mid-size
retail <kunde>: SAP core, commerce frontend, data & AI, under EU compliance pressure. Sanitised —
client and infra specifics are placeholders.

## How we scope it

A retail transformation usually crosses four practice areas at once: **SAP Core Business Services**,
**Customer Experience** (commerce frontend), **Data & AI**, and **Transformation & Security**. Pull a
named lead from each into scoping early — the cross-practice dependencies (especially SAP ↔ commerce
order integration) drive the cutover plan more than any single workstream.

## The S/4HANA migration call

For a mid-size retailer with a clean-enough core, default to **phased brownfield**. Recommend
greenfield only when the ECC customisation debt is genuinely unrecoverable. On the last two retail
engagements the brownfield path roughly halved the cutover window versus a greenfield rebuild. The
decision criteria and the reusable migration-assessment kit are catalogued in the reusable-assets doc.

## Estimating

- Carry **20–25% contingency** on any engagement crossing three or more practice areas.
- Size discovery at ~**10%** of total effort.
- Commerce-frontend replatforming onto <commerce-platform> has run **15–20% over** first-pass
  estimates on recent work — pad it explicitly.

## Compliance gate

Before quoting any CRA- or NIS2-readiness work, run the gap-assessment / scoping checklists with the
CISO office (Maya Singh). Sector classification under NIS2 changes the obligations and the price — do
not guess it.

## Keeping the playbook alive

Every engagement ends with a 30-minute retro. Reusable lessons get written into the **company brain**
by whichever assistant the consultant uses, tagged by practice area, so the next person scoping a
similar deal recalls them instantly instead of re-learning them.
