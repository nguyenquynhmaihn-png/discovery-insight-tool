"""Convert raw Teams .docx transcripts in private/ into anonymised, one-turn-per-line
transcripts in inbox/, ready for analysis.

Output line format:  [mm:ss] SPEAKER: text
- Interviewer lines are labelled 'Interviewer-...' and are never valid evidence.
- Real names are replaced using private/pseudonyms.json.
- Only mechanical fixes are made (spacing after full stops, system lines removed).
  Wording is never changed, so quotes stay verbatim.

Usage: python3 scripts/normalize_transcripts.py
"""
import html, json, re, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "private" / "pseudonyms.json").read_text(encoding="utf-8"))
TURN = re.compile(r"^(.+?)\s+(\d{1,2}:\d{2}(?::\d{2})?)(.*)$")
DATE = re.compile(r"^\d{1,2} \w+ \d{4}, \d{1,2}:\d{2}\s*[ap]m$", re.I)

def paragraphs(docx):
    xml = zipfile.ZipFile(docx).read("word/document.xml").decode("utf-8")
    for p in re.findall(r"<w:p[ >].*?</w:p>", xml, flags=re.S):
        t = html.unescape("".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", p, flags=re.S))).strip()
        if t:
            yield t

def anonymise(text):
    for real, alias in sorted(CFG["replace_in_text"].items(), key=lambda kv: -len(kv[0])):
        text = re.sub(rf"\b{re.escape(real)}\b", alias, text)
    return text

def tidy(text):
    text = re.sub(r"([a-z0-9][.?!])([A-Z])", r"\1 \2", text)  # "time.In" -> "time. In"
    return re.sub(r"\s+", " ", text).strip()

def convert(docx, meta):
    date, turns, unknown = None, [], set()
    for p in paragraphs(docx):
        if DATE.match(p):
            date = p
            continue
        if p.lower() == "transcript" or p.endswith("transcription"):
            continue
        m = TURN.match(p)
        if not m:
            continue
        name, ts, text = m.group(1).strip(), m.group(2), m.group(3)
        spk = CFG["speakers"].get(name)
        if not spk:
            unknown.add(name)
            spk = "UNKNOWN"
        turns.append(f"[{ts}] {spk}: {anonymise(tidy(text))}")
    header = [f"# {meta['id']} — participant {meta['participant']} ({date or 'date not found'})",
              "# Source: Microsoft Teams transcript, anonymised. Interviewer lines are not evidence.", ""]
    return header + turns, unknown

if __name__ == "__main__":
    (ROOT / "inbox").mkdir(exist_ok=True)
    for name, meta in CFG["interviews"].items():
        src = ROOT / "private" / name
        if not meta.get("id"):
            print(f"SKIP {name}: {meta.get('skip_reason')}")
            continue
        lines, unknown = convert(src, meta)
        out = ROOT / "inbox" / f"{meta['id']}.md"
        out.write_text("\n".join(lines) + "\n", encoding="utf-8")
        leaks = [r for r in CFG["replace_in_text"] if re.search(rf"\b{re.escape(r)}\b", "\n".join(lines))]
        print(f"OK   {name} -> inbox/{out.name}: {len(lines) - 3} turns"
              + (f" | UNKNOWN SPEAKERS: {unknown}" if unknown else "")
              + (f" | NAME LEAK: {leaks}" if leaks else ""))
