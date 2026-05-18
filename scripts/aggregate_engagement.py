#!/usr/bin/env python3
"""Generate docs/data/engagement-summary.csv from relational pipeline outputs.

Output: week, elf_attendance, dwarf_attendance
(mean attendance rate per week number across all years and modules, by species).
Run from project root after run_longitudinal_pipeline.py and build_relational_outputs.py.
"""
import pandas as pd
import glob
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

files = sorted(glob.glob(str(ROOT / "data/relational/fact_weekly_engagement_*.csv")))
if not files:
    raise FileNotFoundError("No fact_weekly_engagement_*.csv files found in data/relational/")

df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
students = pd.read_csv(ROOT / "data/relational/dim_students.csv")
df = df.merge(students[["student_id", "species"]], on="student_id")

df["attendance_rate"] = df["attended_sessions"] / df["total_sessions"].replace(0, pd.NA)

eng = (
    df.groupby(["week_number", "species"])[["attendance_rate"]]
    .mean()
    .unstack()
)
eng.columns = ["_".join(col).lower() for col in eng.columns]
eng = eng.round(3).reset_index()
eng.columns = ["week", "dwarf_attendance", "elf_attendance"]
eng = eng[["week", "elf_attendance", "dwarf_attendance"]]

out = ROOT / "docs/data/engagement-summary.csv"
eng.to_csv(out, index=False)
print(f"Written: {out}")
print(eng.to_string(index=False))
