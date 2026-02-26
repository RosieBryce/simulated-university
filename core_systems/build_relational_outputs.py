#!/usr/bin/env python3
"""
Build relational output tables from raw pipeline CSVs.

Reads from data/ and config/, writes 10 clean tables to data/relational/:
  Dimensions: dim_students, dim_programmes, dim_modules, dim_academic_years
  Facts:       fact_enrollment, fact_assessment, fact_progression,
               fact_graduate_outcomes, fact_nss_responses,
               fact_weekly_engagement_YYYY-YY.csv (one file per academic year)

Run from project root after run_longitudinal_pipeline.py.
"""

from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CONFIG_DIR = PROJECT_ROOT / "config"
OUT_DIR = DATA_DIR / "relational"

ACADEMIC_YEARS = ["1046-47", "1047-48", "1048-49", "1049-50", "1050-51", "1051-52", "1052-53"]


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def load_weekly_engagement() -> pd.DataFrame:
    """Load weekly engagement from per-year splits in data/relational/."""
    splits = sorted((DATA_DIR / "relational").glob("fact_weekly_engagement_*.csv"))
    if not splits:
        raise FileNotFoundError(
            "No weekly engagement data found. Run run_longitudinal_pipeline.py first — "
            "it writes fact_weekly_engagement_YYYY-YY.csv to data/relational/."
        )
    return pd.concat([pd.read_csv(p) for p in splits], ignore_index=True)


# ---------------------------------------------------------------------------
# Dimensions
# ---------------------------------------------------------------------------

def build_dim_academic_years() -> pd.DataFrame:
    rows = []
    for y in ACADEMIC_YEARS:
        y1 = int(y.split("-")[0])
        y2 = y1 + 1
        rows.append({
            "academic_year":        y,
            "start_date":           f"{y1}-09-01",
            "end_date":             f"{y2}-07-31",
            "s1_midterm_date":      f"{y1}-11-01",
            "s1_final_date":        f"{y1}-12-15",
            "s2_midterm_date":      f"{y2}-03-15",
            "s2_final_date":        f"{y2}-05-15",
        })
    return pd.DataFrame(rows)


def build_dim_students(students_df: pd.DataFrame) -> pd.DataFrame:
    base_cols = [
        "base_openness", "base_conscientiousness", "base_extraversion",
        "base_agreeableness", "base_neuroticism",
    ]
    df = students_df.drop(columns=[c for c in base_cols if c in students_df.columns])
    df = df.rename(columns={"academic_year": "cohort_year"})
    other = [c for c in df.columns if c not in ("student_id", "cohort_year")]
    return df[["student_id", "cohort_year"] + other].reset_index(drop=True)


def build_dim_programmes(prog_chars_df: pd.DataFrame, enrollment_df: pd.DataFrame) -> pd.DataFrame:
    prog_lookup = (
        enrollment_df[["program_code", "program_name", "department"]]
        .drop_duplicates("program_code")
        .rename(columns={"program_code": "programme_code", "program_name": "programme_name"})
    )
    merged = prog_lookup.merge(prog_chars_df, on="programme_name", how="left")
    if "faculty_x" in merged.columns:
        merged = merged.rename(columns={"faculty_x": "faculty"}).drop(columns=["faculty_y"])
    col_order = [
        "programme_code", "programme_name", "faculty", "department", "description",
        "social_intensity", "practical_theoretical_balance", "stress_level",
        "career_prospects", "academic_difficulty", "creativity_requirement",
        "leadership_opportunities", "research_intensity", "community_engagement",
        "innovation_focus",
    ]
    return merged[[c for c in col_order if c in merged.columns]].reset_index(drop=True)


def build_dim_modules(assessment_df: pd.DataFrame, module_chars_df: pd.DataFrame) -> pd.DataFrame:
    core = (
        assessment_df[["module_code", "module_title", "programme_code", "module_year", "assessment_type"]]
        .drop_duplicates("module_code")
        .copy()
    )
    char_cols = [
        "module_title", "semester", "difficulty_level", "social_requirements",
        "creativity_requirements", "practical_theoretical_balance", "stress_level",
        "group_work_intensity", "independent_study_requirement", "description",
    ]
    chars = (
        module_chars_df[[c for c in char_cols if c in module_chars_df.columns]]
        .drop_duplicates("module_title")
    )
    merged = core.merge(chars, on="module_title", how="left")
    col_order = [
        "module_code", "module_title", "programme_code", "module_year", "semester",
        "assessment_type", "difficulty_level", "social_requirements", "creativity_requirements",
        "practical_theoretical_balance", "stress_level", "group_work_intensity",
        "independent_study_requirement", "description",
    ]
    return merged[[c for c in col_order if c in merged.columns]].reset_index(drop=True)


