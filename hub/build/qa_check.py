#!/usr/bin/env python3
"""
QA checks for the Stonegrove Hub against the built manifest.

    python hub/build/qa_check.py

Checks, and prints a report:
  1. Every planted item, planted error and off-brand file in the bible is
     present in the manifest at the stated location with the stated label.
  2. Every transcript in sites.yaml exists, with its docx export.
  3. Every Learner Guide starting point (hash route in docs/hub/guide.html)
     resolves to a site, library or folder that exists.
  4. The guardrails scenario: which files an AI relying on labels alone would
     read that are in truth sensitive, per site.
  5. Slop and contact checks over everything that ships (previews, guide,
     explorer, README text).
Exits non-zero if any structural check fails.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote

import yaml

HERE = Path(__file__).resolve().parent
HUB = HERE.parent
PROJECT = HUB.parent
BIBLE = HUB / "bible"
MANIFEST = PROJECT / "docs" / "hub" / "data" / "manifest.json"


def main() -> int:
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    files = m["files"]
    by_path = {f["path"]: f for f in files}
    folders = {f["path"] for f in m["folders"]}
    sites = yaml.safe_load((BIBLE / "sites.yaml").read_text(encoding="utf-8"))
    cls = yaml.safe_load((BIBLE / "classification.yaml").read_text(encoding="utf-8"))
    errs = yaml.safe_load((BIBLE / "planted_errors.yaml").read_text(encoding="utf-8"))
    brand = yaml.safe_load((BIBLE / "off_brand.yaml").read_text(encoding="utf-8"))
    lib_folder = {lib["id"]: f"{s['folder_name']}/{lib['folder_name']}" for s in sites["sites"] for lib in s["libraries"]}
    failures: list[str] = []

    # 1. planted items
    print("Planted sensitive items")
    for p in cls["planted"]:
        rel = f"{lib_folder[p['library']]}/{p['path']}/{p['file']}".replace("//", "/")
        f = by_path.get(rel)
        if not f:
            failures.append(f"{p['id']} missing: {rel}")
            print(f"  MISSING {p['id']}  {rel}")
            continue
        ok = (f["label"] == p["label"]) and f["sensitive"]
        print(f"  {'ok ' if ok else 'BAD'} {p['id']}  label={f['label']!s:<13} sensitive={f['sensitive']}  {p['file']}")
        if not ok:
            failures.append(f"{p['id']} label/sensitive mismatch")
    print("Planted errors")
    for e in errs["errors"]:
        hits = [f for f in files if f["name"] == e["file"] and f.get("library") == e["library"]]
        print(f"  {'ok ' if hits else 'MISSING'} {e['id']}  {e['file']}")
        if not hits:
            failures.append(f"{e['id']} missing")
    print("Off-brand plantings")
    for b in brand["planted"]:
        present = [fn for fn in b["files"] if any(f["name"] == fn for f in files)]
        print(f"  {'ok ' if len(present) == len(b['files']) else 'PART'} {b['id']}  {len(present)}/{len(b['files'])} files")
        if not present:
            failures.append(f"{b['id']} has no files present")

    # 2. transcripts
    print("Transcripts")
    for t in sites["transcripts"]:
        vtts = [f for f in files if f["ext"] == "vtt" and f.get("library") == t["library"]]
        docxs = [f for f in files if f["ext"] == "docx" and f.get("library") == t["library"] and "transcript" in f["name"].lower()]
        print(f"  {'ok ' if vtts else 'MISSING'} {t['id']}  {t['title']}  vtt={len(vtts)} docx={len(docxs)}")
        if not vtts:
            failures.append(f"{t['id']} transcript missing")

    # 3. guide routes
    print("Learner Guide routes")
    guide = (PROJECT / "docs" / "hub" / "guide.html").read_text(encoding="utf-8")
    site_ids = {s["id"]: s for s in sites["sites"]}
    for route in sorted(set(re.findall(r'href="index\.html#/([^"]+)"', guide))):
        parts = [unquote(p) for p in route.split("/")]
        s = site_ids.get(parts[0])
        if not s:
            failures.append(f"guide route bad site: {route}")
            print(f"  BAD  {route}")
            continue
        if len(parts) == 1:
            print(f"  ok   {route}")
            continue
        lib = next((l for l in s["libraries"] if l["id"] == parts[1]), None)
        if not lib:
            failures.append(f"guide route bad library: {route}")
            print(f"  BAD  {route}")
            continue
        folder = "/".join([s["folder_name"], lib["folder_name"]] + parts[2:])
        ok = folder in folders
        print(f"  {'ok  ' if ok else 'BAD '} {route}")
        if not ok:
            failures.append(f"guide route bad folder: {route}")

    # 4. guardrails scenario
    print("Guardrails: sensitive files an AI trusting labels would read (label is not Confidential)")
    by_site: dict[str, list[dict]] = {}
    for f in files:
        if f["sensitive"] and f["label"] != "Confidential":
            by_site.setdefault(f["site"], []).append(f)
    for sid, lst in sorted(by_site.items()):
        print(f"  {sid}: {len(lst)}")
        for f in lst:
            print(f"      [{f['label'] or 'no label'}] {f['path']}")
    total_sensitive = sum(1 for f in files if f["sensitive"])
    correctly = sum(1 for f in files if f["sensitive"] and f["label"] == "Confidential")
    print(f"  sensitive files: {total_sensitive}; correctly labelled Confidential: {correctly}; exposed: {total_sensitive - correctly}")

    # 5. slop and contacts
    print("Slop and contact checks")
    texts: list[tuple[str, str]] = []
    for p in (PROJECT / "docs" / "hub").glob("*.html"):
        texts.append((p.name, p.read_text(encoding="utf-8")))
    for p in (PROJECT / "docs" / "hub" / "data" / "preview").glob("*.txt"):
        texts.append((p.name, p.read_text(encoding="utf-8")))
    texts.append(("hub/README.md", (HUB / "README.md").read_text(encoding="utf-8")))
    texts.append(("sites.yaml hints", "\n".join(str(l.get("hint", "")) for s in sites["sites"] for l in s["libraries"]) + "\n".join(str(s.get("hint", "")) for s in sites["sites"])))
    dash = [n for n, t in texts if "—" in t or "–" in t]
    tells = re.compile(r"\b(delve|robust|leverage|streamline|landscape|crucial|it's worth noting|seamless|tapestry|testament to)\b", re.I)
    told = [(n, tells.search(t).group(0)) for n, t in texts if tells.search(t)]
    bad_contacts = []
    for n, t in texts:
        for em in re.findall(r"[\w.-]+@[\w.-]+\.[a-z]{2,}", t):
            if not em.endswith(".example") and "stonegrove.ac.example" not in em:
                bad_contacts.append((n, em))
        for num in re.findall(r"\b0\d{3,4} ?\d{3} ?\d{3,4}\b", t):
            d = num.replace(" ", "")
            if not (d.startswith("01632960") or d.startswith("07700900")):
                bad_contacts.append((n, num))
    print(f"  em/en dashes in: {dash or 'none'}")
    print(f"  stock words: {told[:5] or 'none'}")
    print(f"  contact problems: {bad_contacts[:5] or 'none'}")
    if dash or bad_contacts:
        failures.append("slop or contact check failed")

    print()
    if failures:
        print(f"QA: {len(failures)} failure(s)")
        for x in failures:
            print("  " + x)
        return 1
    print("QA: all structural checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
