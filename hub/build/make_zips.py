#!/usr/bin/env python3
"""
Zip the built Stonegrove Hub estate for download.

    python hub/build/make_zips.py

Reads hub/output/estate/ and docs/hub/data/manifest.json. Writes to
docs/hub/downloads/:
    stonegrove-hub.zip                      the whole estate
    stonegrove-hub-<site-slug>.zip          one per site
Each zip has a README.txt at its root and uses in-world Modified dates
(mapped to real years) as file timestamps. Empty folders are preserved.
"""

from __future__ import annotations

import json
import re
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
HUB = HERE.parent
PROJECT = HUB.parent
sys.path.insert(0, str(HERE))
import renderers as R  # noqa: E402

ESTATE = HUB / "output" / "estate"
MANIFEST = PROJECT / "docs" / "hub" / "data" / "manifest.json"
DOWNLOADS = PROJECT / "docs" / "hub" / "downloads"
ROOT = "stonegrove-hub"

README = """Stonegrove Hub
==============

This is a snapshot of the Stonegrove Hub, the intranet document estate of
Stonegrove University, taken on {snapshot}.

Stonegrove University is fictional. Every person, student, applicant,
organisation, case, figure and document in this archive is synthetic. Any
resemblance to a real person or institution is coincidental. The material is
provided so that learners can practise working with institutional documents,
including sensitive-looking ones, with nothing real at risk.

Contents: {files} files in {folders} folders{scope}.

Produced by the Stonegrove University project (RosieBryce/simulated-university).
All rights reserved. The archive may be used for personal learning, teaching
and research. It may not be redistributed or used commercially without
permission. See the LICENSE file in the project repository.

A browsable version, a learner guide and the full Stonegrove dataset are at
the project website.
"""


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def zinfo(arcname: str, when: R.dt.date) -> zipfile.ZipInfo:
    real = R.real_date(when)
    zi = zipfile.ZipInfo(arcname, date_time=(real.year, real.month, real.day, real.hour, real.minute, 0))
    zi.compress_type = zipfile.ZIP_DEFLATED
    zi.external_attr = 0o644 << 16
    return zi


def build_zip(out_path: Path, files: list[dict], folders: list[dict], snapshot: str, scope: str) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    snap_date = R.parse_inworld_date(snapshot)
    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        readme = README.format(snapshot=R.inworld_long(snap_date), files=len(files), folders=len(folders), scope=scope)
        zf.writestr(zinfo(f"{ROOT}/README.txt", snap_date), readme.replace("\n", "\r\n"))
        for fo in folders:
            zi = zinfo(f"{ROOT}/{fo['path']}/", snap_date)
            zi.external_attr = (0o40755 << 16) | 0x10
            zf.writestr(zi, b"")
        for f in files:
            src = ESTATE / f["path"]
            zi = zinfo(f"{ROOT}/{f['path']}", R.parse_inworld_date(f["modified"]))
            zf.write(src, arcname=zi.filename)  # arcname only; timestamp set below
        # zipfile.write ignores our ZipInfo, so rewrite dates in place
    # Second pass to apply in-world timestamps (zipfile.write uses mtime). Cheap for our sizes.
    tmp = out_path.with_suffix(".tmp.zip")
    with zipfile.ZipFile(out_path) as zin, zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zout:
        by_path = {f"{ROOT}/{f['path']}": f for f in files}
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename in by_path:
                zi = zinfo(item.filename, R.parse_inworld_date(by_path[item.filename]["modified"]))
            else:
                zi = item
            zout.writestr(zi, data)
    tmp.replace(out_path)


def main() -> int:
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    files, folders = m["files"], m["folders"]
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    for old in DOWNLOADS.glob("*.zip"):
        old.unlink()

    whole = DOWNLOADS / f"{ROOT}.zip"
    build_zip(whole, files, folders, m["snapshot_date"], "")
    print(f"  {whole.name}  {whole.stat().st_size / 1_048_576:.1f} MB")

    index = {"estate": whole.name, "sites": {}}
    for s in m["sites"]:
        sf, sl = s["folder"], slug(s["folder"])
        fs = [f for f in files if f["path"].split("/")[0] == sf]
        fo = [f for f in folders if f["path"].split("/")[0] == sf]
        out = DOWNLOADS / f"{ROOT}-{sl}.zip"
        build_zip(out, fs, fo, m["snapshot_date"], f", {s['name']} only")
        index["sites"][s["id"]] = out.name
        print(f"  {out.name}  {out.stat().st_size / 1_048_576:.2f} MB  ({len(fs)} files)")
    (DOWNLOADS / "index.json").write_text(json.dumps(index, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
