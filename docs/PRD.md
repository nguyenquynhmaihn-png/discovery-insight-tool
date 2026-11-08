# PRD — Discovery Insight Tool v0.2 (MVP)

**Status:** Draft · **Owner:** Mai Nguyen · **Updated:** 5 Nov 2026 · **Evidence:** my experiment and 3 PM interviews (not in this repo) · **Changelog:** end of doc

## 1. Problem Alignment

**User:** any PM who runs and synthesises their own customer interviews, without a researcher. Most often a junior PM, but seniority isn't the line: some senior PMs work this way too.
**Reader:** the Head of Product (or manager) who decides which problems to invest in, using the PM's case. They read the overview; the PM works in the detail.
**Job:** When I finish an interview, I want grouped, prioritised problems I can trust, so I can decide what matters without rereading transcripts, and keep adding new interviews.
**Reader's job:** When my team brings me findings, I want to see the few problems that matter, why, and how solid the evidence is, so I can decide what to invest in next.

### The Problem
AI has made interview synthesis fast, but not trustworthy: every PM interviewed (3/3) already uses AI, and 2 of 3 still check its output by hand, rereading transcripts and losing the time saved (the third trusts NotebookLM because it shows source quotes). Without AI it is slow (105 min per interview, manual run). And results don't last: the 2024 synthesis was lost, so new interviews couldn't build on old ones.

**Why defined by behaviour, not seniority:** 2 of my 3 PMs (senior) act on findings others produce; the early-career PM synthesises his own interviews, like me. But a senior PM I follow also runs and synthesises his own interviews with AI tools (secondary: his blog). So the line is *who does the synthesis*, not job title. Evidence is still thin (1 PM + 1 blog + my own experience), which is why it is tested below.

### High-level Approach
**AI does the first draft, code proves the quotes, and the user only reviews what needs a human decision.**
Each new interview's insights come with code-checked quotes; the user reviews only flagged items, opens the transcript at the cited lines when unsure, and approves what joins one growing opportunity tree.

### Goals & Success
By the end of the MVP test (see Risks & Validation):
1. **Trust:** 100% of quotes shown to the user are verified in code, and the user approves or rejects every insight without opening the full transcript (only cited lines).
2. **Speed (guardrail):** checking must not cost the time AI saved: ≤ 30 min per interview incl. review, vs 105 min manually.
3. **Lasting:** 100% of approved insights stay traceable to their quote and transcript line after each new interview is added.
4. **Feeling:** the PM feels confident deciding which problems matter from the tool alone, without going back to the transcript.

### Non-goals
1. **Solutions or backlog:** the job ends at choosing problems; solutions need cost and feasibility data transcripts don't have.
2. **One priority score:** a single number hides weak evidence.
3. **Judging meaning:** code proves who said what; only the interviewer can judge what it means.
4. **Collaboration or integrations:** one PM prepares the case and one manager reads it; no shared editing, comments or connections to other tools yet.
5. **Anonymisation:** internal tool; the user needs real names to follow up.

**Later, not now:** upload in the tool · tree "diff" per new interview · a full evidence-against view (MVP only flags contradictions and counts them) · extra evidence flags.

---

## 2. Solution Alignment

### Key Features
**Core (backed by evidence), in priority order**
1. **Quote check in code:** word for word, said by the participant, at the cited lines. Fails → dropped.
2. **Draft insights:** quote + lines + suggested group; feature requests split from the need.
3. **Review one insight at a time, flagged first** (weak question, unsure group, no "why", contradicts the tree; full list in `CLAUDE.md`). Customer's words first, AI summary editable.
4. **Open in transcript:** one click to the cited lines, highlighted.
5. **Opportunity tree in two layers:** an overview of Focus, Watch and Later problems (each with why it matters, target customers, objective and readiness), and one evidence page per problem with sub-problems, quotes and open questions. Plus an Unassigned queue.
6. **Signals side by side, no single score** (full list in `CLAUDE.md`), plus a **readiness verdict** from a visible rule: 2+ target customers, mostly behaviour, a real cost shown, nobody against.
7. **Approve gate + interview snapshot + change log.** Each review ends in a snapshot saved with the interview: memorable quote, what I learned (by opportunity), opportunities touched, follow-ups raised.

