#!/usr/bin/env python3
"""
Apply the deliberate mess to a built Stonegrove Hub estate.

Called by build_estate.py after rendering and before linting:

    make_mess.apply(builder, estate_root, seed)

Reads bible/mess_rules.yaml and bible/sites.yaml. Every file it creates is a
copy (sometimes altered) of a file the build already produced, and is added
to the builder's manifest with `derived_from` and `mess_rule`, so the truth
is always recoverable. Nothing here invents content; it duplicates, renames,
misdates, mislabels and litters.

Deterministic for a given seed.
"""

from __future__ import annotations

import datetime as dt
import random
import shutil
from pathlib import Path

import yaml

import renderers as R

HERE = Path(__file__).resolve().parent
BIBLE = HERE.parent / "bible"

def longpath(p: Path) -> str:
    """Extended-length path prefix so copies beyond MAX_PATH work on Windows."""
    s = str(p.resolve())
    bs = chr(92)
    prefix = bs * 2 + "?" + bs
    if len(s) > 1 and s[1] == ":" and not s.startswith(prefix):
        return prefix + s
    return s

JUNK_FILES = ["Document1.docx", "Book1.xlsx", "Untitled.docx", "New Text Document.txt", "Presentation1.pptx", "Document2.docx", "Copy of Book1.xlsx"]


