"""
Seed the valantic Knowledge Layer with ~8 sanitized facts.

All content uses placeholders (<kunde>, <host>, <secret>, <person>, <path>) per
org policy — no customer names, prod IPs, or secrets. Compliance specifics defer
to the CISO rather than inventing policy.

Two facts are tagged with non-Claude source_bot (chatgpt, vally) so the dashboard
proves the store is genuinely bot-neutral. Most are origin='document' (background
ingestion); the live demo adds the first origin='conversation' fact.

Run:  .venv/bin/python seed_memory.py
"""

from mcp_server import memory_write

SEED_DATE = "2026-06-16"

FACTS = [
    {
        "name": "cra-gap-assessment-template",
        "description": "Where the CRA gap-assessment template lives and who owns it",
        "type": "reference",
        "source_bot": "claude",
        "origin": "document",
        "body": (
            "The CRA (EU Cyber Resilience Act) gap-assessment template lives at <path>. "
            "Owner: <person>. Use it as the starting point for any product subject to CRA "
            "conformity obligations. For binding compliance interpretation, defer to the CISO "
            "(Dr. Michael Eble) rather than improvising policy.\n\n"
            "Related: [[nis2-scope-checklist]]"
        ),
    },
    {
        "name": "nis2-scope-checklist",
        "description": "How we determine whether a <kunde> engagement falls under NIS2",
        "type": "reference",
        "source_bot": "claude",
        "origin": "document",
        "body": (
            "NIS2 (EU Directive 2022/2555) scope is assessed per engagement using the checklist "
            "at <path>: sector (essential vs important entity), headcount, and turnover thresholds. "
            "Document the determination in the engagement folder. Edge cases and final scoping "
            "sign-off go to the CISO (Dr. Michael Eble).\n\n"
            "Related: [[cra-gap-assessment-template]], [[iec-62443-ot-baseline]]"
        ),
    },
    {
        "name": "iec-62443-ot-baseline",
        "description": "Default reference standard for OT/ICS security assessments",
        "type": "reference",
        "source_bot": "claude",
        "origin": "document",
        "body": (
            "For any OT/ICS engagement, IEC 62443 is the baseline reference standard — cite it "
            "alongside NIS2 obligations. The zone-and-conduit model and security-level (SL) targets "
            "come from the IEC 62443 work products at <path>. Map each <kunde> asset to a zone before "
            "proposing controls."
        ),
    },
    {
        "name": "prod-access-request-flow",
        "description": "Standard read-only production access request process and SLA",
        "type": "project",
        "source_bot": "claude",
        "origin": "document",
        "body": (
            "Standard read-only prod access: open a ticket in the access-requests channel, tag your "
            "manager and the on-call lead, complete a 30-min pairing session, then access is filed via "
            "the IdP and provisions within ~4h. Urgent P1 grants are temporary (24h) and require the "
            "pairing session within 5 working days or access auto-revokes. Authoritative policy at <path>; "
            "owner: <person> (Head of Security)."
        ),
    },
    {
        "name": "on-call-rotation-owner",
        "description": "Who owns the SRE on-call rotation and what the on-call lead handles",
        "type": "project",
        "source_bot": "claude",
        "origin": "document",
        "body": (
            "The SRE on-call rotation is owned by <person> (Head of SRE). The current week's on-call lead "
            "handles ad-hoc access requests, P0/P1 escalations, and pairing sessions with new hires."
        ),
    },
    {
        "name": "new-hire-onboarding-pointers",
        "description": "First-week pointers for a new engineering hire",
        "type": "reference",
        "source_bot": "claude",
        "origin": "document",
        "body": (
            "New engineering hires: request read-only prod access after 2 weeks tenure + a pairing session "
            "(see [[prod-access-request-flow]]). The onboarding handbook is at <path>. For 'where do I find X' "
            "questions, the Engineering Ops Lead (<person>) is the institutional-knowledge contact."
        ),
    },
    {
        "name": "vs-nfd-classification-contact",
        "description": "Who to contact for VS-NFD / Verschlusssachen classification questions",
        "type": "reference",
        "source_bot": "chatgpt",
        "origin": "document",
        "body": (
            "Any question touching Geheimschutz, VS-NFD, or higher VS (Verschlusssachen) classification goes to "
            "the Sicherheitsbeauftragter (SiBe), <person>. Do not self-classify documents. This fact was captured "
            "by a ChatGPT connector pointed at the same store — proving the layer is bot-neutral."
        ),
    },
    {
        "name": "incident-comms-channel",
        "description": "Where P1 incident communication happens and the first escalation step",
        "type": "project",
        "source_bot": "vally",
        "origin": "document",
        "body": (
            "P1 incidents are coordinated in the incident channel <host>. First step: page the on-call lead "
            "(see [[on-call-rotation-owner]]) and open an incident doc from the template at <path>. "
            "Captured by the internal Vally bot — same store, different client."
        ),
    },
]


def main() -> None:
    for fact in FACTS:
        result = memory_write(created=SEED_DATE, **fact)
        print(f"  seeded {result['name']} (v{result['version']})")
    print(f"\nDone — {len(FACTS)} facts written to memory/.")


if __name__ == "__main__":
    main()
