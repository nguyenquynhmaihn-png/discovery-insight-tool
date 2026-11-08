"""Check every piece of quoted evidence against its transcript.

A quote passes only if it appears word-for-word (ignoring case, extra spaces and
curly quotes) inside the cited lines, AND only in lines spoken by the participant.
Interviewer lines ('Interviewer...') never count as evidence.

Checked per insight: quote, severity_quote. Checked per interview: memorable_quote,
and every counter-evidence quote (v0.2).

Usage: python3 scripts/verify_quotes.py [data_dir]   (default: data)
"""
import json, re, sys
from pathlib import Path

LINE = re.compile(r"^\s*(?:\[[0-9:]+\]\s*)?([A-Za-z0-9\-]{1,30}):\s(.*)$")

def speaker(line):
    m = LINE.match(line)
    return (m.group(1), m.group(2)) if m else (None, line)

def norm(s):
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", s).strip().lower()

def check(quote, lines, rng, masked=False):
    if not quote or not rng:
        return False, "missing quote or line range"
    a, b = rng
    if a < 1 or b > len(lines) or a > b:
        return False, f"line range {a}-{b} outside transcript (1-{len(lines)})"
    spoken = [speaker(l) for l in lines[a - 1:b]]
    participant = " ".join(norm(t) for s, t in spoken if s and not s.lower().startswith("interviewer"))
    q = norm(quote)
    if masked:
        pos = 0
        for p in [p.strip() for p in re.split(r"\[[^\]]+\]", q) if p.strip()]:
            i = participant.find(p, pos)
            if i < 0:
                return False, f"fragment not found in participant lines: '{p[:40]}'"
            pos = i + len(p)
        return True, "ok (masked)"
    if q in participant:
        return True, "ok"
    everything = " ".join(norm(t) for _, t in spoken)
    if q in everything:
        return False, "quote is from the interviewer, not the participant"
    return False, "quote not found in cited lines"

def verify_dir(data_dir):
    results = []
    for idir in sorted(d for d in Path(data_dir).glob("organisations/*/interviews/*") if d.is_dir()):
        lines = (idir / "transcript.md").read_text(encoding="utf-8").splitlines()
        if (idir / "insights.json").exists():
            for ins in json.loads((idir / "insights.json").read_text(encoding="utf-8")):
                results.append((ins["id"],) + check(ins.get("quote"), lines, ins.get("lines"), ins.get("masked", False)))
                if ins.get("severity_quote"):
                    results.append((ins["id"] + " severity",) + check(ins["severity_quote"], lines, ins.get("severity_lines") or ins.get("lines")))
        if (idir / "counter_evidence.json").exists():
            for ce in json.loads((idir / "counter_evidence.json").read_text(encoding="utf-8")):
                results.append((ce["id"],) + check(ce.get("quote"), lines, ce.get("lines")))
        if (idir / "snapshot.json").exists():
            mq = json.loads((idir / "snapshot.json").read_text(encoding="utf-8")).get("memorable_quote")
            if mq:
                results.append((idir.name + " memorable quote",) + check(mq["text"], lines, mq["lines"]))
    return results

if __name__ == "__main__":
    res = verify_dir(sys.argv[1] if len(sys.argv) > 1 else "data")
    bad = [r for r in res if not r[1]]
    for i, ok, why in res:
        if not ok:
            print(f"FAIL {i} -> {why}")
    print(f"{len(res) - len(bad)}/{len(res)} quotes verified")
    sys.exit(1 if bad else 0)
