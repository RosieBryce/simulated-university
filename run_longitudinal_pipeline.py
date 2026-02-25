#!/usr/bin/env python3
"""
Run the Stonegrove University longitudinal simulation (7 years, 5 graduating cohorts).

Loops over academic years 1046-47 to 1052-53:
- Year 1: New cohort (500) + progressing/repeating from previous year
- Runs: student gen (new only) → enrollment → engagement → assessment → progression
- Appends outputs per year to CSVs

Execute from project root.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

# Academic years: 7 years, 5 cohorts (first graduates year 3)
ACADEMIC_YEARS_FULL = ["1046-47", "1047-48", "1048-49", "1049-50", "1050-51", "1051-52", "1052-53"]
ACADEMIC_YEARS = ACADEMIC_YEARS_FULL
COHORT_SIZE = 500
BASE_SEED = 42


def _status_change_at(academic_year: str) -> str:
    """Start of year when status takes effect. e.g. 1047-48 -> 1047-09-01"""
    y = academic_year.split("-")[0]
    return f"{y}-09-01"


def _assessment_date(academic_year: str) -> str:
    """End of year assessment date (May of second calendar year)."""
    first_year = int(academic_year.split("-")[0])
    return f"{first_year + 1}-05-15"


def run_year(
    academic_year: str,
    year_index: int,
    new_students_df,
    continuing_students_df,
    progression_outcomes_prev,
    seed: int,
    prior_progression_df=None,
):
    """Run pipeline for one academic year. Returns (enrolled_df, progression_df)."""
    import pandas as pd
    import os
    os.chdir(PROJECT_ROOT)
    sys.path.insert(0, str(PROJECT_ROOT))
    sys.path.insert(0, str(PROJECT_ROOT / "supporting_systems"))

    from core_systems.student_generation_pipeline import generate_students
    from core_systems.program_enrollment_system import ProgramEnrollmentSystem
    from core_systems.engagement_system import EngagementSystem
    from core_systems.assessment_system import AssessmentSystem
    from core_systems.progression_system import ProgressionSystem
    from core_systems.graduate_outcomes_system import GraduateOutcomesSystem

    enrollment_sys = ProgramEnrollmentSystem()
    engagement_sys = EngagementSystem()
    assessment_sys = AssessmentSystem(seed=seed)
    progression_sys = ProgressionSystem(seed=seed)
    outcomes_sys = GraduateOutcomesSystem(seed=seed)

    status_change = _status_change_at(academic_year)
    assessment_date = _assessment_date(academic_year)

    # 1. Combine new + continuing students
    if continuing_students_df is not None and len(continuing_students_df) > 0:
        cont = continuing_students_df.copy()
        if "programme_year_next" in cont.columns:
            cont["programme_year"] = cont["programme_year_next"].fillna(1).astype(int)
        elif "programme_year" in cont.columns:
            prog = cont["programme_year"].fillna(1).astype(int)
            is_progress = cont.get("status", pd.Series(dtype=object)).astype(str) == "enrolled"
            cont["programme_year"] = prog + is_progress.astype(int)
        else:
            cont["programme_year"] = 1
        continuing_enrolled = enrollment_sys.enroll_continuing_students(
            cont, academic_year=academic_year, status_change_at=status_change,
        )
    else:
        continuing_enrolled = pd.DataFrame()

    if new_students_df is not None and len(new_students_df) > 0:
        # Assign student_ids for new cohort (offset by year)
        new_students_df = new_students_df.copy()
        offset = year_index * COHORT_SIZE
        new_students_df["student_id"] = range(offset, offset + len(new_students_df))
        new_enrolled = enrollment_sys.enroll_students_batch(
            new_students_df,
            academic_year=academic_year,
            status_change_at=status_change,
        )
    else:
        new_enrolled = pd.DataFrame()

    # Combine (drop duplicate columns before concat)
    def _dedup_cols(df):
        return df.loc[:, ~df.columns.duplicated()] if len(df) > 0 else df
    if len(continuing_enrolled) > 0 and len(new_enrolled) > 0:
        enrolled_df = pd.concat([_dedup_cols(new_enrolled), _dedup_cols(continuing_enrolled)], ignore_index=True)
    elif len(continuing_enrolled) > 0:
        enrolled_df = continuing_enrolled
    elif len(new_enrolled) > 0:
        enrolled_df = new_enrolled
    else:
        return None, None

    # 2. Engagement (deduplicate columns before passing downstream)
    enrolled_clean = enrolled_df.loc[:, ~enrolled_df.columns.duplicated()] if len(enrolled_df) > 0 else enrolled_df
    weekly_df, semester_df = engagement_sys.generate_engagement_data(
        enrolled_clean, weeks_per_semester=12, academic_year=academic_year
    )
    weekly_df["academic_year"] = academic_year

    # 3. Assessment — pass engagement DataFrame directly (no mid-loop disk write)
    # assessment_date no longer passed; dates computed internally per module/semester
    assessment_df = assessment_sys.generate_assessment_data(
        enrolled_clean,
        academic_year=academic_year,
        weekly_engagement_df=weekly_df,
    )

    # 4. Progression (enrolled_clean already built above)
    progression_df = progression_sys.compute_progression(
        assessment_df,
        enrolled_clean,
        academic_year=academic_year,
        status_change_at=_status_change_at(ACADEMIC_YEARS[year_index + 1]) if year_index + 1 < len(ACADEMIC_YEARS) else "",
        prior_progression_df=prior_progression_df,
    )

    # 5. Graduate outcomes — for students who graduated this year
    graduates = enrolled_clean[
        enrolled_clean.get('status', pd.Series(dtype=str)).astype(str) == 'graduated'
    ] if 'status' in enrolled_clean.columns else pd.DataFrame()
    if len(graduates) == 0:
        # Also check progression_df for graduated students, merge back to get traits
        grad_sids = progression_df[progression_df['status'] == 'graduated']['student_id'].astype(str).tolist()
        graduates = enrolled_clean[enrolled_clean['student_id'].astype(str).isin(grad_sids)]
    graduate_outcomes_df = outcomes_sys.generate_outcomes(
        graduates, academic_year=academic_year, all_assessment_df=assessment_df
    )

    return enrolled_df, progression_df, assessment_df, weekly_df, semester_df, graduate_outcomes_df


def main():
    import pandas as pd
    import os
    os.chdir(PROJECT_ROOT)
    sys.path.insert(0, str(PROJECT_ROOT))
    sys.path.insert(0, str(PROJECT_ROOT / "supporting_systems"))

    from core_systems.student_generation_pipeline import generate_students
    from core_systems.program_enrollment_system import ProgramEnrollmentSystem
    from core_systems.engagement_system import EngagementSystem
    from core_systems.assessment_system import AssessmentSystem
    from core_systems.progression_system import ProgressionSystem
    from core_systems.graduate_outcomes_system import GraduateOutcomesSystem

    print("Stonegrove University Longitudinal Pipeline")
    print("=" * 50)
    print(f"Academic years: {ACADEMIC_YEARS[0]} to {ACADEMIC_YEARS[-1]}")
    print(f"Cohort size: {COHORT_SIZE}")
    print()

    data_dir = PROJECT_ROOT / "data"
    data_dir.mkdir(exist_ok=True)

    all_enrollment = []
    all_assessment = []
    all_progression = []
    all_individual = []
    all_weekly = []
    all_graduate_outcomes = []

    progression_prev = None
    prev_enrolled_df = None
    accumulated_progression = None  # all prior years' progression (for repeat history)

    for i, acad_year in enumerate(ACADEMIC_YEARS):
        print(f"\n--- {acad_year} ---")

        seed = BASE_SEED + i * 1000

        # New cohort (Year 1 only) every year
        new_students = generate_students(n=COHORT_SIZE, seed=seed)
        new_students["academic_year"] = acad_year
        new_students["student_id"] = range(i * COHORT_SIZE, (i + 1) * COHORT_SIZE)
        all_individual.append(new_students)

        # Continuing students from previous progression (enrolled + repeating, not withdrawn)
        if progression_prev is not None and len(progression_prev) > 0 and prev_enrolled_df is not None:
            active = progression_prev[
                progression_prev["status"].isin(["enrolled", "repeating"])
            ].copy()
            if len(active) > 0:
                prev = prev_enrolled_df.loc[:, ~prev_enrolled_df.columns.duplicated()].copy()
                prev["student_id"] = prev["student_id"].astype(str)
                drop_from_prev = [
                    "status", "status_change_at", "academic_year",
                    "year_outcome", "modules_passed", "avg_mark", "modules_total", "programme_year_next",
                ]
                prev = prev.drop(columns=[c for c in drop_from_prev if c in prev.columns], errors="ignore")
                active = active.copy()
                active["student_id"] = active["student_id"].astype(str)
                active = active.merge(prev, on="student_id", how="left")
                continuing_students = active
            else:
                continuing_students = None
        else:
            continuing_students = None

        # Run pipeline for this year
        enrolled_df, progression_df, assessment_df, weekly_df, semester_df, graduate_outcomes_df = run_year(
            acad_year, i, new_students, continuing_students, progression_prev, seed,
            prior_progression_df=accumulated_progression,
        )

        if enrolled_df is None:
            print(f"  No students for {acad_year}, skipping.")
            continue

        all_enrollment.append(enrolled_df.loc[:, ~enrolled_df.columns.duplicated()])
        all_assessment.append(assessment_df)
        all_progression.append(progression_df)
        all_weekly.append(weekly_df)
        if graduate_outcomes_df is not None and len(graduate_outcomes_df) > 0:
            all_graduate_outcomes.append(graduate_outcomes_df)
        progression_prev = progression_df
        prev_enrolled_df = enrolled_df
        # Accumulate all progression outcomes for repeat-history lookup in subsequent years
        accumulated_progression = pd.concat(all_progression, ignore_index=True)

        n_grads = len(graduate_outcomes_df) if graduate_outcomes_df is not None else 0
        print(f"  Enrolled: {len(enrolled_df)}, Assessments: {len(assessment_df)}, Graduates: {n_grads}")

    # Concatenate and save — all files overwritten fresh each run
    if all_enrollment:
        clean = [e.loc[:, ~e.columns.duplicated()] for e in all_enrollment]
        pd.concat(clean, ignore_index=True).to_csv(
            data_dir / "stonegrove_enrollment.csv", index=False
        )
        print(f"\nSaved stonegrove_enrollment.csv")
    if all_assessment:
        pd.concat(all_assessment, ignore_index=True).to_csv(
            data_dir / "stonegrove_assessment_events.csv", index=False
        )
    if all_progression:
        pd.concat(all_progression, ignore_index=True).to_csv(
            data_dir / "stonegrove_progression_outcomes.csv", index=False
        )
    if all_individual:
        pd.concat(all_individual, ignore_index=True).to_csv(
            data_dir / "stonegrove_individual_students.csv", index=False
        )
    if all_weekly:
        pd.concat(all_weekly, ignore_index=True).to_csv(
            data_dir / "stonegrove_weekly_engagement.csv", index=False
        )
    if all_graduate_outcomes:
        pd.concat(all_graduate_outcomes, ignore_index=True).to_csv(
            data_dir / "stonegrove_graduate_outcomes.csv", index=False
        )
        print(f"Saved stonegrove_graduate_outcomes.csv")

    # Write metadata
    import subprocess
    try:
        git_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()[:12]
    except Exception:
        git_commit = "unknown"
    import json
    from datetime import datetime
    metadata = {
        "model_version": "v2.0-longitudinal",
        "git_commit": git_commit,
        "random_seed": BASE_SEED,
        "generation_timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "config_versions": {"progression_rules": "v1.0"},
        "cohort_size": COHORT_SIZE,
        "years_generated": len(ACADEMIC_YEARS),
        "academic_years": ACADEMIC_YEARS,
        "cohorts_total": len(ACADEMIC_YEARS),
        "cohorts_graduating": max(0, len(ACADEMIC_YEARS) - 2),
    }
    with open(data_dir / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"\nSaved data/metadata.json")

    print("\nPipeline complete.")


if __name__ == "__main__":
    main()
