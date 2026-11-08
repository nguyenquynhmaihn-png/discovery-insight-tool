"""v0.2 trust checks. Pure code, no AI, so results are predictable and run locally.

1. flag_questions(lines)  -> interviewer questions that are yes/no or leading
2. answered_question(...) -> the interviewer question an insight's quote is answering
3. coverage(lines, ranges)-> which participant lines no insight uses ("what the AI missed")

Usage (report for one interview):
  python3 scripts/trust_checks.py <transcript.md> [insights.json]
"""
import json, re, sys
from pathlib import Path
from verify_quotes import speaker

FILLERS = {"so", "and", "ok", "okay", "um", "uh", "erm", "yeah", "yes", "right", "well", "but", "alright", "now", "then", "just", "also"}
YES_NO_START = {"do", "does", "did", "is", "are", "was", "were", "have", "has", "had", "can", "could", "would", "will",
                "should", "shall", "may", "might", "isn't", "aren't", "don't", "doesn't", "didn't", "wouldn't", "won't",
                "haven't", "hasn't", "wasn't", "weren't", "can't", "couldn't", "shouldn't"}
# "Can you tell me..." is a polite open request, not a yes/no question
OPEN_REQUEST = re.compile(r"^(can|could|would|will) you (please )?(tell|describe|walk|explain|talk|share|give|elaborate|expand|say more|take me|think of|remember|recall|show|start|run me|go through)")
LEADING = [
    (r"\b(don't|do not) you think\b", "suggests the answer ('don't you think')"),
    (r"\bwouldn't you (say|agree)\b", "suggests the answer ('wouldn't you say')"),
    (r"\bwould you (say|agree)\b", "asks them to agree with a statement"),
    (r"\bdo you agree\b", "asks them to agree with a statement"),
    (r"\b(isn't|wasn't|aren't) (it|that|they)\b", "tag question suggests the answer"),
    (r",\s*(right|correct|yeah|no)\s*\?\s*$", "tag question suggests the answer"),
    (r"\b(i assume|i guess|i suppose|i imagine|presumably|you probably|you must)\b", "states an assumption first"),
    (r"\bso (you're|you are) saying\b", "puts words in their mouth"),
    (r"\b(how|is it|was it|was that|is that|do you find it|did you find it|must be|it's)\s*(really |very |quite |so )?"
     r"(hard|difficult|painful|frustrating|annoying|challenging|time.consuming|tedious|stressful)\b",
     "names the pain before they do"),
]

def _questions(text):
    """Split an interviewer line into question sentences (ending with '?')."""
    parts = re.split(r"(?<=[?.!])\s+", text)
    return [p.strip() for p in parts if p.strip().endswith("?")]

def _first_word(q):
    words = re.findall(r"[a-z']+", q.lower())
    while words and words[0] in FILLERS:
        words.pop(0)
    return words[0] if words else "", " ".join(words)

# call logistics, not interview questions (fix 1 after Mai's test, 3 Oct)
SMALL_TALK = re.compile(r"\b(hear me|are you (back|there|still there)|see my screen|can i ask( about)?\s*\??$|you ok\b|is that ok\b)")
WH = re.compile(r"\b(what|how|why|when|where|who|whom|whose|which)\b")

def classify(question):
    """Return (kind, reason) where kind is 'leading', 'yes_no' or None."""
    low = question.lower()
    if SMALL_TALK.search(low):
        return None, None
    for pat, why in LEADING:
        if re.search(pat, low):
            return "leading", why
    first, cleaned = _first_word(question)
    if OPEN_REQUEST.match(cleaned):
        return None, None
    if first in YES_NO_START:
        return "yes_no", "can be answered with yes or no"
    # yes/no question tucked after a statement: "..., but do they have X?"  (fix 2)
    for clause in ([] if WH.match(re.sub(r"^\W*((so|and|ok|okay|yeah|but)\W+)*", "", low)) else re.split(r",|;|\b(?:but|and|so)\b", low)[1:]):
        f, c = _first_word(clause)
        if f in YES_NO_START and not OPEN_REQUEST.match(c):
            return "yes_no", "ends with a yes/no question"
    # a statement turned into a question: "Need a report for my annual report?"  (fix 3)
    if not WH.search(low):
        return "yes_no", "a statement with a question mark: invites a yes/no confirmation"
    return None, None

def is_interviewer(line):
    s, _ = speaker(line)
    return bool(s) and s.lower().startswith("interviewer")

def flag_questions(lines):
    """[{line, question, kind, reason}] for every flagged question (1-based line numbers)."""
    out = []
    for n, l in enumerate(lines, 1):
        if not is_interviewer(l):
            continue
        _, text = speaker(l)
        for q in _questions(text):
            kind, why = classify(q)
            if kind:
                out.append({"line": n, "question": q, "kind": kind, "reason": why})
    return out

def answered_question(lines, start):
    """Line numbers of the interviewer turn just before `start` (the question being answered)."""
    n = start - 1
    while n >= 1 and not is_interviewer(lines[n - 1]):
        n -= 1
    turn = []
    while n >= 1 and is_interviewer(lines[n - 1]):
        turn.append(n)
        n -= 1
    return sorted(turn)

def substantive(line, min_words=6):
    s, t = speaker(line)
    return bool(s) and not s.lower().startswith("interviewer") and len(t.split()) >= min_words

def coverage(lines, ranges, min_words=6):
    """Share of participant words used by insights, plus the uncovered stretches to review."""
    used = set()
    for a, b in ranges:
        used.update(range(a, b + 1))
    part = [n for n, l in enumerate(lines, 1) if substantive(l, min_words)]
    words = lambda n: len(speaker(lines[n - 1])[1].split())
    total = sum(words(n) for n in part)
    covered = sum(words(n) for n in part if n in used)
    segs, cur = [], None
    for n in part:
        if n in used:
            cur = None
            continue
        if cur and not any(m in used for m in range(cur["end"], n)):
            cur["end"], cur["words"] = n, cur["words"] + words(n)
        else:
            cur = {"start": n, "end": n, "words": words(n)}
            segs.append(cur)
    return {"participant_words": total, "covered_words": covered,
            "pct": round(covered / total, 2) if total else 0, "uncovered": segs}

if __name__ == "__main__":
    lines = Path(sys.argv[1]).read_text(encoding="utf-8").splitlines()
    flags = flag_questions(lines)
    print(f"{len(flags)} flagged questions")
    for f in flags:
        print(f"  L{f['line']} [{f['kind']}] {f['question'][:90]}  ({f['reason']})")
    if len(sys.argv) > 2:
        ins = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
        cov = coverage(lines, [i["lines"] for i in ins])
        print(f"Coverage: {cov['pct']:.0%} of participant words used; {len(cov['uncovered'])} uncovered stretches")
