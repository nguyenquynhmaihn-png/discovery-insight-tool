# Discovery Insight Tool

An AI-assisted tool that turns customer interview transcripts into evidence a PM can check and a Head of Product can act on.

- Every insight keeps the customer's exact words, with the transcript lines they came from.
- Every quote is checked word for word **in code**, not by the AI. A quote that fails is dropped.
- Nothing counts until a PM has reviewed it, one insight at a time.
- Approved insights build an opportunity tree: a short overview of the top problems, with the evidence one click deeper.

Built by Mai Nguyen as a portfolio project. Read the case study: [link to case study]

## Try it

| What | Where | Needs |
|---|---|---|
| Interactive prototype (v0.2 design, fictional data) | https://nguyenquynhmaihn-png.github.io/discovery-insight-tool/ | A browser |
| Working pipeline on demo data | Open `web/index.html` | A browser |
| Run it on your own transcript | See below | Python 3 and Claude Code |

## Why it exists

AI has made interview synthesis fast, but not trustworthy. PMs I interviewed already use AI to synthesise, and most still go back to the transcript to check what it says. This tool puts the checking into the workflow: the AI drafts, code proves the quotes, and the PM decides.

## How it works

1. **Add a transcript** to `inbox/`.
2. **AI drafts insights.** Claude Code follows the rules in `CLAUDE.md` and the procedure in `skills/process-interview/SKILL.md`: each insight gets a verbatim quote, line numbers, a type (behaviour, opinion, feature request) and a suggested place in the tree.
3. **Code checks every quote** (`scripts/verify_quotes.py`, `scripts/validate.py`): word for word, said by the participant (not the interviewer), at the cited lines.
4. **The PM reviews** each proposal: keep, drop or move it. Unsure items go to Unassigned instead of being forced into a group.
5. **The tree updates** (`scripts/approve.py`) and every decision is written to a change log.
6. **The dashboard rebuilds** (`scripts/build_site.py`) so you can open it in a browser with no server.

## Trust rules

- No quote, no insight.
- Never force a fit: unsure items go to Unassigned.
- Unreviewed items are invisible in every count.
- Count people, not mentions.
- No single priority score: signals sit side by side, and only the PM sets a priority.

## Run it on your own transcript

You need Python 3.9 or later and [Claude Code](https://claude.com/claude-code). Your data stays on your machine: `data/`, `inbox/` and `private/` are git-ignored.

1. **Set up an empty project**
   ```bash
   mkdir -p data/opportunities
   cp templates/opportunities/tree.json data/opportunities/tree.json
   ```
2. **Describe your discovery goal** in `config/outcome.md`: learning goal, research questions and who your target customer is. The example file is an ESG reporting case.
3. **Add a transcript** as `inbox/INT-001.md`, one speaker turn per line, for example `Interviewer: ...` and `P-001: ...`. (Teams .docx files can go in `private/` with a `private/pseudonyms.json`, then run `python3 scripts/normalize_transcripts.py`.)
4. **Process it.** Open Claude Code in this folder and say: `Process the new transcript in inbox`. It stops and waits for your review.
5. **Review.** Open `web/index.html`, go to **Pending review**, and tell Claude what to keep, change or drop. It applies your decisions with `scripts/approve.py`.
6. **Check and rebuild**
   ```bash
   python3 scripts/validate.py
   python3 scripts/build_site.py
   ```

To look at the demo data instead: `python3 scripts/build_site.py demo`, then open `web/index.html`.

## What's in the repo

| Folder or file | What it is |
|---|---|
| `CLAUDE.md` | The rules the AI must follow |
| `skills/process-interview/` | The step-by-step procedure for one interview |
| `DATA_MODEL.md` | How insights, interviews and the tree are stored |
| `scripts/` | Quote verification, validation, approval and the dashboard build |
| `web/` | The dashboard (open `index.html`) |
| `demo/` | Four fictional interviews to try the tool |
| `config/outcome.md` | The discovery goal for the example case |
| `docs/` | The v0.2 interactive prototype and the PRD |

## Status and limits

- **v0.2, a portfolio prototype.** The interactive prototype shows the v0.2 design. The working pipeline and dashboard are an earlier build of the same tool, which I used on real interviews.
- **Tested small.** In my own test it cut synthesis from 105 to 13.5 minutes per interview, with every quote verified, but on two interviews I had already analysed, with one reviewer.
- **Not solved yet:** a verified quote can still be misread, and the transcript itself can be wrong (for example garbled words or acronyms from Teams). These are the next trust problems.

All data in this repository is fictional.
