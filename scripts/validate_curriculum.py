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
    else:
        problems.append(f"missing {MODULE_CSV}")
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