**Hypothesis features (built thin, kept only if the tests below support them)**
8. **Customer profile with follow-ups:** one snapshot per interview, plus open questions from review (e.g. a missing "why"), Open → Asked → Answered, as prep for the next interview. *H2* · Secondary: *Continuous Discovery Habits* (weekly customer interviews, so open questions need somewhere to live between interviews); a senior PM's blog.
9. **Tiers with a reason:** the PM sets each problem to Focus, Watch or Later, links it to a product objective and writes why it matters; a tier guide suggests, the PM decides. A compare view puts all problems side by side, and a decision summary sits at the top for the manager. *H3* · Secondary: *Continuous Discovery Habits* (compare sibling opportunities, choose a target opportunity).

10. **Other evidence:** the PM adds evidence from beyond interviews (support tickets, analytics, sales notes, stakeholder input), with source and who added it. Shown next to the interview signals, not counted in them. *H4* · Source: PM feedback (Nov 2026).

*The test prototype shows all features (to get PM feedback on 8 to 10); the MVP build starts with core 1 to 7.*

### Key Flow
**Add transcript** (folder + one command) → **AI drafts + code checks** → **Review, one card at a time:** keep / drop / regroup, add follow-ups → **Snapshot saved; tree + signals update; follow-ups land in the customer profile.** → **PM sets tiers and writes why it matters; the manager reads the overview.** Time and full-transcript opens are logged (Goals 1–2). *Done* = every insight kept or dropped (Unassigned ones carry over to the tree page).

### Key Logic
1. **No quote, no insight.** Failed quotes never reach the user.
2. **Never force a fit.** Unsure → Unassigned; the user decides.
2b. **Tiers are a human decision.** The guide and readiness rule only suggest; the tool never sets a tier.
3. **Unapproved = invisible** in every signal and total.
4. **Count people, not mentions.** Only target customers size a problem.

Full rules: `CLAUDE.md`.

## 3. Risks & Validation
| Risk / hypothesis (biggest first) | Test | Pass bar |
|---|---|---|
| **H1** The tree is a better way to see the top problems than what PMs use now (ChatGPT, NotebookLM, Miro). The need for synthesis is already backed: all 3 PMs do it; one PM and a senior PM I follow built their own tools | PMs use the prototype tree, then: "Compared with how you group interviews now, is this better, worse or the same, and why?" | ≥ 2 of 3 name the top 2–3 problems from the tree without help and say it beats their current way |
| Results don't hold on new data (13.5 min was on already-analysed interviews, n = 2) | Unseen INT-001, INT-003 | Goals 1–3 met · grouping ≥ 80% agreed · flags ≥ 80% caught, ≤ 1 in 5 false alarms |
| User approves without reading | Spot-check 3 random approved insights per interview | ≥ 80% correct |
| Only the builder has used it; the user definition rests on 1 PM + 1 blog | 2 sessions with PMs who synthesise their own interviews (junior first; 1 senior if possible), no help | ≥ 1 of 2 uses a trust feature to accept/reject · feeling goal confirmed |
| NotebookLM + rereading is good enough | Same interview in NotebookLM | Tool faster *and* no full reread |
| **H2** Saved follow-ups improve the next interview | Show the test prototype to the 3 PMs; ask about behaviour: "When did you last talk to the same customer twice? Where did your open questions from the first interview end up?" + user sessions | ≥ 2 of 3 PMs describe a real follow-up situation · ≥ 1 of 2 users puts a follow-up in their next guide |
| **H3** Tiers with a reason help a manager decide | Show the overview to a Head of Product, no help: "Which problems would you invest in, and what would you check first?" | Names the Focus problems and their main gap within 2 minutes |
| **H4** Other evidence makes the case stronger | PM adds 1 to 2 non-interview items per Focus problem in a session | Manager says it changed or confirmed their decision |

