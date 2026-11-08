"""Validate all data files: schema, references between files, opportunity-tree rules,
and quote verification. Run after every extraction and before every build.

Usage: python3 scripts/validate.py [data_dir]   (default: data)
Exit code 1 if there are errors. Warnings do not fail, but should be reviewed.
"""
import json, sys
from pathlib import Path
from verify_quotes import verify_dir

ENUMS = {
    "org_type": {"company", "ngo", "consultancy", "professional_body", "investor", "other"},
    "participant_type": {"target_customer", "adjacent_user", "expert"},
    "type": {"behaviour", "opinion", "feature_request", "context"},
    "severity": {"blocker", "workaround", "irritation", "unknown"},
    "action": {"attach", "create_sub", "create_top", "parking_lot"},
    "confidence": {"high", "medium", "low"},
    "scope": {"in_scope", "parking_lot"},
    "status": {"open", "exploring", "addressed"},
}
RQS = {"RQ1", "RQ2", "RQ3", "RQ4"}
errors, warnings = [], []
err = lambda where, msg: errors.append(f"{where}: {msg}")
warn = lambda where, msg: warnings.append(f"{where}: {msg}")

def need(obj, where, fields):
    for f in fields:
        if f not in obj:
            err(where, f"missing field '{f}'")

def enum(obj, where, field, key=None):
    v = obj.get(field)
    if v is not None and v not in ENUMS[key or field]:
        err(where, f"{field}='{v}' not one of {sorted(ENUMS[key or field])}")

