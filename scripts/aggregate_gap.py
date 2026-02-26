#!/usr/bin/env python3
"""Generate docs/data/gap-summary.csv from relational pipeline outputs.

Output: academic_year, elf_good, dwarf_good
Good degree rate (First or 2:1, as %) by species per graduating year.
Run from project root after run_longitudinal_pipeline.py and build_relational_outputs.py.
"""
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

outcomes = pd.read_csv(ROOT / "data/relational/fact_graduate_outcomes.csv")
students  = pd.read_csv(ROOT / "data/relational/dim_students.csv")

df = outcomes.merge(students[["student_id", "species"]], on="student_id")
df["good_degree"] = df["degree_classification"].isin(["First", "2:1"])

gap = (
    df.groupby(["academic_year_graduated", "species"])["good_degree"]
    .mean()
    .mul(100)
    .round(1)
    .unstack()
    .reset_index()
)
gap.columns = ["academic_year", "dwarf_good", "elf_good"]
gap = gap[["academic_year", "elf_good", "dwarf_good"]]

out = ROOT / "docs/data/gap-summary.csv"
gap.to_csv(out, index=False)
print(f"Written: {out}")
print(gap.to_string(index=False))