**Decision rule:** H1 holds → v0.3 strengthens the tree. H1 fails → keep grouping, but show it as a simple theme list instead of a tree. H2, H3 or H4 fail → remove those features.

---

## Changelog
- 5 Oct 2026: Header + Problem Alignment drafted from `REQUIREMENTS.md` and experiment results.
- 5 Oct 2026: High-level Approach confirmed: review queue (core) + transcript drill-down; alternatives listed.
- 6 Oct 2026: Problem Alignment cut to fit the one-page target (~800 → ~420 words).
- 6 Oct 2026: Problem back to a paragraph (OPs move to case study); High-level Approach rewritten in plain steps.
- 6 Oct 2026: Solution Alignment drafted (features, future, key flow, key logic).
- 6 Oct 2026: Goals rewritten to map 1:1 to the problem (trust, slow, lasts). Flag accuracy, grouping and junior PM use move to Validation.
- 6 Oct 2026: Goals rewritten as one SMART sentence each (trust, speed, lasting) + one feeling goal.
- 6 Oct 2026: Privacy/anonymisation removed from scope (personal tool; user needs customer names). Supersedes REQUIREMENTS Must 5(g) and the anonymisation non-functional requirement.
- 6 Oct 2026: Risks & Validation drafted (5 risks, 3 tests, decision rule).
- 6 Oct 2026: Cut toward one page: risks + validation merged, features as a list, Future folded into Non-goals, Key Logic to 4 rules, 'How this solves it' removed (~1,170 → ~822 words).
- 6 Oct 2026: Second cut: approach to one line, flag/signal lists to sub-doc, Should line and batch-grouping risk removed, 8/27 sentence removed (~713 words).
- 6 Oct 2026: Non-goals rewritten as a numbered list, one sentence each: what + why.
- 6 Oct 2026: Mai edited Goals (test scope line) and Key Features (tree wording). Non-goals shortened.
- 8 Oct 2026: Done rule changed: every insight kept or dropped; Unassigned insights carry over instead of blocking completion.
- 8 Oct 2026: Added features 8 (focus + reason) and 9 (customer profile with follow-ups) to MVP; review is one card at a time. Mockup: `mockups/mvp_prototype.html`.
- 8 Oct 2026: Aligned with case study: v0.2 naming, trust-first problem + why junior PM, speed as guardrail, core vs hypothesis features (H2 follow-ups, H3 focus), batch-grouping risk restored as H1, product decision rule, follow-up duplication removed, contradiction scope clarified, logging for goals. Open question resolved: approve one by one.
- 9 Oct 2026: User defined by behaviour (PMs who synthesise their own interviews), not seniority; a senior PM's blog + Continuous Discovery Habits added as secondary evidence for features 8–9; H2 test with the 3 PMs via behaviour questions; prototype shows all features, MVP build starts with core 1–7.
- 9 Oct 2026: Interview snapshot added to core feature 7 (review → snapshot per interview); customer profile (H2) = snapshots + follow-ups.
- 9 Oct 2026: H1 changed from "grouping is a real pain" to "the tree is the right approach"; synthesis need backed by PM evidence (all 3 synthesise; one PM and a senior PM I follow built their own tools). Decision rule updated.
- 5 Nov 2026: After PM feedback: reader added (Head of Product). Tree in two layers: overview with Focus, Watch and Later tiers, why it matters, objective and readiness; one evidence page per problem; compare view and tier guide. Readiness rule added. Feature 9 becomes tiers with a reason (H3 reworded). New feature 10: other evidence beyond interviews (H4). Non-goal 4 reworded: one PM prepares, one manager reads; no collaboration yet. New key logic: tiers are a human decision.
- 6 Nov 2026: Problem corrected to 2 of 3 PMs checking by hand (matches interview notes). One-page image re-rendered as `portfolio/PRD_one_page_v0.3.png`.
