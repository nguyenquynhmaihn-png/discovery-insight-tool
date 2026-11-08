"""Apply the user's review decisions to one interview, update the tree and write the change log.

Usage:
  python3 scripts/approve.py INT-005 --all                      approve every pending proposal
  python3 scripts/approve.py INT-005 --ids INS-005-01,INS-005-03
  python3 scripts/approve.py INT-005 --reject INS-005-02
  add --data demo to work on the demo folder (default: data)

Edits (a different opportunity, a reworded title) are made in insights.json first; this
script only applies decisions. New opportunities get IDs here, never from the bot.
"""
import argparse, json, re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser()
ap.add_argument("interview"); ap.add_argument("--data", default="data")
ap.add_argument("--all", action="store_true"); ap.add_argument("--ids", default=""); ap.add_argument("--reject", default="")
a = ap.parse_args()

data = ROOT / a.data
tree_f = data / "opportunities" / "tree.json"
tree = json.loads(tree_f.read_text(encoding="utf-8"))
opps = tree["opportunities"]
ins_f = next(data.glob(f"organisations/*/interviews/{a.interview}/insights.json"))
insights = json.loads(ins_f.read_text(encoding="utf-8"))
today = date.today().isoformat()

def next_id(prefix, parent=None):
    if parent:
        n = [int(o["id"].split(".")[1]) for o in opps if o.get("parent_id") == parent]
        return f"{parent}.{max(n, default=0) + 1}"
    n = [int(re.match(rf"{prefix}-(\d+)$", o["id"]).group(1)) for o in opps if re.match(rf"{prefix}-(\d+)$", o["id"])]
    return f"{prefix}-{max(n, default=0) + 1:02d}"

pending = [i for i in insights if not i["mapping"].get("approved") and not i["mapping"].get("rejected")]
chosen = {x.strip() for x in a.ids.split(",") if x.strip()}
rejected = {x.strip() for x in a.reject.split(",") if x.strip()}
log = {"created": [], "reinforced": {}, "parked": [], "rejected": [], "followups": []}
made = {}  # proposed_title -> new id (so several insights can create one opportunity)

order = {"create_top": 0, "parking_lot": 1, "create_sub": 2, "attach": 3}
pending.sort(key=lambda i: order.get(i["mapping"]["action"], 9))
by_title = {o["title"].strip().lower(): o["id"] for o in opps}

for i in pending:
    m = i["mapping"]
    if i["id"] in rejected:
        m["rejected"] = True; log["rejected"].append(i["id"]); continue
    if not (a.all or i["id"] in chosen):
        continue
    act = m["action"]
    if act in ("create_top", "create_sub") or (act == "parking_lot" and not m.get("opportunity_id")):
        key = m["proposed_title"].strip().lower()
        if key not in made:
            if act == "create_sub":
                parent = m.get("parent_id") or made.get(m.get("parent_proposed_title", "").strip().lower()) \
                    or by_title.get(m.get("parent_proposed_title", "").strip().lower())
                ptitle = (m.get("parent_proposed_title") or "").strip()
                if not parent and ptitle:
                    # new parent proposed only through its sub-opportunities: create it too
                    parent = next_id("OPP")
                    opps.append({"id": parent, "parent_id": None, "title": ptitle, "scope": "in_scope", "status": "open",
                                 "created": today, "summary": None, "market_factor": None, "company_factor": None, "decision_rationale": None})
                    made[ptitle.lower()] = by_title[ptitle.lower()] = parent
                    log["created"].append(f"{parent} {ptitle}")
                if not parent:
                    print(f"SKIP {i['id']}: parent '{m.get('parent_proposed_title')}' not approved yet"); continue
                m["parent_id"] = parent
                oid, scope = next_id(None, parent), "in_scope"
            elif act == "parking_lot":
                oid, parent, scope = next_id("PARK"), None, "parking_lot"
            else:
                oid, parent, scope = next_id("OPP"), None, "in_scope"
            opps.append({"id": oid, "parent_id": parent, "title": m["proposed_title"], "scope": scope, "status": "open",
                         "created": today, "summary": None, "market_factor": None, "company_factor": None, "decision_rationale": None})
            made[key] = oid
            by_title[key] = oid
            (log["parked"] if scope == "parking_lot" else log["created"]).append(f"{oid} {m['proposed_title']}")
        m["opportunity_id"] = made[key]
    else:
        log["reinforced"][m["opportunity_id"]] = log["reinforced"].get(m["opportunity_id"], 0) + 1
    m["approved"] = True
    if i.get("needs_followup"):
        log["followups"].append(i["followup_question"])

# v0.2 counter-evidence: same --all / --ids / --reject switches
ce_f = ins_f.parent / "counter_evidence.json"
ces = json.loads(ce_f.read_text(encoding="utf-8")) if ce_f.exists() else []
log["counter"], log["counter_rejected"] = [], []
for c in ces:
    if c.get("approved") or c.get("rejected"):
        continue
    if c["id"] in rejected:
        c["rejected"] = True; log["counter_rejected"].append(c["id"])
    elif a.all or c["id"] in chosen:
        c["approved"] = True; log["counter"].append(f"{c['id']} against {c['opportunity_id']}")
if ces:
    ce_f.write_text(json.dumps(ces, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

tree["updated"] = today
tree_f.write_text(json.dumps(tree, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
ins_f.write_text(json.dumps(insights, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

entry = [f"## {today} — {a.interview}"]
if log["created"]: entry.append("- Created: " + "; ".join(log["created"]))
if log["reinforced"]: entry.append("- Reinforced: " + ", ".join(f"{k} (+{v})" for k, v in sorted(log["reinforced"].items())))
if log["parked"]: entry.append("- Parked: " + "; ".join(log["parked"]))
if log["rejected"]: entry.append("- Rejected by reviewer: " + ", ".join(log["rejected"]))
if log["counter"]: entry.append("- Counter-evidence added: " + "; ".join(log["counter"]))
if log["counter_rejected"]: entry.append("- Counter-evidence rejected: " + ", ".join(log["counter_rejected"]))
for q in log["followups"]: entry.append(f"- Follow-up added: {q}")
left = [i["id"] for i in insights if not i["mapping"].get("approved") and not i["mapping"].get("rejected")]
left += [c["id"] for c in ces if not c.get("approved") and not c.get("rejected")]
if left: entry.append("- Still pending: " + ", ".join(left))
cl = data / "changelog.md"
old = cl.read_text(encoding="utf-8") if cl.exists() else "# Change Log\n"
head, _, rest = old.partition("\n")
cl.write_text(head + "\n\n" + "\n".join(entry) + "\n\n" + rest.lstrip("\n"), encoding="utf-8")
print("\n".join(entry))
if log["created"]:
    print("\nNext: write a summary for each new opportunity (CLAUDE.md §10), then validate and build.")