def main(data_dir):
    root = Path(data_dir)
    tree = json.loads((root / "opportunities" / "tree.json").read_text(encoding="utf-8"))
    opps = {}
    for o in tree.get("opportunities", []):
        w = f"tree/{o.get('id')}"
        need(o, w, ["id", "parent_id", "title", "scope", "status"])
        enum(o, w, "scope"); enum(o, w, "status")
        if o["id"] in opps:
            err(w, "duplicate id")
        opps[o["id"]] = o
    for o in opps.values():
        w = f"tree/{o['id']}"
        p = o.get("parent_id")
        if p:
            if p not in opps:
                err(w, f"parent '{p}' does not exist")
            elif opps[p].get("parent_id"):
                err(w, "tree is deeper than 2 levels (parent is itself a sub-opportunity)")
    for o in opps.values():
        kids = [c for c in opps.values() if c.get("parent_id") == o["id"]]
        if len(kids) == 1:
            warn(f"tree/{o['id']}", f"vertical branch: only one child ({kids[0]['id']}); merge or find the missing sibling")

    parts, orgs, ins_ids, used, rejected = {}, set(), set(), {}, set()
    top_titles, deferred = set(), []
    for od in sorted(d for d in (root / "organisations").glob("*") if d.is_dir()):
        if not (od / "organisation.json").exists():
            err(od.name, "missing organisation.json"); continue
        org = json.loads((od / "organisation.json").read_text(encoding="utf-8"))
        need(org, od.name, ["id", "pseudonym", "org_type", "fits_icp", "source"]); enum(org, od.name, "org_type")
        orgs.add(org["id"])
        for pf in sorted((od / "participants").glob("*.json")):
            p = json.loads(pf.read_text(encoding="utf-8"))
            need(p, pf.stem, ["id", "org_id", "role", "participant_type"]); enum(p, pf.stem, "participant_type")
            parts[p["id"]] = p
        for idir in sorted(d for d in (od / "interviews").glob("*") if d.is_dir()):
            if not (idir / "transcript.md").exists():
                err(idir.name, "missing transcript.md")
            if (idir / "counter_evidence.json").exists():
                for ce in json.loads((idir / "counter_evidence.json").read_text(encoding="utf-8")):
                    w = ce.get("id", "?")
                    need(ce, w, ["id", "interview_id", "participant_id", "opportunity_id", "quote", "lines", "reason", "approved"])
                    if ce.get("interview_id") != idir.name:
                        err(w, f"interview_id '{ce.get('interview_id')}' does not match folder '{idir.name}'")
                    if ce.get("opportunity_id") not in opps:
                        err(w, f"counter-evidence points to unknown opportunity '{ce.get('opportunity_id')}'")
                    if ce.get("rejected"):
                        rejected.add(w)
                    elif not ce.get("approved"):
                        warn(w, "counter-evidence proposal: needs the user's decision")
            if not (idir / "insights.json").exists():
                continue
            for i in json.loads((idir / "insights.json").read_text(encoding="utf-8")):
                w = i.get("id", "?")
                need(i, w, ["id", "interview_id", "org_id", "participant_id", "type", "research_questions",
                            "statement", "quote", "lines", "severity", "mapping"])
                if w in ins_ids:
                    err(w, "duplicate insight id")
                ins_ids.add(w)
                enum(i, w, "type"); enum(i, w, "severity")
                if i.get("interview_id") != idir.name:
                    err(w, f"interview_id '{i.get('interview_id')}' does not match folder '{idir.name}'")
                if i.get("participant_id") not in parts:
                    err(w, f"participant '{i.get('participant_id')}' has no profile")
                if not set(i.get("research_questions", [])) <= RQS or not i.get("research_questions"):
                    err(w, "research_questions must be a non-empty subset of RQ1-RQ4")
                if not (isinstance(i.get("lines"), list) and len(i["lines"]) == 2):
                    err(w, "lines must be [from, to]")
                if i.get("severity") not in (None, "unknown") and not i.get("severity_quote"):
                    err(w, f"severity '{i['severity']}' needs a severity_quote as evidence")
                if i.get("needs_followup") and not i.get("followup_question"):
                    err(w, "needs_followup is true but followup_question is empty")
                if i.get("type") == "feature_request" and not i.get("linked_insight_ids") and not i.get("needs_followup"):
                    warn(w, "feature request with no linked underlying need and no follow-up")
                m = i.get("mapping") or {}
                need(m, w + ".mapping", ["action", "confidence", "reason", "approved"])
                enum(m, w, "action"); enum(m, w, "confidence")
                if m.get("rejected"):
                    rejected.add(w)
                    continue
                if m.get("approved"):
                    if m.get("opportunity_id") not in opps:
                        err(w, f"approved but opportunity '{m.get('opportunity_id')}' is not in tree.json")
                    else:
                        used[m["opportunity_id"]] = used.get(m["opportunity_id"], 0) + 1
                else:
                    a = m.get("action")
                    if a == "attach" and m.get("opportunity_id") not in opps:
                        err(w, f"attach proposal points to unknown opportunity '{m.get('opportunity_id')}'")
                    if a in ("create_sub", "create_top") and not m.get("proposed_title"):
                        err(w, f"{a} proposal needs proposed_title")
                    if a == "create_top":
                        top_titles.add(m.get("proposed_title", "").strip().lower())
                    if a == "create_sub" and m.get("parent_id") not in opps:
                        deferred.append((w, (m.get("parent_proposed_title") or "").strip().lower()))
                    if m.get("confidence") != "high":
                        warn(w, f"{m.get('confidence')}-confidence proposal: needs the user's decision")
    existing_titles = {o["title"].strip().lower() for o in opps.values()}
    for w, pt in deferred:
        if not pt:
            err(w, "create_sub needs an existing parent_id or a parent_proposed_title")
        elif pt not in top_titles and pt not in existing_titles:
            warn(w, f"create_sub also creates a new parent: '{pt}'")
    for o in opps.values():
        kids = [c for c in opps.values() if c.get("parent_id") == o["id"]]
        if not used.get(o["id"]) and not any(used.get(k["id"]) for k in kids):
            warn(f"tree/{o['id']}", "no approved evidence attached")

    for i, ok, why in verify_dir(root):
        if not ok and i.split(" ")[0] not in rejected:
            err(i, "quote check failed: " + why)

    for e in errors:
        print("ERROR  " + e)
    for x in warnings:
        print("WARN   " + x)
    print(f"\n{len(errors)} errors, {len(warnings)} warnings · {len(orgs)} organisations, {len(parts)} participants, {len(ins_ids)} insights, {len(opps)} opportunities")
    return 1 if errors else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "data"))
