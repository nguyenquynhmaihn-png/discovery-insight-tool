# Data Model

## Folder structure
```
discovery-insight-tool/
├── CLAUDE.md                  # rules the bot must follow
├── DATA_MODEL.md              # this file
├── config/outcome.md          # outcome, research questions, ICP, participant types
├── inbox/                     # drop a new transcript here to start a run
├── private/                   # git-ignored: raw .docx transcripts + contacts.csv
├── skills/process-interview/SKILL.md   # step-by-step procedure for the bot
├── scripts/                   # normalize_transcripts, validate, verify_quotes, approve, build_site
├── web/                       # dashboard (open web/index.html)
├── demo/                      # fictional demo data, same structure as data/
└── data/
    ├── organisations/
    │   └── ORG-001/
    │       ├── organisation.json
    │       ├── participants/P-001.json
    │       └── interviews/INT-001/
    │           ├── transcript.md      # line-numbered (real names allowed, internal use)
    │           ├── snapshot.json      # interview snapshot
    │           └── insights.json
    ├── opportunities/tree.json
    └── changelog.md
```
Relationships: Organisation 1—n Participant 1—n Interview 1—n Insight n—1 Opportunity.
Repeat interviews with the same person or company go into the same organisation folder.

## organisation.json
```json
{
  "id": "ORG-001",
  "pseudonym": "Acme GmbH",
  "org_type": "company | ngo | consultancy | professional_body | investor | other",
  "sector": "manufacturing",
  "country": "Germany",
  "size_band": "mid-size | small | large | not mentioned",
  "fits_icp": true,
  "reporting_context": "not mentioned",
  "source": "transcript INT-001 L12-18"
}
```

## participants/P-001.json
```json
{
  "id": "P-001",
  "org_id": "ORG-001",
  "role": "Sustainability Manager",
  "participant_type": "target_customer | adjacent_user | expert",
  "current_tools": ["Excel"],
  "contact_ref": "private/contacts.csv#P-001",
  "notes": "Only facts stated in the transcript, each with a line reference"
}
```
`contact_ref` points to the private file. It is used later for "notify customers when an opportunity is addressed".

Names: this is an internal tool, so `pseudonym` holds the real organisation name (field to be renamed `name` in the rebuild). Public builds replace it with an alias. `masked` stays `false` for internal use.

## insights.json (one array per interview)
```json
{
  "id": "INS-001-03",
  "interview_id": "INT-001",
  "org_id": "ORG-001",
  "participant_id": "P-001",
  "type": "behaviour | opinion | feature_request | context",
  "research_questions": ["RQ1", "RQ2"],
  "statement": "I can't get reliable emissions data from my suppliers in time",
  "quote": "exact words from the transcript",
  "lines": [84, 86],
  "masked": false,
  "verified": false,
  "severity": "blocker | workaround | irritation | unknown",
  "severity_quote": "exact words showing the impact, or null",
  "linked_insight_ids": [],
  "needs_followup": false,
  "followup_question": null,
  "interpretation_note": null,
  "severity_lines": null,
  "mapping": {
    "action": "attach | create_sub | create_top | parking_lot",
    "opportunity_id": "OPP-02.1        (attach; set by approve.py for new ones)",
    "parent_id": "OPP-02            (create_sub only)",
    "proposed_title": "...          (create_sub / create_top / new parking_lot)",
    "confidence": "high | medium | low",
    "reason": "why this match",
    "approved": false,
    "rejected": false
  }
}
```

## opportunities/tree.json
```json
{
  "outcome": "see config/outcome.md",
  "updated": "2026-09-22",
  "opportunities": [
    {
      "id": "OPP-02",
      "parent_id": null,
      "title": "I struggle to collect the data I need for the report",
      "scope": "in_scope | parking_lot",
      "status": "open | exploring | addressed",
      "created": "2026-09-22",
      "insight_ids": [],
      "signals": {
        "unique_target_customers": 0,
        "adjacent_users": 0,
        "experts": 0,
        "total_mentions": 0,
        "severity_mix": {"blocker": 0, "workaround": 0, "irritation": 0, "unknown": 0},
        "behaviour_ratio": 0,
        "latest_evidence": null
      },
      "market_factor": null,
      "company_factor": null,
      "decision_rationale": null
    },
    { "id": "OPP-02.1", "parent_id": "OPP-02", "title": "..." }
  ]
}
```
`signals` are computed by script from insights, never typed by the bot.
`market_factor`, `company_factor`, `decision_rationale` are filled in by the user only.

## snapshot.json (interview snapshot, per Continuous Discovery)
```json
{
  "interview_id": "INT-001", "org_id": "ORG-001", "participant_id": "P-001",
  "date": "2025-03-12", "interviewer": "Mai",
  "memorable_quote": {"text": "verbatim", "lines": [19, 19]},
  "story": ["What happened, in order, each with (Lx)"],
  "interesting": ["Notable, not yet an opportunity (Lx)"]
}
```
Quick facts come from the participant/organisation profile; opportunities and follow-ups come from insights.json.
Opportunities in tree.json also carry `summary` (see CLAUDE.md §10).

## counter_evidence.json (v0.2, one per interview folder, optional)
```json
[{
  "id": "CE-004-01",               // CE-<interview number>-<nn>
  "interview_id": "INT-004", "org_id": "ORG-004", "participant_id": "P-004",
  "opportunity_id": "OPP-01",      // the opportunity this counts against
  "quote": "verbatim participant words",
  "lines": [12, 12],
  "reason": "one sentence: why this counts against the opportunity",
  "approved": false,               // set only by approve.py
  "rejected": false
}]
```

## Computed at build time (v0.2, never stored)
- per interview: `question_flags` [{line, question, kind: yes_no|leading, reason}], `coverage` {pct, uncovered: [{start, end, words}]}
- per insight / counter-evidence: `asked_lines` (the question it answers), `weak_question` (set if that question was flagged)
- per opportunity: `counter_evidence` (approved ids)