# ---------------------------------------------------------------------------
# Facts
# ---------------------------------------------------------------------------

def build_fact_enrollment(enrollment_df: pd.DataFrame) -> pd.DataFrame:
    keep = [
        "student_id", "academic_year", "program_code",
        "programme_year", "status", "status_change_at",
    ]
    df = enrollment_df[[c for c in keep if c in enrollment_df.columns]].copy()
    return df.rename(columns={"program_code": "programme_code"})


def build_fact_weekly_engagement(
    engagement_df: pd.DataFrame,
    assessment_df: pd.DataFrame,
) -> pd.DataFrame:
    lookup = (
        assessment_df[["programme_code", "module_title", "module_code"]]
        .drop_duplicates(["programme_code", "module_title"])
    )
    df = engagement_df.rename(columns={"program_code": "programme_code"}).copy()
    df = df.merge(lookup, on=["programme_code", "module_title"], how="left")

    unmatched = df["module_code"].isna().sum()
    if unmatched > 0:
        print(f"  WARNING: {unmatched:,} engagement rows could not be matched to a module_code")

    keep = [
        "student_id", "academic_year", "week_number", "module_code", "semester",
        "attendance_rate", "participation_score", "academic_engagement",
        "social_engagement", "stress_level",
    ]
    return df[[c for c in keep if c in df.columns]]


def build_fact_assessment(assessment_df: pd.DataFrame) -> pd.DataFrame:
    keep = [
        "student_id", "academic_year", "module_code", "component_code",
        "assessment_mark", "combined_mark", "grade", "assessment_date",
    ]
    return assessment_df[[c for c in keep if c in assessment_df.columns]].copy()


def build_fact_progression(progression_df: pd.DataFrame) -> pd.DataFrame:
    return progression_df.copy()


def build_fact_graduate_outcomes(graduate_outcomes_df: pd.DataFrame) -> pd.DataFrame:
    return graduate_outcomes_df.copy()


def build_fact_nss_responses(nss_df: pd.DataFrame) -> pd.DataFrame:
    return nss_df.copy()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    OUT_DIR.mkdir(exist_ok=True)

    print("Loading raw pipeline outputs...")
    students_df      = pd.read_csv(DATA_DIR / "stonegrove_individual_students.csv")
    enrollment_df    = pd.read_csv(DATA_DIR / "stonegrove_enrollment.csv")
    engagement_df    = load_weekly_engagement()
    assessment_df    = pd.read_csv(DATA_DIR / "stonegrove_assessment_events.csv")
    progression_df   = pd.read_csv(DATA_DIR / "stonegrove_progression_outcomes.csv")
    grad_outcomes_df = pd.read_csv(DATA_DIR / "stonegrove_graduate_outcomes.csv")
    nss_df           = pd.read_csv(DATA_DIR / "stonegrove_nss_responses.csv")

    print("Loading config files...")
    prog_chars_df   = pd.read_csv(CONFIG_DIR / "programme_characteristics.csv")
    module_chars_df = pd.read_csv(CONFIG_DIR / "module_characteristics.csv")

    tables = {
        "dim_academic_years":     build_dim_academic_years(),
        "dim_students":           build_dim_students(students_df),
        "dim_programmes":         build_dim_programmes(prog_chars_df, enrollment_df),
        "dim_modules":            build_dim_modules(assessment_df, module_chars_df),
        "fact_enrollment":        build_fact_enrollment(enrollment_df),
        "fact_assessment":        build_fact_assessment(assessment_df),
        "fact_progression":       build_fact_progression(progression_df),
        "fact_graduate_outcomes": build_fact_graduate_outcomes(grad_outcomes_df),
        "fact_nss_responses":     build_fact_nss_responses(nss_df),
    }

    print(f"\nWriting to {OUT_DIR}/:")
    for name, df in tables.items():
        path = OUT_DIR / f"{name}.csv"
        df.to_csv(path, index=False)
        print(f"  {name}.csv  — {len(df):,} rows × {len(df.columns)} cols")

    # Weekly engagement: write one cleaned file per academic year
    for year in ACADEMIC_YEARS:
        year_eng = engagement_df[engagement_df["academic_year"] == year]
        year_fact = build_fact_weekly_engagement(year_eng, assessment_df)
        path = OUT_DIR / f"fact_weekly_engagement_{year}.csv"
        year_fact.to_csv(path, index=False)
        print(f"  fact_weekly_engagement_{year}.csv  — {len(year_fact):,} rows × {len(year_fact.columns)} cols")

    print("\nDone.")


if __name__ == "__main__":
    main()
