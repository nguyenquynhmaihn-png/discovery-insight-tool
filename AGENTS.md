# Instructions for AI coding agents (Codex, GitHub Copilot and others)

This project was built and tested with Claude Code, which reads `CLAUDE.md`. If you are another agent, follow the same files:

1. **Rules:** read and follow `CLAUDE.md` in full. Its evidence rules are non-negotiable.
2. **Procedure:** to process a new transcript in `inbox/`, follow `skills/process-interview/SKILL.md` step by step.
3. **Discovery goal:** read `config/outcome.md` before every run.
4. **Data format:** write files exactly as described in `DATA_MODEL.md`.

Most important rules:

- Every insight needs a quote copied character for character from a participant line in the transcript, with its line numbers. No quote, no insight.
- Never edit the transcript to make a quote match.
- After drafting, run `python3 scripts/validate.py` and fix every error before handing over.
- Do not approve anything yourself. Stop and let the user review. Only run `scripts/approve.py` with the IDs the user chooses.
