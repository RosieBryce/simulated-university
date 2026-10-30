#!/usr/bin/env python3
"""Validate the canonical curriculum before a pipeline run.

Checks `curriculum-and-lore/Stonegrove_University_Curriculum_v7.xlsx` (Modules sheet)
and `config/module_characteristics.csv` for the failure that stranded two thirds of
students in the v2.6.0 dataset: a module whose `Programme code` does not match the
programme named on the same row, so the enrolment system cannot find it.

Every programme must have at least one module in each of Years 1, 2 and 3, otherwise
students reaching that year are enrolled with no modules, get no assessment or
progression rows, and silently disappear from the simulation.

Exit code 0 = clean, 1 = problems found. Run from the project root:

    python scripts/validate_curriculum.py
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
XLSX = ROOT / "curriculum-and-lore" / "Stonegrove_University_Curriculum_v7.xlsx"
MODULE_CSV = ROOT / "config" / "module_characteristics.csv"
YEARS = (1, 2, 3)


def validate() -> list[str]:
    problems: list[str] = []
    programmes = pd.read_excel(XLSX, sheet_name="Programmes")
    modules = pd.read_excel(XLSX, sheet_name="Modules")
    name_to_code = dict(zip(programmes["Programme"], programmes["Programme code"]))
    valid_codes = set(programmes["Programme code"])

    # 1. Modules sheet: programme code must exist and must match the programme name.
    unknown = modules[~modules["Programme code"].isin(valid_codes)]
    if len(unknown):
        problems.append(
            f"Modules sheet: {len(unknown)} rows carry a Programme code that is not in the "
            f"Programmes sheet (e.g. {sorted(unknown['Programme code'].unique())[:5]})"
        )
    expected = modules["Programme"].map(name_to_code)
    mismatch = modules[expected != modules["Programme code"]]
    if len(mismatch):
        problems.append(
            f"Modules sheet: {len(mismatch)} of {len(modules)} rows have a Programme code that "
            f"does not match the programme named on the row"
        )

    # 2. Every programme has modules in every year (the enrolment system keys on code + Year).
    counts = (
        modules.groupby(["Programme code", "Year"]).size().unstack(fill_value=0)
        .reindex(index=programmes["Programme code"], columns=YEARS, fill_value=0)
    )
    code_to_name = dict(zip(programmes["Programme code"], programmes["Programme"]))
    empty = counts[(counts == 0).any(axis=1)]
    for code, row in empty.iterrows():
        missing = [y for y in YEARS if row[y] == 0]
        problems.append(f"{code} ({code_to_name[code]}): no modules in Year {missing}")

    # 3. config/module_characteristics.csv must agree with the spreadsheet.
    if MODULE_CSV.exists():
        mc = pd.read_csv(MODULE_CSV)
        csv_expected = mc["programme_name"].map(name_to_code)
        bad = mc[csv_expected != mc["programme_code"]]
        if len(bad):
            problems.append(
                f"config/module_characteristics.csv: {len(bad)} of {len(mc)} rows have a "
                f"programme_code that does not match programme_name"
            )
        if mc["programme_name"].map(name_to_code).isna().any():
            problems.append("config/module_characteristics.csv: programme_name not in Programmes sheet")
        sheet_codes = set(modules["Module Code"].astype(str))
        csv_codes = set(mc["module_code"].astype(str))
        if sheet_codes != csv_codes:
            problems.append(
                f"config/module_characteristics.csv: module codes differ from the Modules sheet "
                f"({len(sheet_codes - csv_codes)} only in sheet, {len(csv_codes - sheet_codes)} only in CSV)"
            )
    else:
        problems.append(f"missing {MODULE_CSV}")

    problems += check_module_codes(modules)
    problems += check_programme_references(programmes)
    return problems


def check_module_codes(modules: pd.DataFrame) -> list[str]:
    """Module Code integrity: the second half of the autofill failure, plus collisions.

    A Module Code is <level digit><programme code digits><2-digit sequence>, e.g. 641204 is
    level 6, programme 4_1_2, module 04; 6351204 is level 6, programme 3_5_12, module 04.
    A module shared between programmes keeps its home programme's code, so a code that
    disagrees with its own row is only legitimate when the home programme carries the same
    code with the same title and year.
    """
    problems: list[str] = []
    level_digit = {1: "4", 2: "5", 3: "6"}
    code = modules["Module Code"].astype(str)
    home = modules["Year"].map(level_digit) + modules["Programme code"].str.replace("_", "") + code.str[-2:]
    off_home = modules[code != home]

    # Level and Year must agree (Level 4/5/6 = Year 1/2/3).
    bad_level = modules[modules["Level"] != modules["Year"] + 3]
    if len(bad_level):
        problems.append(f"Modules sheet: {len(bad_level)} rows where Level is not Year + 3")

    # A shared code must have a home row, and every row sharing it must agree on title and year.
    for mod_code, grp in modules.groupby(code):
        if len(grp) < 2:
            continue
        if grp["Module Title"].nunique() > 1 or grp["Year"].nunique() > 1:
            problems.append(
                f"Module Code {mod_code} is used by different modules/years: "
                f"{sorted(set(zip(grp['Programme code'], grp['Module Title'], grp['Year'])))[:3]}"
            )
    home_codes = set(code[code == home])
    orphans = off_home[~off_home["Module Code"].astype(str).isin(home_codes)]
    if len(orphans):
        problems.append(
            f"Modules sheet: {len(orphans)} rows have a Module Code that does not match their "
            f"Programme code and is not a shared module (e.g. {orphans['Module Code'].head(3).tolist()})"
        )

    # AssessmentSystem resolves module codes by (Programme code, Year, Module Title), so that
    # triple must be unique or two modules collapse onto one code. (A programme may reuse a
    # title in different years, e.g. Brewcraft's Quality Control & Sensory Analysis; the year
    # in the key keeps those apart.)
    dup = modules[modules.duplicated(["Programme code", "Year", "Module Title"], keep=False)]
    for (prog, year, title), grp in dup.groupby(["Programme code", "Year", "Module Title"]):
        problems.append(
            f"{prog}: module title '{title}' appears {len(grp)} times in Year {year}; "
            f"the (programme, year, title) code lookup cannot tell them apart"
        )

    # Every programme should carry the same number of modules per year.
    per_year = modules.groupby(["Programme code", "Year"]).size()
    modal = per_year.mode().iloc[0]
    odd = per_year[per_year != modal]
    if len(odd):
        problems.append(
            f"{len(odd)} programme-years do not have the usual {modal} modules "
            f"(e.g. {[f'{p} Y{y}={n}' for (p, y), n in odd.head(3).items()]})"
        )
    return problems


def check_programme_references(programmes: pd.DataFrame) -> list[str]:
    """Other config keyed on programme code must name real programmes, and cover all of them."""
    problems: list[str] = []
    valid = set(programmes["Programme code"])

    pc_path = ROOT / "config" / "programme_characteristics.csv"
    if pc_path.exists():
        pc = pd.read_csv(pc_path)
        name_to_code = dict(zip(programmes["Programme"], programmes["Programme code"]))
        wrong = pc[pc["programme_name"].map(name_to_code) != pc["programme_code"]]
        if len(wrong):
            problems.append(f"config/programme_characteristics.csv: {len(wrong)} rows whose programme_code does not match programme_name")
        if set(pc["programme_code"]) != valid:
            problems.append("config/programme_characteristics.csv: programme codes differ from the Programmes sheet")

    aff_path = ROOT / "config" / "clan_program_affinities.yaml"
    if aff_path.exists():
        import yaml
        clans = yaml.safe_load(aff_path.read_text(encoding="utf-8"))["clans"]
        for clan, spec in clans.items():
            keys = set(spec["program_affinities"])
            if keys - valid:
                problems.append(f"clan_program_affinities.yaml [{clan}]: unknown programme codes {sorted(keys - valid)[:3]}")
            if valid - keys:
                problems.append(f"clan_program_affinities.yaml [{clan}]: {len(valid - keys)} programmes have no affinity "
                                f"and may never be chosen (e.g. {sorted(valid - keys)[:3]})")
    return problems


def main() -> int:
    problems = validate()
    if problems:
        print(f"Curriculum validation FAILED ({len(problems)} problems):")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("Curriculum validation passed: every programme has modules in Years 1-3 and all codes match.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
