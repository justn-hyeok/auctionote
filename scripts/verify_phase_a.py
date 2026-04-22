import json
import pathlib
import sys

m_path = pathlib.Path("fixtures/MANIFEST.json")
if not m_path.exists():
    print("MANIFEST.json missing")
    sys.exit(1)

m = json.loads(m_path.read_text())
raws = list(pathlib.Path("fixtures/raw").glob("*.html"))
exps = list(pathlib.Path("fixtures/expected").glob("*.json"))

errors = []
if len(raws) < 8:
    errors.append(f"raw HTML too few: {len(raws)}")
if len(exps) < 8:
    errors.append(f"expected JSON too few: {len(exps)}")
if not m.get("robots_txt_checked"):
    errors.append("robots_txt_checked is not true")

details = [f for f in m.get("files", []) if f.get("type") == "detail"]
if len(details) < 6:
    errors.append(f"details too few: {len(details)}")

for f in m.get("files", []):
    if not pathlib.Path(f["raw"]).exists():
        errors.append(f"missing raw: {f['raw']}")
    if not pathlib.Path(f["expected"]).exists():
        errors.append(f"missing expected: {f['expected']}")

if errors:
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)

print("phase A verification: ok")
