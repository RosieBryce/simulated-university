#!/usr/bin/env python3
"""
One-time migration: add Module Code column to curriculum Excel.

Assigns codes as {programme_code}.{seq:02d} where seq runs sequentially
across all years within a programme (year 1 first, then 2, then 3),
preserving the existing row order in the sheet.

Run once from project root. Safe to re-run — codes are deterministic.
"""

from pathlib import Path
import pandas as pd

CURRICULUM_PATH = Path("Instructions and guides/Stonegrove_University_Curriculum.xlsx")


def main():
    mods = pd.read_excel(CURRICULUM_PATH, sheet_name="Modules")

    if "Module Code" in mods.columns:
        print("Module Code column already exists. Re-generating to ensure consistency.")
        mods = mods.drop(columns=["Module Code"])

    # Sequential code per programme, in existing row order (year 1 → 2 → 3)
    seq = mods.groupby("Programme code", sort=False).cumcount() + 1
    mods["Module Code"] = mods["Programme code"].astype(str) + "." + seq.apply(lambda x: f"{x:02d}")

    col_order = ["Programme code", "Module Code", "Programme", "Year", "Module Title"]
    mods = mods[col_order]

    with pd.ExcelWriter(CURRICULUM_PATH, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
        mods.to_excel(writer, sheet_name="Modules", index=False)

    print(f"Updated: {CURRICULUM_PATH}")
    print(f"  {len(mods)} modules across {mods['Programme code'].nunique()} programmes")
    print()
    print("Sample (first programme):")
    print(mods[mods["Programme code"] == mods["Programme code"].iloc[0]].to_string(index=False))


if __name__ == "__main__":
    main()
