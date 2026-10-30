"""
Stonegrove University — Output Validation Report

Reads from data/relational/ (and config/ for module difficulty) and checks:
  0. Integrity: every student accounted for, every programme covered (exits 1 on failure)
  1. Shape and completeness
  2. Progression rates (pass/fail/withdraw/graduate) by year level
  3. Mark distributions overall and by year level
  4. Awarding gaps: species, clan, SES, gender
  5. Observable correlations against the published schema:
       - attendance (attended/total sessions) → mark
       - module difficulty (from config) → mark

Run from project root: py metaanalysis/validate_outputs.py [path/to/relational]
Exit code 1 if any section-0 integrity check fails; range checks only warn.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np

RELATIONAL = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/relational")
CONFIG = Path("config")

# Expected ranges for flagging
TARGETS = {
    "progression_pass_rate":        (0.88, 0.97),   # year pass rate, overall and per programme year (own calibration: the UK publishes no year-fail rate)
    "year3_fail_vs_year1_ratio":    (0.0, 1.25),    # final year should not fail much more than the first
    "withdrawal_rate":              (0.03, 0.18),
    "year1_noncontinuation":        (0.04, 0.08),   # entrants who withdraw after year 1; HESA UK full-time first degree ~5-6%
    "cohort_completion":            (0.75, 0.95),   # entrants who graduate, cohorts with 4+ years observed; OfS B3 completion threshold 75%
    "overall_mean_mark":            (52.0, 68.0),
    "overall_std_mark":             (10.0, 22.0),
    "elf_dwarf_mark_gap_pp":        (3.0, 18.0),    # Elf > Dwarf, mean module mark
    "elf_dwarf_good_degree_gap_pp": (15.0, 27.0),   # Elf > Dwarf, % getting First/2:1; settled at ~23pp after condonement (UK ethnicity gap ~18-20pp)
    "ses_gap_pp":                   (5.0, 25.0),    # rank 8 vs rank 1
    "engagement_mark_corr":         (0.05, 0.60),   # weak-to-moderate positive
    "difficulty_mark_corr":         (-0.60, -0.02), # negative (harder = lower marks)
}


def flag(value, lo, hi, label=""):
    ok = lo <= value <= hi
    symbol = "  OK " if ok else " WARN"
    return f"{symbol}  {label}: {value:.3f}  (expected {lo}–{hi})"


def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


FAILURES: list[str] = []


def check(ok, label, detail=""):
    """Hard integrity check: prints FAIL (and fails the run) rather than a soft WARN."""
    print(f"{'  OK ' if ok else ' FAIL'}  {label}" + (f"  -> {detail}" if detail and not ok else ""))
    if not ok:
        FAILURES.append(label)
    return ok


def expected_module_count():
    """Distinct module codes in the curriculum config (what dim_modules should contain)."""
    mc_path = CONFIG / "module_characteristics.csv"
    return pd.read_csv(mc_path)["module_code"].nunique() if mc_path.exists() else None


def load():
    tables = {}
    for name in ["dim_students", "dim_modules", "dim_programmes", "dim_academic_years",
                 "fact_enrollment", "fact_assessment", "fact_progression"]:
        path = RELATIONAL / f"{name}.csv"
        if not path.exists():
            print(f"MISSING: {path}")
            sys.exit(1)
        tables[name] = pd.read_csv(path)

    # Graduate outcomes (optional — skip section if absent)
    honours_path = RELATIONAL / "fact_good_honours.csv"
    tables["fact_graduate_outcomes"] = pd.read_csv(honours_path) if honours_path.exists() else None

    nss_path = RELATIONAL / "fact_nss_responses.csv"
    tables["fact_nss_responses"] = pd.read_csv(nss_path) if nss_path.exists() else None

    # Weekly engagement stored per academic year — load first available year for correlation checks
    eng_files = sorted(RELATIONAL.glob("fact_weekly_engagement_*.csv"))
    if eng_files:
        tables["fact_weekly_engagement"] = pd.read_csv(eng_files[0])
        tables["_engagement_years_found"] = len(eng_files)
    else:
        print("MISSING: fact_weekly_engagement_*.csv (no per-year files found)")
        sys.exit(1)
    return tables


# ---------------------------------------------------------------------------

def check_integrity(t):
    """Hard checks that every student is accounted for and every programme is covered.

    These catch the failure behind the v2.6.0 dataset: a mis-coded curriculum left 34 of 55
    programmes with no Year 2/3 modules, so students reaching those years got no assessment or
    progression rows and silently vanished, and only 21 programmes ever produced a graduate.
    Unlike the range checks below, a failure here means the data is wrong, not just
    mis-calibrated, and makes the script exit non-zero.
    """
    section("0. INTEGRITY (students accounted for, programmes covered)")
    enr, prog, assess = t["fact_enrollment"], t["fact_progression"], t["fact_assessment"]
    years = sorted(t["dim_academic_years"]["academic_year"])
    final_year, next_year = years[-1], dict(zip(years, years[1:]))
    key = ["student_id", "academic_year"]

    def n_missing(left, right):
        m = left[key].drop_duplicates().merge(right[key].drop_duplicates(), how="left", on=key, indicator=True)
        return int((m["_merge"] == "left_only").sum())

    # --- Student lifecycle ---------------------------------------------------
    print("  Student lifecycle:")
    n_enr = len(enr[key].drop_duplicates())
    no_students = len(set(t["dim_students"]["student_id"]) - set(enr["student_id"]))
    check(no_students == 0, "every student in dim_students has an enrolment", f"{no_students} students never enrolled")

    n = n_missing(enr, prog)
    check(n == 0, "every enrolment-year has a progression row", f"{n:,} of {n_enr:,} enrolment-years have none")
    n = n_missing(enr, assess)
    check(n == 0, "every enrolment-year has assessment rows", f"{n:,} of {n_enr:,} have none (student enrolled with no modules)")

    eng_missing = 0
    sat = set(map(tuple, enr[key].drop_duplicates().itertuples(index=False)))
    for f in sorted(RELATIONAL.glob("fact_weekly_engagement_*.csv")):
        e = pd.read_csv(f, usecols=key).drop_duplicates()
        yr = e["academic_year"].iloc[0] if len(e) else None
        want = {k for k in sat if k[1] == yr}
        eng_missing += len(want - set(map(tuple, e.itertuples(index=False))))
    check(eng_missing == 0, "every enrolment-year has weekly engagement rows", f"{eng_missing:,} enrolment-years have none")

    # A student carried forward must actually be enrolled the next year; this is the
    # 'last row is status enrolled, nothing afterwards' signature of a silently dropped student.
    cont = prog[prog["status"].isin(["enrolled", "repeating"]) & (prog["academic_year"] != final_year)].copy()
    cont["academic_year"] = cont["academic_year"].map(next_year)
    n = n_missing(cont, enr)
    check(n == 0, "students progressing to the next year are enrolled in it", f"{n:,} of {len(cont):,} carried forward then vanished")

    # --- Programme coverage --------------------------------------------------
    print("\n  Programme coverage:")
    progs = set(t["dim_programmes"]["programme_code"])
    by_year = enr.groupby(["programme_code", "programme_year"]).size().unstack(fill_value=0).reindex(index=sorted(progs), columns=[1, 2, 3], fill_value=0)
    for yr in (1, 2, 3):
        empty = by_year.index[by_year[yr] == 0].tolist()
        check(not empty, f"every programme has Year {yr} enrolments", f"{len(empty)} without, e.g. {empty[:4]}")

    grads = t.get("fact_graduate_outcomes")
    if grads is not None:
        entrants = enr[enr["programme_year"] == 1].groupby("programme_code")["student_id"].nunique().reindex(sorted(progs), fill_value=0)
        graduates = grads.groupby("programme_code")["student_id"].nunique().reindex(sorted(progs), fill_value=0)
        none = graduates.index[graduates == 0].tolist()
        check(not none, "every programme has graduates", f"{len(none)} of {len(progs)} have none, e.g. {none[:4]}")
        rate = (graduates / entrants.where(entrants > 0)).dropna()
        low = rate.index[rate < 0.5 * rate.median()].tolist()
        check(not low, "no programme's graduate rate is under half the median",
              f"median {rate.median():.0%}; low: {[f'{p} {rate[p]:.0%}' for p in low[:4]]}")

        stat = set(prog.loc[prog["status"] == "graduated", "student_id"])
        diff = stat ^ set(grads["student_id"])
        check(not diff, "graduated progression rows match fact_good_honours", f"{len(diff):,} students differ")

    # --- Modules ---------------------------------------------------------------
    print("\n  Modules:")
    mc_path = CONFIG / "module_characteristics.csv"
    if mc_path.exists():
        mc = pd.read_csv(mc_path)
        cfg_codes = set(mc["module_code"].astype(str))
        dim_codes = set(t["dim_modules"]["module_code"].astype(str))
        assessed = set(assess["module_code"].astype(str))
        missing = sorted(cfg_codes - dim_codes)
        check(not missing, "every curriculum module is in dim_modules", f"{len(missing)} missing, e.g. {missing[:4]}")
        stray = sorted(assessed - cfg_codes)
        check(not stray, "every assessed module is in the curriculum", f"{len(stray)} unknown, e.g. {stray[:4]}")
        check(len(t["dim_modules"]) == t["dim_modules"]["module_code"].nunique(), "dim_modules.module_code is unique")

        # modules_total on progression should equal the curriculum's modules for that programme-year
        want = mc.groupby(["programme_code", "year"]).size().rename("expected").reset_index()
        pm = prog.merge(enr[key + ["programme_code", "programme_year"]].drop_duplicates(), on=key, how="left")
        pm = pm.merge(want, left_on=["programme_code", "programme_year"], right_on=["programme_code", "year"], how="left")
        wrong = pm[pm["modules_total"] != pm["expected"]]
        check(wrong.empty, "progression modules_total matches the curriculum",
              f"{len(wrong):,} of {len(pm):,} student-years differ (e.g. programmes {wrong['programme_code'].value_counts().head(3).to_dict()})")
    else:
        print("  WARN  config/module_characteristics.csv not found — module checks skipped")

    # --- NSS -------------------------------------------------------------------
    nss = t.get("fact_nss_responses")
    if nss is not None:
        n = n_missing(nss, assess)
        check(n == 0, "every NSS row belongs to a student with marks that year", f"{n:,} of {len(nss):,} NSS rows have no assessment")


# ---------------------------------------------------------------------------

def check_shapes(t):
    section("1. SHAPE AND COMPLETENESS")
    eng_years = t.get("_engagement_years_found", 0)
    n_modules = expected_module_count()
    expected = {
        "dim_academic_years":     (7,   "7 academic years"),
        "dim_students":           (35000, "7 cohorts × 5000 students"),
        "dim_programmes":         (55,  "55 programmes"),
        "dim_modules":            (n_modules, f"{n_modules} distinct module codes in config/module_characteristics.csv"),
    }
    print(f"  OK   fact_weekly_engagement_*.csv: {eng_years} per-year files found")
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
        ("fact_weekly_engagement", "module_code"),   # first year only
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
    fail_by_year = {}
    for yr in sorted(prog["programme_year"].dropna().unique()):
        sub = prog[prog["programme_year"] == yr]
        vc  = sub["year_outcome"].value_counts(normalize=True)
        parts = "  ".join(f"{k}: {v:.0%}" for k, v in vc.items())
        print(f"    Year {int(yr)}: {len(sub)} records — {parts}")
        fail_by_year[int(yr)] = 1 - vc.get("pass", 0)
    print()
    lo, hi = TARGETS["progression_pass_rate"]
    for yr, fr in fail_by_year.items():
        print(flag(1 - fr, lo, hi, f"Year {yr} pass rate"))
    if 1 in fail_by_year and 3 in fail_by_year and fail_by_year[1] > 0:
        lo, hi = TARGETS["year3_fail_vs_year1_ratio"]
        print(flag(fail_by_year[3] / fail_by_year[1], lo, hi, "Year 3 fail rate / Year 1 fail rate"))

    # UK-benchmarked cohort outcomes. The UK publishes non-continuation and completion,
    # not year-fail rates, so these are the checks that tie the progression model to real data.
    print()
    print("  Cohort outcomes (UK benchmarks):")
    prog = prog.sort_values(["student_id", "academic_year"])
    entry = prog.groupby("student_id")["academic_year"].transform("min")
    first_year = prog[prog["academic_year"] == entry]
    lo, hi = TARGETS["year1_noncontinuation"]
    print(flag((first_year["status"] == "withdrawn").mean(), lo, hi, "year 1 non-continuation"))

    years = sorted(prog["academic_year"].unique())
    mature = set(years[:max(len(years) - 3, 0)])   # cohorts with at least 4 years observed
    last = prog.groupby("student_id").tail(1)
    last = last[entry.loc[last.index].isin(mature)]
    if len(last):
        lo, hi = TARGETS["cohort_completion"]
        print(flag((last["status"] == "graduated").mean(), lo, hi,
                   f"completion ({len(mature)} earliest cohorts)"))


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
    print("  Grade band breakdown (combined mark, 40/60 weight):")
    pivoted = (
        assess.pivot_table(index=["student_id", "academic_year", "module_code"],
                           columns="component_code", values="assessment_mark")
        .reset_index()
    )
    pivoted.columns.name = None
    if "MIDTERM" in pivoted.columns and "FINAL" in pivoted.columns:
        pivoted["combined"] = pivoted[["MIDTERM", "FINAL"]].mean(axis=1)
        def _g(m):
            if m >= 70: return "First"
            if m >= 60: return "2:1"
            if m >= 50: return "2:2"
            if m >= 40: return "Third"
            return "Fail"
        pivoted["grade"] = pivoted["combined"].apply(_g)
        grades = pivoted["grade"].value_counts()
        total  = len(pivoted)
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
    assess   = t["fact_assessment"]
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
        lo, hi = TARGETS["elf_dwarf_mark_gap_pp"]
        print(f"\n{flag(gap, lo, hi, 'Elf–Dwarf mean mark gap (pp)')}")

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

    # Good degree rate (First + 2:1) from classified graduates
    grad = t.get("fact_graduate_outcomes")
    if grad is not None:
        print()
        print("  Good degree rate (First + 2:1) by species:")
        gd = grad.merge(students[["student_id","species","clan"]], on="student_id", how="left")
        gd["good_degree"] = gd["degree_classification"].isin(["First", "2:1"])
        gd_sp = gd.groupby("species")["good_degree"].mean() * 100
        for species, rate in gd_sp.sort_values(ascending=False).items():
            n = gd[gd["species"] == species]["student_id"].nunique()
            print(f"    {species:<10}  {rate:.1f}%  (n={n})")
        if "Elf" in gd_sp.index and "Dwarf" in gd_sp.index:
            gd_gap = gd_sp["Elf"] - gd_sp["Dwarf"]
            lo, hi = TARGETS["elf_dwarf_good_degree_gap_pp"]
            print(f"\n{flag(gd_gap, lo, hi, 'Elf–Dwarf good degree gap (pp)')}")

        print()
        print("  Good degree rate by clan:")
        gd_clan = gd.groupby("clan")["good_degree"].mean() * 100
        for c, r in gd_clan.sort_values(ascending=False).items():
            print(f"    {c:<20}  {r:.1f}%")

    # Mean mark by clan
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
    # These checks run against the PUBLISHED observable schema — the latent
    # constructs (attendance_rate, academic_engagement, difficulty_level) were
    # stripped from data/relational/ by the output firewall. We validate that
    # the observable data a downstream researcher receives still shows the
    # expected relationships:
    #   - attendance (attended_sessions / total_sessions) -> mark
    #   - module difficulty (re-joined from config, a legitimate validation
    #     input — not published student data) -> mark
    # Only FINAL component rows are used, so each module contributes one mark.
    assess = t["fact_assessment"]
    finals = assess[assess["component_code"] == "FINAL"] if "component_code" in assess.columns else assess

    # Engagement -> mark, using observable attendance from session counts.
    eng = t["fact_weekly_engagement"]
    grp = (
        eng.groupby(["student_id", "academic_year", "module_code"])[["attended_sessions", "total_sessions"]]
        .sum()
        .reset_index()
    )
    grp = grp[grp["total_sessions"] > 0]
    grp["attendance"] = grp["attended_sessions"] / grp["total_sessions"]
    merged = finals.merge(grp, on=["student_id", "academic_year", "module_code"], how="inner")
    if len(merged) > 100:
        corr = merged["attendance"].corr(merged["assessment_mark"])
        lo, hi = TARGETS["engagement_mark_corr"]
        print(flag(corr, lo, hi, "attendance -> mark correlation (Pearson r)"))
        print(f"  Matched rows: {len(merged)}  (note: first engagement year only)")
    else:
        print("  WARN  Not enough matched attendance–mark rows to compute correlation")

    # Difficulty -> mark, difficulty re-joined from config by module_code.
    print()
    mc_path = CONFIG / "module_characteristics.csv"
    if mc_path.exists():
        mods = pd.read_csv(mc_path)[["module_code", "difficulty_level"]].dropna()
        mods["module_code"] = mods["module_code"].astype(str)
        assess_d = finals.copy()
        assess_d["module_code"] = assess_d["module_code"].astype(str)
        assess_d = assess_d.merge(mods, on="module_code", how="inner")
        if len(assess_d) > 100:
            corr_d = assess_d["difficulty_level"].corr(assess_d["assessment_mark"])
            lo, hi = TARGETS["difficulty_mark_corr"]
            print(flag(corr_d, lo, hi, "difficulty -> mark correlation (Pearson r)"))
            print(f"  Matched rows: {len(assess_d)}")
        else:
            print("  WARN  Not enough matched difficulty–mark rows")
    else:
        print(f"  WARN  {mc_path} not found — cannot check difficulty–mark correlation")


# ---------------------------------------------------------------------------

def main():
    print("\nStonegrove University — Output Validation Report")
    print(f"Reading from: {RELATIONAL.resolve()}")

    t = load()
    check_integrity(t)
    check_shapes(t)
    check_progression(t)
    check_marks(t)
    check_awarding_gaps(t)
    check_correlations(t)

    print(f"\n{'='*60}")
    if FAILURES:
        print(f"  END OF REPORT — {len(FAILURES)} INTEGRITY CHECK(S) FAILED")
        for f in FAILURES:
            print(f"    - {f}")
    else:
        print("  END OF REPORT — integrity checks passed")
    print(f"{'='*60}\n")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
