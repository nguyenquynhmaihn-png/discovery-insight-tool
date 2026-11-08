"""Build web/data.js from a data folder so the dashboard can open with no server.

Usage: python3 scripts/build_site.py [data_dir] [--public]
  data_dir  default 'data'; use 'demo' for demo data
  --public  for sharing (e.g. GitHub Pages): keeps only the transcript lines that are
            quoted as evidence; every other line is withheld.
v0.2 adds: question flags, quote context, coverage and counter-evidence (scripts/trust_checks.py).
Signals are computed here from insights, never typed by hand or by the bot.
"""
import json, sys
from datetime import date
from pathlib import Path
from verify_quotes import check
from trust_checks import flag_questions, answered_question, coverage

ROOT = Path(__file__).resolve().parent.parent
args = [a for a in sys.argv[1:] if not a.startswith("--")]
PUBLIC = "--public" in sys.argv
data_dir = ROOT / (args[0] if args else "data")
# optional per-dataset title and research questions (e.g. data/project.json)
PROJECT = json.loads((data_dir / "project.json").read_text(encoding="utf-8")) if (data_dir / "project.json").exists() else {}
rd = lambda p: json.loads(Path(p).read_text(encoding="utf-8"))

orgs, participants, interviews, insights, counter = [], [], [], [], []
CONTEXT = 2  # lines shown before/after each quote (v0.2)
for od in sorted(d for d in (data_dir / "organisations").glob("*") if d.is_dir()):
    if not (od / "organisation.json").exists():
        continue
    orgs.append(rd(od / "organisation.json"))
    participants += [rd(p) for p in sorted((od / "participants").glob("*.json"))]
    for idir in sorted(d for d in (od / "interviews").glob("*") if d.is_dir()):
        lines = (idir / "transcript.md").read_text(encoding="utf-8").splitlines()
        snap = rd(idir / "snapshot.json") if (idir / "snapshot.json").exists() else {}
        ins = rd(idir / "insights.json") if (idir / "insights.json").exists() else []
        ins = [i for i in ins if not i.get("mapping", {}).get("rejected")]  # rejected stay on disk for audit, not shown
        for i in ins:
            ok, why = check(i.get("quote"), lines, i.get("lines"), i.get("masked", False))
            if i.get("severity_quote"):
                sok, swhy = check(i["severity_quote"], lines, i.get("severity_lines") or i.get("lines"))
                ok, why = ok and sok, why if not ok else ("ok" if sok else "severity quote: " + swhy)
            i["verified"], i["verify_note"], i["date"] = ok, why, snap.get("date")
        # v0.2: which question was this an answer to, and was it yes/no or leading?
        flags = flag_questions(lines)
        flagged = {f["line"]: f for f in flags}
        for i in ins:
            asked = answered_question(lines, i["lines"][0])
            hit = next((flagged[n] for n in asked if n in flagged), None)
            i["asked_lines"] = asked
            i["weak_question"] = {"kind": hit["kind"], "reason": hit["reason"], "line": hit["line"]} if hit else None
        used_ranges = [i["lines"] for i in ins]  # approved + pending (rejected already removed)
        ces = rd(idir / "counter_evidence.json") if (idir / "counter_evidence.json").exists() else []
        ces = [c for c in ces if not c.get("rejected")]
        cov = coverage(lines, used_ranges + [c["lines"] for c in ces])
        for c in ces:
            c["verified"], c["verify_note"] = check(c.get("quote"), lines, c.get("lines"))
            c["date"] = snap.get("date")
            c["asked_lines"] = answered_question(lines, c["lines"][0])
            hit = next((flagged[n] for n in c["asked_lines"] if n in flagged), None)
            c["weak_question"] = {"kind": hit["kind"], "reason": hit["reason"], "line": hit["line"]} if hit else None
        counter += ces
        insights += ins
        if PUBLIC:
            keep = set()
            for i in ins:
                keep.update(range(i["lines"][0] - CONTEXT, i["lines"][1] + CONTEXT + 1))
                keep.update(i["asked_lines"])
            for c in ces:
                keep.update(range(c["lines"][0] - CONTEXT, c["lines"][1] + CONTEXT + 1))
            if snap.get("memorable_quote"):
                keep.update(range(snap["memorable_quote"]["lines"][0], snap["memorable_quote"]["lines"][1] + 1))
            lines = [l if (n + 1) in keep or n < 2 else None for n, l in enumerate(lines)]
        interviews.append({"id": idir.name, "org_id": od.name, "transcript": lines, "question_flags": flags,
                           "coverage": cov, **snap})

