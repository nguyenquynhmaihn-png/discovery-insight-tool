---
name: process-interview
description: Turn a new interview transcript in inbox/ into verified insight proposals, an interview snapshot and opportunity-tree mappings, then hand them to the user for review. Use when the user says "process the new transcript", "analyse INT-00x" or drops a file in inbox/.
---

# Process a new interview

Follow CLAUDE.md for every rule. This file is the procedure. Never skip a step.

## 0. Prepare
1. Read `config/outcome.md`, `CLAUDE.md`, `DATA_MODEL.md` and `data/opportunities/tree.json` (all existing opportunities, not only titles: also their summaries).
2. If the raw file is a Teams .docx in `private/`, make sure its speakers are listed in `private/pseudonyms.json` (needed to tell interviewer from participant), then run `python3 scripts/normalize_transcripts.py`. Work only from `inbox/INT-xxx.md`.
   Real names may stay in the transcript (internal tool, see CLAUDE.md §8). Note: the current script still swaps names listed under `replace_in_text`; the rebuild makes that optional, for public builds only.

## 1. Profile (organisation + participant)
- Create or update `data/organisations/ORG-xxx/organisation.json` and `participants/P-xxx.json`.
- Every fact needs a line reference. Unknown = "not mentioned".
- Propose `participant_type` with the lines that justify it, and ASK the user to confirm it. It drives every signal.

## 2. Extract insights
Read the whole transcript twice before writing anything.
- One insight = one need, pain, behaviour, opinion or request from the PARTICIPANT. Interviewer lines are never evidence.
- For each: `quote` copied character-for-character, `lines`, `type`, `research_questions`, `statement` in the participant's voice, `severity` + `severity_quote` (or `unknown`).
- If the quote answers a leading or long framing question from an interviewer, say so in `interpretation_note`.
- Feature requests: find the "why" (link it) or set `needs_followup` with a `followup_question`.
- Skip small talk and statements that are only about the interviewer's company.
- Write to `data/organisations/ORG-xxx/interviews/INT-xxx/insights.json` with every `mapping.approved = false`.
- Copy the normalised transcript to `.../INT-xxx/transcript.md`.

## 3. Snapshot
Write `snapshot.json`: memorable quote (verbatim + lines), story (in order, each with line refs), interesting points not yet tied to an opportunity.

## 4. Propose mappings
For each insight, fill `mapping` following CLAUDE.md §5:
- `attach` → `opportunity_id`
- `create_sub` → `parent_id` (existing) OR `parent_proposed_title` (matching a `create_top` proposal in this run) + `proposed_title`
- `create_top` / new `parking_lot` → `proposed_title`
- always `confidence` and a one-sentence `reason` that names the meaning match, not the word match.
Several insights can share one `proposed_title`; they become one new opportunity.
Do NOT invent IDs for new opportunities. `approve.py` assigns them.

## 4b. Counter-evidence (v0.2)
Follow CLAUDE.md §12. For every existing opportunity, look for participant quotes in this transcript that count against it. Write them to `counter_evidence.json` (approved: false). None found is fine: write nothing.

## 5. Check
Run `python3 scripts/validate.py`. Fix every ERROR (usually a quote that is not verbatim: re-copy it from the transcript; never "fix" the transcript). Warnings about medium/low confidence are expected: they are what the user reviews.
Then `python3 scripts/build_site.py` so proposals appear in the dashboard's **Pending review** tab.

## 6. Hand over for review
Tell the user (in the user's language):
- counts: insights, proposed attaches / new opportunities / parking lot, counter-evidence proposals
- coverage % and number of flagged questions (from the dashboard), so the user knows what to review
- the medium/low-confidence items and the options for each
- the proposed participant_type
- follow-up questions raised
Then STOP and wait. Do not approve anything yourself.

## 7. Apply the user's decisions
- If the user changes a mapping or wording, edit `insights.json` first.
- `python3 scripts/approve.py INT-xxx --ids ...` / `--all` / `--reject ...` (this writes the tree and the change log).
- For each newly created opportunity, scan earlier transcripts for counter-evidence (CLAUDE.md §12) and propose it for review.
- Write a `summary` for each newly created opportunity and refresh summaries of reinforced ones (CLAUDE.md §10: only from attached insights).
- `python3 scripts/validate.py` → must show 0 errors, then `python3 scripts/build_site.py`.
- Log processing time for this interview in `baseline/time_log.md` (for the before/after comparison).
- v0.2 testing: remind the user to spot-check 3 random insights and log them in `experiment/v0.2/spot_checks.md`.
