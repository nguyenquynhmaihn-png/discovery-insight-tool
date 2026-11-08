# Discovery Insight Tool — Operating Rules

You turn customer interview transcripts into verified insights and map them onto an opportunity solution tree.
Read `config/outcome.md` before every run. Data model: `DATA_MODEL.md`.
Procedure for a new interview: `skills/process-interview/SKILL.md`. Follow it step by step.

## 1. Evidence rules (non-negotiable)
1. Use ONLY the transcript and the participant/organisation profile provided. No outside knowledge about the participant, their company or the ESG market.
2. Every insight MUST carry a verbatim quote copied character-for-character from the transcript, plus the line range where it appears. No quote → no insight.
3. If information is not in the transcript, write `null` / "not mentioned". Never guess company size, tools, sector, etc.
4. Keep evidence and interpretation apart: `quote` = what they said; `statement` = your one-line reframe in the customer's voice. Any inference beyond that goes in `interpretation_note` and is marked as such.
5. After extraction, run `scripts/verify_quotes.py`. Unverified quotes are fixed or dropped before anything is mapped.

## 2. Insight typing
Tag each insight with exactly one `type`:
- `behaviour` — a story of something that actually happened ("Last quarter I spent two weeks chasing…"). Strongest evidence.
- `opinion` — a belief, generalisation or prediction ("Most companies don't care about Scope 3").
- `feature_request` — a solution the participant proposes ("I want a dashboard that…").
- `context` — background facts (role, team size, reporting frameworks). Goes to the profile, not the tree.

For every `feature_request`, look in the transcript for WHY they want it.
- Why is present → create the underlying need as a separate insight and link both.
- Why is absent → set `needs_followup: true` and write a `followup_question` for the next interview.

## 3. Severity (must be backed by a quote)
- `blocker` — stops them completing a key reporting task or meeting a deadline/regulation.
- `workaround` — they get it done, but through costly manual effort (time, people, consultants).
- `irritation` — annoying, no material cost described.
- `unknown` — transcript does not show the impact. Do NOT upgrade by assumption.

## 4. Opportunity rules
An opportunity is a customer need, pain point or desire — never a solution.
- Write it in the customer's words and from the customer's perspective, not the company's.
- Solution-in-disguise test: can you name at least two different ways to address it? If not, reframe.
- Capture the cause, not the feeling ("can't trust data from suppliers", not "frustrated").
- Maximum two levels below the outcome: Opportunity → Sub-opportunity. Insights attach to the lowest level.
- No vertical branches (a parent with a single child and no siblings): merge them or flag the gap.
- Each opportunity has exactly one parent. If it seems to fit two, it is too broad — split it.
- Sizing counts unique `target_customer` participants only. Adjacent users and experts are shown separately.

## 5. Matching protocol (new insight → tree)
For each insight choose one action and give a confidence (high / medium / low):
- `attach` to an existing (sub-)opportunity — only when the meaning matches, not just the wording.
- `create_sub`: a new sub-opportunity under an existing opportunity (`parent_id` + `proposed_title`).
- `create_top`: a new top-level opportunity (`proposed_title`).
- `parking_lot`: out of scope per `config/outcome.md`, or a market/competitor signal rather than a customer need.
Every proposal is written with `approved: false`. Never assign IDs to new opportunities; `scripts/approve.py` does.
If confidence is not high, explain the options and your reasoning when handing over; the user decides.
Do not assume every insight belongs to an existing opportunity. Creating a new one is a normal outcome.

## 6. Human review gate
Never edit `data/opportunities/tree.json` by hand to add evidence or opportunities. Proposals stay `approved: false` and show in the dashboard's Pending review tab.
Only `scripts/approve.py`, run after the user's decision, approves, rejects, creates opportunities and updates the tree.
Present: new insights, proposed mappings, items needing decision, the proposed participant_type, follow-up questions.

## 7. Change log
`scripts/approve.py` writes the change log automatically. Only add a manual entry for tree edits made outside approve.py (reframing, merging, moving to parking lot), and say why.

## 8. Customer data (internal use)
- This is a personal / internal team tool. Real names, organisations and contact details may be used in profiles, insights, snapshots and the tree: the user needs them to manage customers and follow-ups.
- IDs (ORG-001, P-001, INT-001) stay as stable keys; names go in the name fields.
- Quotes stay verbatim. No masking for internal use.
- Publishing is different: anything shared outside the team (GitHub, portfolio, case study) uses `demo/` data or a `--public` build that anonymises. Never publish `data/`, `inbox/` or `private/`.

## 9. Prioritisation
Do not compute a single priority score. For each opportunity, show: unique target customers, total mentions, severity mix, behaviour-vs-opinion ratio and the most recent evidence date.
`market_factor`, `company_factor` and `decision_rationale` are entered by the user only. Leave them empty.

## 10. Opportunity summary
Each opportunity has a short `summary` (2–3 sentences). Write it ONLY from the insights attached to that opportunity. No new facts, numbers or claims. Say when evidence is mostly from experts or adjacent users. The dashboard labels it "AI synthesis".

## 11. After every approved run
1. `python3 scripts/validate.py` — schema, references, tree rules and quote verification. Must show 0 errors.
2. `python3 scripts/build_site.py` — rebuilds the dashboard (`web/index.html`). Use `--public` for anything shared outside this computer.

## Language
Transcripts and data are in English. Explain results to the user in the language they write in.

## 12. Counter-evidence (v0.2)
- After mapping, look in the transcript for participant statements that count AGAINST an existing opportunity: they say it is not a problem for them, they already handle it well, or it does not apply to them.
- Only real disagreement. "It's a small problem" is weak support, not counter-evidence. A different problem is not counter-evidence.
- Copy the quote character-for-character from participant lines, with `lines` and a one-sentence `reason`. Write to `counter_evidence.json` in the interview folder with `approved: false`.
- When a NEW opportunity is approved, scan the earlier transcripts for counter-evidence to it too.
- Finding none is a valid result. Never stretch a quote to fill the section.

## 13. Trust checks are code, not judgement (v0.2)
Question flags (yes/no, leading), quote context and coverage are computed by `scripts/trust_checks.py` at build time. Do not write or edit them by hand. Still use `interpretation_note` when an answer was shaped by the question.

