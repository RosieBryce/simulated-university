#!/usr/bin/env python3
"""
Filename and path linter for the Stonegrove Hub estate.

Reads hub/bible/filename_rules.yaml and checks either a directory tree or a
manifest.json. Exits non-zero on any violation so build_estate.py can fail.

Usage:
    python hub/build/lint_filenames.py --tree hub/output/estate
    python hub/build/lint_filenames.py --manifest docs/hub/data/manifest.json
    python hub/build/lint_filenames.py --names "Some name.docx" "Another folder"
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

HUB_ROOT = Path(__file__).resolve().parent.parent
RULES_PATH = HUB_ROOT / "bible" / "filename_rules.yaml"


class Rules:
    def __init__(self, path: Path = RULES_PATH, allow_tilde_dollar_prefix: bool = False):
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        self.regex = re.compile(raw["allowed_characters"]["regex"])
        self.max_name = raw["structure"]["max_name_length"]
        self.max_path = raw["structure"]["max_path_length_in_zip"]
        self.allowed_ext = set(raw["extensions"]["allowed"])
        self.reserved = {r.lower() for r in raw["reserved_names"]["windows"]}
        self.zip_root = raw["zip"]["root_folder"]
        self.allow_tilde_dollar_prefix = allow_tilde_dollar_prefix

    # ------------------------------------------------------------------
    def check_segment(self, name: str, is_file: bool) -> list[str]:
        """Return a list of problems with one path segment (file or folder name)."""
        problems: list[str] = []
        candidate = name
        if self.allow_tilde_dollar_prefix and (name.startswith("~$") or name.startswith("~")):
            candidate = name.lstrip("~$")
        if not name.isascii():
            problems.append("non-ascii")
        if not self.regex.match(candidate):
            problems.append("disallowed character")
        if name != name.strip():
            problems.append("leading or trailing space")
        if name.startswith(".") or name.endswith("."):
            problems.append("leading or trailing dot")
        if ".." in name:
            problems.append("consecutive dots")
        if "  " in name:
            problems.append("consecutive spaces")
        if len(name) > self.max_name:
            problems.append(f"name longer than {self.max_name}")
        if is_file:
            if "." not in name:
                problems.append("file has no extension")
            else:
                stem, ext = name.rsplit(".", 1)
                if ext != ext.lower():
                    problems.append("extension not lower case")
                if ext.lower() not in self.allowed_ext:
                    problems.append(f"extension .{ext} not allowed")
                if stem.lower() in self.reserved:
                    problems.append("windows reserved name")
        else:
            if name.lower() in self.reserved:
                problems.append("windows reserved name")
        return problems

    def check_path(self, rel_path: str, is_file: bool) -> list[tuple[str, str]]:
        """Check every segment of a relative path plus total length under the zip root."""
        out: list[tuple[str, str]] = []
        segments = [s for s in rel_path.replace("\\", "/").split("/") if s]
        for i, seg in enumerate(segments):
            last = i == len(segments) - 1
            for p in self.check_segment(seg, is_file and last):
                out.append((rel_path, f"'{seg}': {p}"))
        full = f"{self.zip_root}/{'/'.join(segments)}"
        if len(full) > self.max_path:
            out.append((rel_path, f"zip path {len(full)} chars, limit {self.max_path}"))
        return out

    def check_case_collisions(self, paths: list[str]) -> list[tuple[str, str]]:
        seen: dict[str, str] = {}
        out: list[tuple[str, str]] = []
        for p in paths:
            key = p.replace("\\", "/").lower()
            if key in seen and seen[key] != p:
                out.append((p, f"differs only by case from '{seen[key]}'"))
            seen.setdefault(key, p)
        return out


# ----------------------------------------------------------------------
def lint_tree(root: Path, rules: Rules) -> list[tuple[str, str]]:
    problems: list[tuple[str, str]] = []
    all_paths: list[str] = []
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix()
        all_paths.append(rel)
        problems.extend(rules.check_path(rel, path.is_file()))
    problems.extend(rules.check_case_collisions(all_paths))
    return problems


def lint_manifest(manifest_path: Path, rules: Rules) -> list[tuple[str, str]]:
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    problems: list[tuple[str, str]] = []
    paths: list[str] = []
    for item in data.get("files", []):
        rel = item["path"]
        paths.append(rel)
        problems.extend(rules.check_path(rel, True))
    for folder in data.get("folders", []):
        rel = folder["path"]
        paths.append(rel)
        problems.extend(rules.check_path(rel, False))
    problems.extend(rules.check_case_collisions(paths))
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tree", type=Path, help="directory to lint recursively")
    ap.add_argument("--manifest", type=Path, help="manifest.json to lint")
    ap.add_argument("--names", nargs="*", help="individual names to check (files if they have an extension)")
    ap.add_argument("--allow-tilde-dollar-prefix", action="store_true",
                    help="permit the ~$ lock-file prefix (only after phase 1 proves it round-trips)")
    args = ap.parse_args()

    rules = Rules(allow_tilde_dollar_prefix=args.allow_tilde_dollar_prefix)
    problems: list[tuple[str, str]] = []
    if args.tree:
        problems.extend(lint_tree(args.tree, rules))
    if args.manifest:
        problems.extend(lint_manifest(args.manifest, rules))
    if args.names:
        for n in args.names:
            problems.extend(rules.check_path(n, "." in n.rsplit("/", 1)[-1]))

    if problems:
        print(f"lint_filenames: {len(problems)} problem(s)")
        for where, what in problems:
            print(f"  {where}\n      {what}")
        return 1
    print("lint_filenames: clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