tree = rd(data_dir / "opportunities" / "tree.json")
ptype = {p["id"]: p["participant_type"] for p in participants}
opps = tree["opportunities"]
children = {o["id"]: [c["id"] for c in opps if c.get("parent_id") == o["id"]] for o in opps}

def signals(ids):
    ev = [i for i in insights if i.get("mapping", {}).get("opportunity_id") in ids and i.get("mapping", {}).get("approved")]
    by = lambda t: {i["participant_id"] for i in ev if ptype.get(i["participant_id"]) == t}
    sev = {k: sum(1 for i in ev if i["severity"] == k) for k in ["blocker", "workaround", "irritation", "unknown"]}
    beh = [i for i in ev if i["type"] in ("behaviour", "opinion", "feature_request")]
    return {
        "unique_target_customers": len(by("target_customer")),
        "adjacent_users": len(by("adjacent_user")),
        "experts": len(by("expert")),
        "total_mentions": len(ev),
        "interviews": len({i["interview_id"] for i in ev}),
        "severity_mix": sev,
        "behaviour_ratio": round(sum(1 for i in beh if i["type"] == "behaviour") / len(beh), 2) if beh else 0,
        "latest_evidence": max((i["date"] for i in ev if i.get("date")), default=None),
        "insight_ids": [i["id"] for i in ev],
    }
for o in opps:
    o["counter_evidence"] = [c["id"] for c in counter if c.get("approved") and c["opportunity_id"] in [o["id"]] + children[o["id"]]]
    o["children"] = children[o["id"]]
    o["signals"] = signals([o["id"]] + o["children"])

rq = {}
for i in insights:
    for q in i.get("research_questions", []):
        rq.setdefault(q, {"count": 0, "target": set()})
        rq[q]["count"] += 1
        if ptype.get(i["participant_id"]) == "target_customer":
            rq[q]["target"].add(i["participant_id"])
rq = {k: {"count": v["count"], "target_customers": len(v["target"])} for k, v in sorted(rq.items())}
interviewed = {t: len({p["id"] for p in participants if p["participant_type"] == t}) for t in ["target_customer", "adjacent_user", "expert"]}

out = {
    "meta": {"source": data_dir.name, "built": date.today().isoformat(), "demo": data_dir.name == "demo",
             "public": PUBLIC, "title": PROJECT.get("title", "Discovery Insights"), "subtitle": PROJECT.get("subtitle", "Demo · ESG reporting software (idea stage)")},
    "interviewed": interviewed,
    "research_questions": PROJECT.get("research_questions") or {"RQ1": "Pain points in preparing ESG reports", "RQ2": "Current tools & process",
                           "RQ3": "Needs from software", "RQ4": "Desired outcomes"},
    "rq_coverage": rq,
    "organisations": orgs, "participants": participants, "interviews": interviews,
    "insights": insights, "opportunities": opps, "counter_evidence": counter, "context_lines": CONTEXT,
    "changelog": (data_dir / "changelog.md").read_text(encoding="utf-8") if (data_dir / "changelog.md").exists() else "",
}
(ROOT / "web" / "data.js").write_text("window.DATA = " + json.dumps(out, ensure_ascii=False) + ";\n", encoding="utf-8")
bad = [i["id"] for i in insights + counter if not i["verified"]]
print(f"Built web/data.js from '{data_dir.name}': {len(interviews)} interviews, {len(insights)} insights, {len(opps)} opportunities")
print(f"Quotes verified: {len(insights) + len(counter) - len(bad)}/{len(insights) + len(counter)}" + (f"  FAILED: {', '.join(bad)}" if bad else ""))
