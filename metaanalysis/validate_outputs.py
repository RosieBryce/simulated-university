"""
Stonegrove University — Output Validation Report

Reads from data/relational/ and checks:
  1. Shape and completeness
  2. Progression rates (pass/fail/withdraw/graduate) by year level
  3. Mark distributions overall and by year level
  4. Awarding gaps: species, clan, SES, gender
  5. Engagement–mark correlation
  6. Module difficulty–mark correlation

Run from project root: py metaanalysis/validate_outputs.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np

RELATIONAL = Path("data/relational")

# Expected ranges for flagging
TARGETS = {
    "progression_pass_rate":    (0.70, 0.92),
    "withdrawal_rate":          (0.03, 0.18),
    "overall_mean_mark":        (52.0, 68.0),
    "overall_std_mark":         (10.0, 22.0),
    "elf_dwarf_gap_pp":         (3.0, 18.0),   # Elf > Dwarf, percentage points
    "ses_gap_pp":               (5.0, 25.0),   # rank 8 vs rank 1
    "engagement_mark_corr":     (0.05, 0.60),  # weak-to-moderate positive
    "difficulty_mark_corr":     (-0.60, -0.02), # negative (harder = lower marks)
}


def flag(value, lo, hi, label=""):
    ok = lo <= value <= hi
    symbol = "  OK " if ok else " WARN"
    return f"{symbol}  {label}: {value:.3f}  (expected {lo}–{hi})"


def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def load():
    tables = {}
    for name in ["dim_students", "dim_modules", "dim_programmes", "dim_academic_years",
                 "fact_enrollment", "fact_weekly_engagement", "fact_assessment", "fact_progression"]:
        path = RELATIONAL / f"{name}.csv"
        if not path.exists():
            print(f"MISSING: {path}")
            sys.exit(1)
        tables[name] = pd.read_csv(path)
    return tables


# ---------------------------------------------------------------------------

def check_shapes(t):
    section("1. SHAPE AND COMPLETENESS")
    expected = {
        "dim_academic_years":     (7,   "7 academic years"),
        "dim_students":           (3500, "7 cohorts × 500 students"),
        "dim_programmes":         (44,  "44 programmes"),
        "dim_modules":            (353, "353 curriculum modules"),
    }
    for name, (exp, note) in expected.items():
        n = len(t[name])
        ok = "  OK " if n == exp else " WARN"
        print(f"{ok}  {name}: {n} rows  ({note})")

    # Null checks on key fact columns
    print()
    checks = [
        ("fact_enrollment",        "student_id"),
        ("fact_enrollment",        "programme_code"),
        ("fact_assessment",        "assessment_mark"),
        ("fact_assessment",        "module_code"),
        ("fact_weekly_engagement", "module_code"),
        ("fact_progression",       "year_outcome"),
    ]
    for tbl, col in checks:
        n_null = t[tbl][col].isna().sum()
        ok = "  OK " if n_null == 0 else " WARN"
        print(f"{ok}  {tbl}.{col}: {n_null} nulls")


# ---------------------------------------------------------------------------

def check_progression(t):
    section("2. PROGRESSION RATES")
    prog = t["fact_progression"]
    enr  = t["fact_enrollment"]

    # Join programme_year onto progression via enrollment
    py = enr[["student_id", "academic_year", "programme_year"]].drop_duplicates()
    prog = prog.merge(py, on=["student_id", "academic_year"], how="left")

    total = len(prog)
    print(f"  Total progression records: {total}")
    print()

    # Year outcome (academic result): pass / fail
    outcomes = prog["year_outcome"].value_counts()
    print("  Academic outcome (year_outcome):")
    for outcome, n in outcomes.items():
        print(f"    {outcome:<15} {n:>6}  ({n/total*100:.1f}%)")

    lo, hi = TARGETS["progression_pass_rate"]
    pass_rate = outcomes.get("pass", 0) / total
    print(f"\n{flag(pass_rate, lo, hi, 'pass rate')}")

    # Status (next-year action): enrolled / repeating / graduated / withdrawn
    print()
    statuses = prog["status"].value_counts()
    print("  Next-year status (status):")
    for s, n in statuses.items():
        print(f"    {s:<15} {n:>6}  ({n/total*100:.1f}%)")

    grad_rate = statuses.get("graduated", 0) / total
    print(f"\n  {'  OK ' if grad_rate > 0 else ' WARN'}  graduate rate: {grad_rate:.3f}")

    withdraw_rate = statuses.get("withdrawn", 0) / total
    lo, hi = TARGETS["withdrawal_rate"]
    print(flag(withdraw_rate, lo, hi, "withdrawal rate"))

    print()
    print("  By programme_year:")
    for yr in sorted(prog["programme_year"].dropna().unique()):
        sub = prog[prog["programme_year"] == yr]
        vc  = sub["year_outcome"].value_counts(normalize=True)
        parts = "  ".join(f"{k}: {v:.0%}" for k, v in vc.items())
        print(f"    Year {int(yr)}: {len(sub)} records — {parts}")


# ---------------------------------------------------------------------------

def check_marks(t):
    section("3. MARK DISTRIBUTIONS")
    assess = t["fact_assessment"]
    marks  = assess["assessment_mark"].dropna()

    mean, std = marks.mean(), marks.std()
    lo, hi = TARGETS["overall_mean_mark"]
    print(flag(mean, lo, hi, "overall mean mark"))
    lo, hi = TARGETS["overall_std_mark"]
    print(flag(std,  lo, hi, "overall std mark"))

    print()
    print("  Grade band breakdown:")
    grades = assess["grade"].value_counts()
    total  = len(assess)
    for g in ["First", "2:1", "2:2", "Third", "Fail"]:
        n = grades.get(g, 0)
        print(f"    {g:<8}  {n:>6}  ({n/total*100:.1f}%)")

    # By module_year
    mod_year = t["dim_modules"][["module_code", "module_year"]]
    assess_y = assess.merge(mod_year, on="module_code", how="left")
    print()
    print("  Mean mark by module year:")
    for yr in sorted(assess_y["module_year"].dropna().unique()):
        sub = assess_y[assess_y["module_year"] == yr]["assessment_mark"]
        print(f"    Year {int(yr)}: mean {sub.mean():.1f}  std {sub.std():.1f}  (n={len(sub)})")


# ---------------------------------------------------------------------------

def check_awarding_gaps(t):
    section("4. AWARDING GAPS")
    assess  = t["fact_assessment"]
    students = t["dim_students"][["student_id", "species", "clan", "socio_economic_rank", "gender"]]
    df = assess.merge(students, on="student_id", how="left")

    # Species
    print("  Mean mark by species:")
    sp = df.groupby("species")["assessment_mark"].agg(["mean","count"]).sort_values("mean", ascending=False)
    for species, row in sp.iterrows():
        print(f"    {species:<10}  {row['mean']:.1f}  (n={int(row['count'])})")

    elf_mean   = sp.loc["Elf",   "mean"] if "Elf"   in sp.index else None
    dwarf_mean = sp.loc["Dwarf", "mean"] if "Dwarf" in sp.index else None
    if elf_mean and dwarf_mean:
        gap = elf_mean - dwarf_mean
        lo, hi = TARGETS["elf_dwarf_gap_pp"]
        print(f"\n{flag(gap, lo, hi, 'Elf–Dwarf gap (pp)')}")

    # SES
    print()
    print("  Mean mark by SES rank:")
    ses = df.groupby("socio_economic_rank")["assessment_mark"].mean().sort_index()
    for rank, mean in ses.items():
        print(f"    SES {int(rank)}: {mean:.1f}")
    if len(ses) >= 2:
        ses_gap = ses.max() - ses.min()
        lo, hi = TARGETS["ses_gap_pp"]
        print(f"\n{flag(ses_gap, lo, hi, 'SES gap rank 8 vs rank 1 (pp)')}")

    # Gender
    print()
    print("  Mean mark by gender:")
    gen = df.groupby("gender")["assessment_mark"].agg(["mean","count"]).sort_values("mean", ascending=False)
    for gender, row in gen.iterrows():
        print(f"    {gender:<15}  {row['mean']:.1f}  (n={int(row['count'])})")

    # Top 5 clans by gap from overall mean
    print()
    overall = df["assessment_mark"].mean()
    clan = df.groupby("clan")["assessment_mark"].mean().sort_values(ascending=False)
    print(f"  Mean mark by clan (overall mean: {overall:.1f}):")
    for c, m in clan.items():
        diff = m - overall
        marker = " ^" if diff > 1.5 else (" v" if diff < -1.5 else "  ")
        print(f"    {c:<20}  {m:.1f}  ({diff:+.1f}){marker}")


# ---------------------------------------------------------------------------

def check_correlations(t):
    section("5. ENGAGEMENT AND DIFFICULTY CORRELATIONS")

    # Engagement -> mark
    eng   = t["fact_weekly_engagement"]
    assess = t["fact_assessment"]

    eng_avg = (
        eng.groupby(["student_id", "academic_year", "module_code"])
        [["attendance_rate", "participation_score", "academic_engagement"]]
        .mean()
        .mean(axis=1)
        .reset_index(name="avg_engagement")
    )
    merged = assess.merge(eng_avg, on=["student_id", "academic_year", "module_code"], how="inner")
    if len(merged) > 100:
        corr = merged["avg_engagement"].corr(merged["assessment_mark"])
        lo, hi = TARGETS["engagement_mark_corr"]
        print(flag(corr, lo, hi, "engagement -> mark correlation (Pearson r)"))
        print(f"  Matched rows: {len(merged)}")
    else:
        print("  WARN  Not enough matched engagement–mark rows to compute correlation")

    # Difficulty -> mark
    print()
    mods = t["dim_modules"][["module_code", "difficulty_level"]].dropna()
    assess_d = assess.merge(mods, on="module_code", how="inner")
    if len(assess_d) > 100:
        corr_d = assess_d["difficulty_level"].corr(assess_d["assessment_mark"])
        lo, hi = TARGETS["difficulty_mark_corr"]
        print(flag(corr_d, lo, hi, "difficulty -> mark correlation (Pearson r)"))
        print(f"  Matched rows: {len(assess_d)}")
    else:
        print("  WARN  Not enough matched difficulty–mark rows")


# ---------------------------------------------------------------------------

def main():
    print("\nStonegrove University — Output Validation Report")
    print(f"Reading from: {RELATIONAL.resolve()}")

    t = load()
    check_shapes(t)
    check_progression(t)
    check_marks(t)
    check_awarding_gaps(t)
    check_correlations(t)

    print(f"\n{'='*60}")
    print("  END OF REPORT")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
