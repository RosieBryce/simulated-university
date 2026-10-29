#!/usr/bin/env python3
"""
Build the Stonegrove Hub estate from hub/source/.

    python hub/build/build_estate.py --seed 42

Steps:
  1. Read the bible (cast, sites, classification) and hub/source/values.yaml.
  2. Walk hub/source/. Every .md with front-matter is rendered to its real
     format at the same relative path in hub/output/estate/. Every other file
     (csv, xlsx, png, jpg, pdf) is copied as-is; its metadata comes from an
     optional <name>.meta.yaml sidecar, else from the library defaults.
  3. Apply mess rules (phase 3; --no-mess skips, and it is skipped if
     make_mess.py is absent).
  4. Lint every name and path against bible/filename_rules.yaml. Fail on any
     problem.
  5. Write docs/hub/data/manifest.json and text previews for the explorer.

The build never touches a file listed in bible/hand_supplied.yaml that is
already present in hub/source/.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import shutil
import sys
import time
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
HUB = HERE.parent
PROJECT = HUB.parent
sys.path.insert(0, str(HERE))

import renderers as R  # noqa: E402
from lint_filenames import Rules, lint_tree  # noqa: E402

BIBLE = HUB / "bible"
SOURCE = HUB / "source"
OUT = HUB / "output" / "estate"
DOCS_HUB = PROJECT / "docs" / "hub"
MANIFEST = DOCS_HUB / "data" / "manifest.json"
PREVIEWS = DOCS_HUB / "data" / "preview"

TEXT_PREVIEW_FORMATS = {"docx", "pdf", "pptx", "txt", "md", "vtt", "eml", "csv"}


# ----------------------------------------------------------------------
def load_bible() -> dict:
    b = {}
    for name in ["cast", "sites", "classification", "hand_supplied", "storylines_placeholder"]:
        p = BIBLE / f"{name}.yaml"
        if p.exists():
            b[name] = yaml.safe_load(p.read_text(encoding="utf-8"))
    values_path = SOURCE / "values.yaml"
    b["values"] = yaml.safe_load(values_path.read_text(encoding="utf-8")) if values_path.exists() else {}
    return b


def site_index(sites: dict) -> tuple[dict, dict, dict]:
    """folder_name -> site; (site folder, library folder) -> library; library id -> (site, library)."""
    by_folder, lib_by_folders, lib_by_id = {}, {}, {}
    for s in sites["sites"]:
        by_folder[s["folder_name"]] = s
        for lib in s["libraries"]:
            lib_by_folders[(s["folder_name"], lib["folder_name"])] = (s, lib)
            lib_by_id[lib["id"]] = (s, lib)
    return by_folder, lib_by_folders, lib_by_id


def date_str(d: dt.date) -> str:
    return d.isoformat()


# ----------------------------------------------------------------------
class Builder:
    def __init__(self, seed: int, apply_mess: bool, do_lint: bool):
        self.seed = seed
        self.apply_mess = apply_mess
        self.do_lint = do_lint
        self.bible = load_bible()
        self.cast = R.Cast(self.bible["cast"])
        self.values = R.HubValues(self.bible["values"])
        self.sites = self.bible["sites"]
        self.snapshot = R.parse_inworld_date(self.sites["snapshot_date"])
        self.site_by_folder, self.lib_by_folders, self.lib_by_id = site_index(self.sites)
        self.hand_supplied = {Path(f["path"]).as_posix() for f in self.bible.get("hand_supplied", {}).get("files", [])}
        self.files: list[dict] = []
        self.built: dict[str, Path] = {}   # source rel path (posix, with .md) -> output path
        self.problems: list[str] = []

    # ------------------------------------------------------------------
    def locate(self, rel: Path) -> tuple[dict | None, dict | None, str]:
        """From a source-relative path, find the site, library and folder path within the library."""
        parts = rel.parts
        if len(parts) < 2:
            return None, None, ""
        key = (parts[0], parts[1])
        if key not in self.lib_by_folders:
            return self.site_by_folder.get(parts[0]), None, "/".join(parts[2:-1])
        s, lib = self.lib_by_folders[key]
        return s, lib, "/".join(parts[2:-1])

    def default_meta(self, rel: Path) -> dict:
        s, lib, folder = self.locate(rel)
        return {
            "title": rel.stem,
            "author": (lib or s or {}).get("owner") if (lib and lib.get("owner")) else (s or {}).get("owner"),
            "created": date_str(self.snapshot),
            "modified": date_str(self.snapshot),
            "label": (lib or {}).get("default_label", (s or {}).get("default_label")),
            "sensitive": False,
            "site": (s or {}).get("id"),
            "library": (lib or {}).get("id"),
            "path": folder,
        }

    # ------------------------------------------------------------------
    def build(self) -> None:
        # The repo lives in a Google Drive folder, which holds handles on
        # recently written directories, so rmtree can fail with WinError 5.
        # Delete files first, then try the tree, and tolerate leftover dirs.
        if OUT.exists():
            for p in OUT.rglob("*"):
                if p.is_file():
                    try:
                        p.unlink()
                    except PermissionError:
                        time.sleep(0.5)
                        p.unlink()
            shutil.rmtree(OUT, ignore_errors=True)
        OUT.mkdir(parents=True, exist_ok=True)
        PREVIEWS.mkdir(parents=True, exist_ok=True)
        for old in PREVIEWS.glob("*.txt"):
            old.unlink()

        self.make_skeleton()

        sources = sorted(p for p in SOURCE.rglob("*") if p.is_file())
        md_docs = [p for p in sources if p.suffix == ".md" and p.name != "values.yaml"]
        raw_files = [p for p in sources if p.suffix != ".md" and p.name != "values.yaml" and not p.name.endswith(".meta.yaml")]

        # Pass 1: raw copies (hand-supplied assets, generated extracts)
        for p in raw_files:
            self.copy_raw(p)
        # Pass 2: everything renderable except emails
        docs = [R.read_source(p) for p in md_docs]
        for d in docs:
            if d.fmt != "eml":
                self.render_doc(d)
        # Pass 3: emails, which may attach built files
        for d in docs:
            if d.fmt == "eml":
                self.render_doc(d)

        if self.apply_mess:
            try:
                import make_mess  # noqa: F401
                make_mess.apply(self, OUT, self.seed)
            except ImportError:
                print("make_mess.py not present; skipping mess pass (phase 3)")

        self.collect_folders()
        if self.do_lint:
            rules = Rules(allow_tilde_dollar_prefix=self.apply_mess)
            problems = lint_tree(OUT, rules)
            if problems:
                print(f"lint_filenames: {len(problems)} problem(s)")
                for where, what in problems:
                    print(f"  {where}\n      {what}")
                raise SystemExit(1)
            print("lint_filenames: clean")
        self.write_manifest()
        self.publish_estate()

    def publish_estate(self) -> None:
        """Mirror the built tree into docs/hub/estate/ so the explorer can serve
        individual files and build folder zips in the browser."""
        pub = DOCS_HUB / "estate"
        if pub.exists():
            for p in pub.rglob("*"):
                if p.is_file():
                    try:
                        p.unlink()
                    except PermissionError:
                        time.sleep(0.5)
                        p.unlink()
            shutil.rmtree(pub, ignore_errors=True)
        shutil.copytree(OUT, pub, dirs_exist_ok=True)
        print(f"published estate -> {pub.relative_to(PROJECT)}")

    # ------------------------------------------------------------------
    def make_skeleton(self) -> None:
        for s in self.sites["sites"]:
            for lib in s["libraries"]:
                (OUT / s["folder_name"] / lib["folder_name"]).mkdir(parents=True, exist_ok=True)
                for f in lib.get("folders", []):
                    (OUT / s["folder_name"] / lib["folder_name"] / f).mkdir(parents=True, exist_ok=True)

    def out_for(self, rel_src: Path, ext: str) -> Path:
        return OUT / rel_src.with_suffix("." + ext)

    def copy_raw(self, p: Path) -> None:
        rel = p.relative_to(SOURCE)
        out = OUT / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, out)
        meta = self.default_meta(rel)
        sidecar = p.with_name(p.name + ".meta.yaml")
        if sidecar.exists():
            meta.update(yaml.safe_load(sidecar.read_text(encoding="utf-8")) or {})
        meta.setdefault("generated", "Data Extracts" in rel.parts)
        meta["hand_supplied"] = rel.as_posix() in self.hand_supplied
        self.register(out, meta, preview=None)
        self.built[rel.as_posix()] = out

    def render_doc(self, d: R.SourceDoc) -> None:
        rel = d.path.relative_to(SOURCE)
        meta = self.default_meta(rel)
        meta.update(d.meta)
        if rel.as_posix() in self.hand_supplied:
            # a hand-supplied .md would be odd, but honour the rule
            meta["hand_supplied"] = True
        out = self.out_for(rel, d.fmt)
        out.parent.mkdir(parents=True, exist_ok=True)
        label = meta.get("label")
        ctx = R.RenderContext(cast=self.cast, values=self.values, doc=d, out_path=out, label=label,
                              built_files=self.built)
        try:
            R.render(ctx)
        except Exception as e:  # keep going, report at end
            self.problems.append(f"{rel}: {type(e).__name__}: {e}")
            return
        preview = None
        if d.fmt in TEXT_PREVIEW_FORMATS:
            preview = self.write_preview(out, R.filled_body(ctx) if d.fmt != "vtt" else out.read_text(encoding="utf-8"))
        self.register(out, meta, preview)
        self.built[rel.as_posix()] = out

        # Transcripts also exported as docx, as Teams does
        if d.fmt == "vtt" and meta.get("also_docx"):
            docx_name = meta.get("docx_name") or (out.stem + " transcript.docx")
            out2 = out.with_name(docx_name)
            ctx2 = R.RenderContext(cast=self.cast, values=self.values, doc=d, out_path=out2, label=label,
                                   built_files=self.built)
            R.render_transcript_docx(ctx2)
            meta2 = dict(meta)
            meta2["title"] = meta.get("title", out.stem) + " (transcript)"
            meta2["derived_from"] = out.relative_to(OUT).as_posix()
            self.register(out2, meta2, self.write_preview(out2, out.read_text(encoding="utf-8")))

    def write_preview(self, out: Path, text: str) -> str:
        key = hashlib.sha1(out.relative_to(OUT).as_posix().encode("utf-8")).hexdigest()[:16]
        p = PREVIEWS / f"{key}.txt"
        p.write_text(text, encoding="utf-8")
        return f"data/preview/{key}.txt"

    def register(self, out: Path, meta: dict, preview: str | None) -> None:
        rel = out.relative_to(OUT).as_posix()
        author_id = meta.get("author")
        modified_by_id = meta.get("modified_by") or author_id
        modified = R.parse_inworld_date(meta.get("modified") or self.snapshot)
        created = R.parse_inworld_date(meta.get("created") or modified)
        entry = {
            "path": rel,
            "name": out.name,
            "ext": out.suffix.lower().lstrip("."),
            "size": out.stat().st_size,
            "title": meta.get("title") or out.stem,
            "author_id": author_id,
            "author": self.cast.short(author_id) if author_id and author_id in self.cast.people else (author_id or ""),
            "modified": date_str(modified),
            "modified_display": R.inworld_long(modified),
            "created": date_str(created),
            "modified_by": self.cast.short(modified_by_id) if modified_by_id in self.cast.people else (modified_by_id or ""),
            "label": meta.get("label"),
            "sensitive": bool(meta.get("sensitive", False)),
            "site": meta.get("site"),
            "library": meta.get("library"),
            "folder": rel.rsplit("/", 1)[0] if "/" in rel else "",
            "storylines": meta.get("storylines", []),
            "skills": meta.get("skills", []),
            "planted": meta.get("planted"),
            "planted_error": meta.get("planted_error"),
            "off_brand": meta.get("off_brand"),
            "hand_supplied": bool(meta.get("hand_supplied", False)),
            "placeholder": bool(meta.get("placeholder", False)),
            "generated": bool(meta.get("generated", False)),
            "derived_from": meta.get("derived_from"),
            "mess_rule": meta.get("mess_rule"),
            "preview": preview,
        }
        self.files.append(entry)

    # ------------------------------------------------------------------
    def collect_folders(self) -> None:
        self.folders = []
        for p in sorted(x for x in OUT.rglob("*") if x.is_dir()):
            rel = p.relative_to(OUT).as_posix()
            s, lib, _ = self.locate(Path(rel) / "x")
            self.folders.append({
                "path": rel,
                "name": p.name,
                "site": (s or {}).get("id"),
                "library": (lib or {}).get("id"),
                "label_default": (lib or {}).get("default_label", (s or {}).get("default_label")),
            })

    def write_manifest(self) -> None:
        MANIFEST.parent.mkdir(parents=True, exist_ok=True)
        sites_out = []
        for s in self.sites["sites"]:
            sites_out.append({
                "id": s["id"], "name": s["name"], "folder": s["folder_name"], "owner": s.get("owner"),
                "owner_name": self.cast.name(s.get("owner")) if s.get("owner") else "",
                "owner_title": self.cast.title(s["owner"]) if s.get("owner") else "",
                "description": s.get("description_in_world", "").strip(),
                "hint": s.get("hint", "").strip(), "skills": s.get("skills", []),
                "default_label": s.get("default_label"),
                "libraries": [{
                    "id": lib["id"], "name": lib["name"], "folder": lib["folder_name"],
                    "default_label": lib.get("default_label"), "hint": lib.get("hint", "").strip() if lib.get("hint") else "",
                    "budget": lib.get("budget", {}),
                } for lib in s["libraries"]],
            })
        manifest = {
            "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
            "seed": self.seed,
            "snapshot_date": date_str(self.snapshot),
            "snapshot_display": R.inworld_long(self.snapshot),
            "institution": self.cast.institution,
            "sites": sites_out,
            "folders": self.folders,
            "files": sorted(self.files, key=lambda f: f["path"].lower()),
            "counts": {"files": len(self.files), "folders": len(self.folders),
                       "bytes": sum(f["size"] for f in self.files)},
        }
        MANIFEST.write_text(json.dumps(manifest, indent=1, ensure_ascii=True), encoding="utf-8")
        mb = manifest["counts"]["bytes"] / 1_048_576
        print(f"manifest: {len(self.files)} files, {len(self.folders)} folders, {mb:.1f} MB -> {MANIFEST.relative_to(PROJECT)}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--no-mess", action="store_true", help="skip the mess pass")
    ap.add_argument("--skip-lint", action="store_true", help="do not fail on filename problems (debug only)")
    args = ap.parse_args()
    b = Builder(seed=args.seed, apply_mess=not args.no_mess, do_lint=not args.skip_lint)
    b.build()
    if b.problems:
        print(f"\n{len(b.problems)} document(s) failed to render:")
        for p in b.problems:
            print("  " + p)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