# ----------------------------------------------------------------------
class Mess:
    def __init__(self, builder, root: Path, seed: int):
        self.b = builder
        self.root = root
        self.rng = random.Random(seed)
        self.rules = yaml.safe_load((BIBLE / "mess_rules.yaml").read_text(encoding="utf-8"))
        self.by_rule = {r["id"]: r for r in self.rules["rules"]}
        self.habits = self.rules.get("author_habits", {})
        self.lib_profiles: dict[str, str] = {}
        self.lib_folder: dict[str, str] = {}
        self.site_of_lib: dict[str, dict] = {}
        for s in self.b.sites["sites"]:
            for lib in s["libraries"]:
                self.lib_profiles[lib["id"]] = lib.get("mess_profile", s.get("mess_profile", "normal"))
                self.lib_folder[lib["id"]] = f"{s['folder_name']}/{lib['folder_name']}"
                self.site_of_lib[lib["id"]] = s
        self.made = 0
        self.index = {f["path"]: f for f in self.b.files}
        self.max_path = yaml.safe_load((BIBLE / "filename_rules.yaml").read_text(encoding="utf-8"))["structure"]["max_path_length_in_zip"]

    # ------------------------------------------------------------ helpers
    def libs_with(self, profiles: list[str]) -> list[str]:
        return [lid for lid, p in self.lib_profiles.items() if p in profiles]

    def applies(self, rule: dict) -> list[str]:
        out: list[str] = []
        for a in rule.get("applies_to", []):
            if a in ("tidy", "normal", "chaotic", "island"):
                out.extend(self.libs_with([a]))
            elif a in self.lib_profiles:
                out.append(a)
        return [lid for lid in dict.fromkeys(out) if self.lib_profiles[lid] != "island"]

    def files_in(self, lib_id: str, exts=("docx", "xlsx", "pptx", "pdf")) -> list[dict]:
        return [f for f in self.b.files if f.get("library") == lib_id and f["ext"] in exts
                and not f.get("derived_from") and not f.get("planted") and not f.get("generated")
                and not f.get("hand_supplied") and not f.get("sensitive")]

    def rand_count(self, spec, profile: str) -> int:
        if isinstance(spec, dict):
            spec = spec.get(profile, [0, 0])
        lo, hi = spec
        return self.rng.randint(lo, hi)

    def unique(self, rel: str) -> str:
        p = Path(rel)
        cand, n = rel, 2
        while (self.root / cand).exists():
            cand = str(p.with_name(f"{p.stem} ({n}){p.suffix}")).replace("\\", "/")
            n += 1
        return cand

    def derive(self, src: dict, new_rel: str, rule: str, *, modified: str | None = None, modified_by=None,
               label=..., title: str | None = None, alter: str | None = None, note: str | None = None) -> dict | None:
        """Copy src to new_rel (relative to root), optionally alter, register in manifest."""
        new_rel = new_rel.replace("\\", "/")
        src_path = self.root / src["path"]
        dst = self.root / new_rel
        if dst.exists() or not src_path.exists():
            return None
        if len("stonegrove-hub/" + new_rel) > self.max_path:
            return None  # would break Windows extraction; the lint would reject it anyway
        dst.parent.mkdir(parents=True, exist_ok=True)
        # Windows MAX_PATH: deep StoneShare chains plus the repo path can exceed 260
        shutil.copy2(longpath(src_path), longpath(dst))
        if alter:
            self.alter(dst, alter)
        meta = {
            "title": title or src.get("title"),
            "author": src.get("author_id"),
            "modified_by": src.get("author_id") if modified_by is None else modified_by,
            "created": src.get("created"),
            "modified": modified or src.get("modified"),
            "label": src.get("label") if label is ... else label,
            "sensitive": src.get("sensitive", False),
            "site": src.get("site"),
            "library": src.get("library"),
            "path": new_rel.rsplit("/", 1)[0] if "/" in new_rel else "",
            "storylines": src.get("storylines", []),
            "skills": src.get("skills", []),
            "planted": None,
            "derived_from": src["path"],
            "mess_rule": rule,
        }
        if note:
            meta["mess_note"] = note
        self.b.register(dst, meta, src.get("preview"))
        entry = self.b.files[-1]
        if note:
            entry["mess_note"] = note
        # modified_by may be a display string rather than cast id
        if isinstance(modified_by, str) and modified_by not in self.b.cast.people:
            entry["modified_by"] = modified_by
        self.index[new_rel] = entry
        self.made += 1
        return entry

    def alter(self, path: Path, how: str) -> None:
        ext = path.suffix.lower()
        try:
            if ext == ".docx" and how in ("drop_paragraph", "changed", "incomplete"):
                import docx
                d = docx.Document(path)
                paras = [p for p in d.paragraphs if p.text.strip()]
                if len(paras) > 3:
                    victim = paras[-2] if how != "incomplete" else paras[len(paras) // 2]
                    victim._element.getparent().remove(victim._element)
                if how == "incomplete":
                    d.add_paragraph("[to be completed]")
                d.save(path)
            elif ext == ".xlsx":
                from openpyxl import load_workbook
                wb = load_workbook(path)
                if how.startswith("drop_sheet:"):
                    name = how.split(":", 1)[1]
                    if name in wb.sheetnames and len(wb.sheetnames) > 1:
                        wb.remove(wb[name])
                elif how == "break_formulas":
                    for ws in wb.worksheets:
                        for row in ws.iter_rows():
                            for c in row:
                                if isinstance(c.value, str) and c.value.startswith("=INDEX"):
                                    c.value = "#REF!"
                elif how in ("changed", "incomplete"):
                    ws = wb.worksheets[-1]
                    ws.append(["updated" if how == "changed" else "TODO: finish this"])
                wb.save(path)
            elif ext == ".pptx" and how in ("changed", "incomplete"):
                from pptx import Presentation
                prs = Presentation(path)
                if len(prs.slides) > 2:
                    xml_slides = prs.slides._sldIdLst
                    slides = list(xml_slides)
                    xml_slides.remove(slides[-1])
                prs.save(path)
        except Exception:
            pass  # an unaltered copy is still a valid copy

    def shift_date(self, iso: str, days: int) -> str:
        d = R.parse_inworld_date(iso) + dt.timedelta(days=days)
        if d > self.b.snapshot:
            d = self.b.snapshot
        return d.isoformat()

    def other_person(self, site_id: str, exclude: str | None) -> str:
        people = [p["id"] for p in self.b.bible["cast"]["staff"] if p.get("site") == site_id and p["id"] != exclude]
        return self.rng.choice(people) if people else (exclude or "")

    # ------------------------------------------------------------ rules
    def version_sprawl(self) -> None:
        rule = self.by_rule["version_sprawl"]
        params = rule["params"]
        # Named lineages first
        for key, lin in rule.get("named_lineages", {}).items():
            folder = f"{self.lib_folder[lin['library']]}/{lin['path']}".rstrip("/")
            root_rel = f"{folder}/{lin['root']}"
            src = self.index.get(root_rel)
            if not src:
                # fall back to the sibling marked true_latest if it was authored
                for sib in lin["siblings"]:
                    if sib.get("true_latest") and self.index.get(f"{folder}/{sib['name']}"):
                        src = self.index[f"{folder}/{sib['name']}"]
                        break
            if not src:
                continue
            for sib in lin["siblings"]:
                rel = f"{folder}/{sib['name']}"
                if self.index.get(rel):
                    continue
                content = str(sib.get("content", ""))
                alter = None
                low = content.lower()
                if "missing tab" in low:
                    alter = "drop_sheet:Legend"
                elif "formulas broken" in low:
                    alter = "break_formulas"
                elif "byte-identical" in low or sib.get("true_latest"):
                    alter = None
                elif "incomplete" in low or "consolidation" in low:
                    alter = "incomplete"
                else:
                    alter = "changed"
                self.derive(src, rel, "version_sprawl", modified=str(sib.get("modified", src["modified"])),
                            modified_by=self.rng.choice([src.get("author_id"), self.other_person(src["site"], src.get("author_id"))]),
                            alter=alter, note=content or None)
        # Random sprawl
        for lib_id in self.applies(rule):
            profile = self.lib_profiles[lib_id]
            roots = self.files_in(lib_id)
            self.rng.shuffle(roots)
            n_roots = {"normal": 2, "chaotic": 4}.get(profile, 0)
            for src in roots[:n_roots]:
                k = self.rand_count(params["siblings_per_root"], profile)
                suffixes = self.rng.sample(params["suffixes"], k)
                stem, ext = src["name"].rsplit(".", 1)
                for i, suf in enumerate(suffixes):
                    name = f"{stem}{suf}.{ext}"
                    # stale final: FINAL older than DRAFT with the given probability
                    delta = -self.rng.randint(5, 120) if ("FINAL" in suf and self.rng.random() < params["stale_final_probability"]) else self.rng.randint(-60, 30)
                    identical = self.rng.random() < params["byte_identical_probability"]
                    self.derive(src, f"{src['folder']}/{name}", "version_sprawl",
                                modified=self.shift_date(src["modified"], delta),
                                modified_by=self.rng.choice([src.get("author_id"), self.other_person(src["site"], src.get("author_id"))]),
                                alter=None if identical else "changed")

    def copies(self) -> None:
        for rule_id, fmt in (("copy_of", "Copy of {stem}.{ext}"), ("numbered_dup", "{stem} ({n}).{ext}")):
            rule = self.by_rule[rule_id]
            for lib_id in self.applies(rule):
                profile = self.lib_profiles[lib_id]
                n = self.rand_count(rule["params"]["per_library"], profile)
                pool = self.files_in(lib_id, exts=("docx", "xlsx", "pptx", "pdf", "txt"))
                if not pool:
                    continue
                for src in self.rng.sample(pool, min(n, len(pool))):
                    stem, ext = src["name"].rsplit(".", 1)
                    name = fmt.format(stem=stem, ext=ext, n=self.rng.choice([1, 1, 2]))
                    changed = rule_id == "numbered_dup" and self.rng.random() < rule["params"].get("changed_probability", 0)
                    self.derive(src, self.unique(f"{src['folder']}/{name}"), rule_id,
                                modified=self.shift_date(src["modified"], self.rng.randint(0, 40)),
                                alter="changed" if changed else None)

    def metadata_drift(self) -> None:
        rule = self.by_rule["metadata_drift"]
        for lib_id in self.applies(rule):
            profile = self.lib_profiles[lib_id]
            p_dis = rule["params"]["disagree_probability"][profile]
            p_nomb = rule["params"]["no_modified_by_probability"][profile]
            for f in self.b.files:
                if f.get("library") != lib_id or f.get("planted"):
                    continue
                if self.rng.random() < p_dis:
                    f["modified_by"] = self.b.cast.short(self.other_person(f["site"], f.get("author_id")))
                if self.rng.random() < p_nomb:
                    f["modified_by"] = ""

    def junk_and_empty(self) -> None:
        rule = self.by_rule["junk_folders"]
        for lib_id in self.applies(rule):
            n = self.rand_count(rule["params"]["per_library"], "chaotic")
            names = self.rng.sample(rule["params"]["names"], min(n, len(rule["params"]["names"])))
            base = self.root / self.lib_folder[lib_id]
            for name in names:
                d = base / name
                d.mkdir(parents=True, exist_ok=True)
                if self.rng.random() >= rule["params"]["empty_probability"]:
                    self.zero_byte_file(d, lib_id)
        rule = self.by_rule["empty_folders"]
        for lib_id in self.applies(rule):
            profile = self.lib_profiles[lib_id]
            n = self.rand_count(rule["params"]["per_library"], profile)
            base = self.root / self.lib_folder[lib_id]
            existing = [p for p in base.rglob("*") if p.is_dir()] or [base]
            for _ in range(n):
                parent = self.rng.choice(existing)
                (parent / self.rng.choice(["New folder", "Old", "temp", "Misc", "Archive"])).mkdir(exist_ok=True)

    def zero_byte_file(self, folder: Path, lib_id: str, name: str | None = None) -> None:
        name = name or self.rng.choice(JUNK_FILES)
        p = folder / name
        if p.exists() or len("stonegrove-hub/" + p.relative_to(self.root).as_posix()) > self.max_path:
            return
        p.write_bytes(b"")
        s = self.site_of_lib[lib_id]
        self.b.register(p, {"title": p.stem, "author": None, "modified": self.rng.choice(["1052-11-09", "1053-01-14", "1052-12-02"]),
                            "label": None, "sensitive": False, "site": s["id"], "library": lib_id,
                            "mess_rule": "zero_byte"}, None)
        self.b.files[-1]["mess_rule"] = "zero_byte"
        self.made += 1

    def zero_byte(self) -> None:
        rule = self.by_rule["zero_byte"]
        for lib_id in self.applies(rule):
            n = self.rand_count(rule["params"]["per_library"], "chaotic")
            base = self.root / self.lib_folder[lib_id]
            dirs = [p for p in base.rglob("*") if p.is_dir() and len(p.relative_to(self.root).as_posix()) < 120] or [base]
            for name in self.rng.sample(rule["params"]["names"], min(n, len(rule["params"]["names"]))):
                self.zero_byte_file(self.rng.choice(dirs), lib_id, name)

    def litter(self) -> None:
        """tmp and lock files. Needs the tilde/dollar exception in the linter."""
        for rule_id in ("tmp_litter", "lock_files"):
            rule = self.by_rule[rule_id]
            for lib_id in self.applies(rule):
                n = self.rand_count(rule["params"]["per_library"], "chaotic")
                pool = [f for f in self.b.files if f.get("library") == lib_id and f["ext"] == "docx"]
                for _ in range(n):
                    if rule_id == "tmp_litter":
                        folder = self.root / (self.rng.choice(pool)["folder"] if pool else self.lib_folder[lib_id])
                        name = f"~WRL{self.rng.randint(0, 9999):04d}.tmp"
                        data = bytes(self.rng.getrandbits(8) for _ in range(self.rng.randint(200, 4000)))
                    else:
                        if not pool:
                            break
                        src = self.rng.choice(pool)
                        folder = self.root / src["folder"]
                        name = f"~${src['name']}"
                        data = b"\x00" * 162
                    p = folder / name
                    if p.exists() or len("stonegrove-hub/" + p.relative_to(self.root).as_posix()) > self.max_path:
                        continue
                    p.write_bytes(data)
                    s = self.site_of_lib[lib_id]
                    self.b.register(p, {"title": name, "author": None, "modified": "1053-04-11", "label": None, "sensitive": False,
                                        "site": s["id"], "library": lib_id, "mess_rule": rule_id}, None)
                    self.b.files[-1]["mess_rule"] = rule_id
                    self.made += 1

    def wrong_site(self) -> None:
        rule = self.by_rule["wrong_site"]
        for item in rule.get("named", []):
            src = next((f for f in self.b.files if f["name"] == item["file"] and f.get("library") == item["from"]), None)
            if not src:
                continue
            name = item.get("rename", item["file"])
            rel = f"{self.lib_folder[item['to']]}/{item['path']}/{name}".replace("//", "/")
            self.derive(src, rel, "wrong_site", label=None, modified=self.shift_date(src["modified"], self.rng.randint(1, 90)),
                        modified_by=self.other_person(self.site_of_lib[item["to"]]["id"], None))
            if self.b.files and self.b.files[-1]["path"] == rel:
                self.b.files[-1]["library"] = item["to"]
                self.b.files[-1]["site"] = self.site_of_lib[item["to"]]["id"]
        for lib_id in self.applies(rule):
            n = self.rand_count(rule["params"]["random_per_library"], "chaotic")
            others = [f for f in self.b.files if f.get("library") and f["library"] != lib_id and f["label"] in ("Internal", "Public")
                      and not f.get("sensitive") and not f.get("derived_from") and f["ext"] in ("docx", "pdf", "pptx")]
            base = self.root / self.lib_folder[lib_id]
            dirs = [p for p in base.rglob("*") if p.is_dir() and len(p.relative_to(self.root).as_posix()) < 110] or [base]
            for src in self.rng.sample(others, min(n, len(others))):
                target = self.rng.choice(dirs).relative_to(self.root).as_posix()
                e = self.derive(src, self.unique(f"{target}/{src['name']}"), "wrong_site", label=None)
                if e:
                    e["library"] = lib_id
                    e["site"] = self.site_of_lib[lib_id]["id"]

    def email_dump(self) -> None:
        rule = self.by_rule["email_dump"]
        pdfs = [f for f in self.b.files if f["ext"] == "pdf" and not f.get("sensitive")]
        docs = [f for f in self.b.files if f.get("library") == "pst-providers" and f["ext"] == "docx"]
        pngs = [f for f in self.b.files if f["ext"] == "png"]
        jpgs = [f for f in self.b.files if f["ext"] == "jpg"]
        for lib_id in self.applies(rule):
            target = self.lib_folder[lib_id] + ("/Faculty Shared/Admin" if lib_id == "fac-stoneshare" else "")
            for name in rule["params"]["generic_names"]:
                ext = name.rsplit(".", 1)[1]
                pool = {"png": pngs, "jpg": jpgs, "pdf": pdfs, "docx": docs}.get(ext)
                if not pool:
                    continue
                src = self.rng.choice(pool)
                e = self.derive(src, self.unique(f"{target}/{name}"), "email_dump", label=None, title=name.rsplit(".", 1)[0],
                                modified=self.rng.choice(["1052-11-09", "1053-02-11", "1052-06-03", "1053-03-20"]))
                if e:
                    e["library"] = lib_id
                    e["site"] = self.site_of_lib[lib_id]["id"]

    def labels(self) -> None:
        rule = self.by_rule["label_inconsistency"]
        for lib_id in self.applies(rule):
            profile = self.lib_profiles[lib_id]
            p = rule["params"]["missing_label_probability"][profile]
            for f in self.b.files:
                if f.get("library") != lib_id or f.get("planted") or f.get("sensitive"):
                    continue
                if lib_id in ("fac-stoneshare", "pst-email-attachments") or self.rng.random() < p:
                    f["label"] = None
        # migrated and saved material: nothing labelled, nothing attributed
        for f in self.b.files:
            if f.get("library") in ("fac-stoneshare", "pst-email-attachments") and not f.get("planted"):
                f["label"] = None

    # ------------------------------------------------------------ run
    def run(self) -> int:
        self.version_sprawl()
        self.copies()
        self.wrong_site()
        self.email_dump()
        self.junk_and_empty()
        self.zero_byte()
        self.litter()
        self.metadata_drift()
        self.labels()
        return self.made


def apply(builder, root: Path, seed: int) -> int:
    m = Mess(builder, root, seed)
    n = m.run()
    print(f"make_mess: {n} derived files")
    return n
