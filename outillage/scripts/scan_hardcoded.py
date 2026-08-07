#!/usr/bin/env python3
"""Repère le texte anglais littéral dans kubejs/, config/fancymenu/, Dialog. Best-effort."""
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / "society-sunlit-valley"
out = []
JS_PAT = re.compile(
    r"(?:Text\.of|Component\.literal|\.tooltip|\.displayName|\.formattedText|\.name)"
    r"\s*\(\s*['\"]([A-Z][^'\"]{3,120})['\"]")
for js in (REPO / "kubejs").rglob("*.js"):
    for i, line in enumerate(js.read_text(errors="ignore").splitlines(), 1):
        for m in JS_PAT.finditer(line):
            out.append({"file": str(js.relative_to(REPO)), "line": i,
                        "text": m.group(1), "kind": "kubejs"})
FM_KEYS = {"label", "text", "title", "tooltip", "description"}
def walk(obj, f):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in FM_KEYS and isinstance(v, str) and re.search(r"[A-Za-z]{4}", v) \
               and not v.startswith(("%", "{", "fancymenu.", "society.")):
                out.append({"file": f, "line": 0, "text": v, "kind": "fancymenu"})
            else:
                walk(v, f)
    elif isinstance(obj, list):
        for v in obj:
            walk(v, f)
for jf in (REPO / "config" / "fancymenu").rglob("*.json"):
    try:
        walk(json.loads(jf.read_text(errors="ignore")), str(jf.relative_to(REPO)))
    except Exception:
        pass
dedup = {(o["file"], o["line"], o["text"]): o for o in out}
(ROOT / "fr-workspace" / "hardcoded-candidates.json").write_text(
    json.dumps(list(dedup.values()), ensure_ascii=False, indent=1) + "\n")
print(f"{len(dedup)} candidats")
