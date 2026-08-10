"""
aggregate_dashboard.py — produces JSON data files for docs/explore/data/.
Run after the full longitudinal pipeline.

Output files (docs/explore/data/):
  attainment.json   module mark summaries by species × faculty × year × prog year
  clans.json        mark summaries by clan × species × faculty
  engagement.json   weekly engagement by species × faculty × academic year × week
  progression.json  year-end status by species × faculty × academic year
  nss.json          NSS theme scores by species × faculty × academic year
  survey.json       enrolment survey by species × faculty × academic year × prog year
  outcomes.json     graduate outcomes by species × faculty
"""

import glob
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Windows consoles default to cp1252, which cannot encode the arrows/dashes in the
# progress output. Without this the script dies mid-run, after some JSON is written.
sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
REL  = ROOT / "data" / "relational"
OUT  = ROOT / "docs" / "explore" / "data"
OUT.mkdir(parents=True, exist_ok=True)

GOOD_GRADES  = {"First", "2:1"}
GRADE_ORDER  = ["First", "2:1", "2:2", "Third", "Fail"]
SALARY_LABELS = {1: "Band 1 (lowest)", 2: "Band 2", 3: "Band 3", 4: "Band 4", 5: "Band 5 (highest)"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def r2(x):
    return round(float(x), 2)

def weighted_avg(rows, val_key, weight_key="n"):
    total_w = sum(r[weight_key] for r in rows)
    if not total_w:
        return 0.0
    return sum(r[val_key] * r[weight_key] for r in rows) / total_w

def grade_dist(series):
    n = len(series)
    return {g: r2(100 * (series == g).sum() / n) for g in GRADE_ORDER}


# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------

def load():
    print("  dim_students …")
    students = pd.read_csv(
        REL / "dim_students.csv",
        usecols=["student_id", "species", "clan", "gender", "socio_economic_rank", "first_gen", "disabilities"],
    )

    print("  dim_programmes …")
    programmes = pd.read_csv(
        REL / "dim_programmes.csv",
        usecols=["programme_code", "faculty"],
    )

    print("  fact_enrollment …")
    enrollment = pd.read_csv(
        REL / "fact_enrollment.csv",
        usecols=["student_id", "academic_year", "programme_code", "programme_year"],
    )

    print("  fact_assessment …")
    assessment_raw = pd.read_csv(
        REL / "fact_assessment.csv",
        usecols=["student_id", "academic_year", "module_code", "component_code", "assessment_mark"],
    )
    # Derive combined mark (50/50) and grade for dashboard aggregation
    pivoted = (
        assessment_raw.pivot_table(
            index=["student_id", "academic_year", "module_code"],
            columns="component_code",
            values="assessment_mark",
        )
        .reset_index()
    )
    pivoted.columns.name = None
    pivoted["combined_mark"] = pivoted[["MIDTERM", "FINAL"]].mean(axis=1)
    def _grade(m):
        if m >= 70: return "First"
        if m >= 60: return "2:1"
        if m >= 50: return "2:2"
        if m >= 40: return "Third"
        return "Fail"
    pivoted["grade"] = pivoted["combined_mark"].apply(_grade)
    pivoted["component_code"] = "FINAL"
    assessment = pivoted[["student_id", "academic_year", "component_code", "combined_mark", "grade"]].copy()

    print("  fact_progression …")
    progression = pd.read_csv(
        REL / "fact_progression.csv",
        usecols=["student_id", "academic_year", "year_outcome", "status"],
    )

    print("  fact_good_honours …")
    good_honours = pd.read_csv(
        REL / "fact_good_honours.csv",
        usecols=["student_id", "academic_year_graduated", "programme_code", "degree_classification"],
    )

    print("  fact_graduate_outcomes …")
    grad_survey = pd.read_csv(
        REL / "fact_graduate_outcomes.csv",
        usecols=["student_id", "academic_year_graduated", "survey_responded",
                 "outcome_type", "professional_level", "salary_band"],
    )
    # Merge: honours for all graduates, survey columns only for respondents
    grad_out = good_honours.merge(
        grad_survey, on=["student_id", "academic_year_graduated"], how="left"
    )

    print("  fact_nss_responses …")
    nss = pd.read_csv(REL / "fact_nss_responses.csv")

    print("  fact_enrolment_survey …")
    survey = pd.read_csv(REL / "fact_enrolment_survey.csv")

    print("  fact_weekly_engagement (all years) …")
    eng_files = sorted(glob.glob(str(REL / "fact_weekly_engagement_*.csv")))
    header = pd.read_csv(eng_files[0], nrows=0).columns.tolist()
    # Attendance: new schema uses session counts, old schema uses rate
    if "attended_sessions" in header:
        att_cols = ["attended_sessions", "total_sessions"]
    else:
        att_cols = ["attendance_rate"]
    # Load only columns that actually exist in this schema
    wanted = ["student_id", "academic_year", "week_number",
              "participation_score", "academic_engagement",
              "social_engagement", "stress_level", "vle_logins"]
    eng_base_cols = [c for c in wanted if c in header]
    eng_chunks = []
    for f in eng_files:
        eng_chunks.append(pd.read_csv(f, usecols=eng_base_cols + att_cols))
    engagement = pd.concat(eng_chunks, ignore_index=True)

    return dict(
        students=students,
        programmes=programmes,
        enrollment=enrollment,
        assessment=assessment,
        progression=progression,
        grad_out=grad_out,
        nss=nss,
        survey=survey,
        engagement=engagement,
    )


# ---------------------------------------------------------------------------
# Attainment
# ---------------------------------------------------------------------------

def build_attainment(t):
    finals = t["assessment"][t["assessment"]["component_code"] == "FINAL"].dropna(subset=["combined_mark"]).copy()
    finals = finals.merge(t["students"][["student_id", "species", "clan"]], on="student_id")
    finals = finals.merge(t["enrollment"], on=["student_id", "academic_year"])
    finals = finals.merge(t["programmes"], on="programme_code")
    finals["good"] = finals["grade"].isin(GOOD_GRADES)

    by_group = []
    for (species, faculty, ay, py), grp in finals.groupby(["species", "faculty", "academic_year", "programme_year"]):
        by_group.append({
            "species":       species,
            "faculty":       faculty,
            "academic_year": ay,
            "programme_year": int(py),
            "mean_mark":     r2(grp["combined_mark"].mean()),
            "good_mark_pct": r2(100 * grp["good"].mean()),
            "n":             len(grp),
            "grade_dist":    grade_dist(grp["grade"]),
        })

    by_clan = []
    for (clan, species, faculty), grp in finals.groupby(["clan", "species", "faculty"]):
        by_clan.append({
            "clan":          clan,
            "species":       species,
            "faculty":       faculty,
            "mean_mark":     r2(grp["combined_mark"].mean()),
            "good_mark_pct": r2(100 * grp["good"].mean()),
            "n":             len(grp),
            "grade_dist":    grade_dist(grp["grade"]),
        })

    return by_group, by_clan


# ---------------------------------------------------------------------------
# Engagement
# ---------------------------------------------------------------------------

def build_engagement(t):
    eng = t["engagement"].copy()

    # Normalise attendance to 0–1 rate
    if "attended_sessions" in eng.columns:
        eng["attendance"] = eng["attended_sessions"] / eng["total_sessions"].replace(0, np.nan)
    else:
        eng["attendance"] = eng["attendance_rate"]

    # Average per student × year × week (across modules) before joining demographics
    agg_map = {
        "attendance":  "mean",
        "vle_logins":  "mean",
    }
    agg_map = {k: v for k, v in agg_map.items() if k in eng.columns}
    per_student = eng.groupby(["student_id", "academic_year", "week_number"]).agg(agg_map).reset_index()

    per_student = per_student.merge(t["students"][["student_id", "species"]], on="student_id")

    # One programme per student per year
    enroll_prog = (
        t["enrollment"][["student_id", "academic_year", "programme_code"]]
        .drop_duplicates(subset=["student_id", "academic_year"])
    )
    per_student = per_student.merge(enroll_prog, on=["student_id", "academic_year"])
    per_student = per_student.merge(t["programmes"], on="programme_code")

    metric_cols = list(agg_map.keys())
    rows = []
    for (species, faculty, ay, wk), grp in per_student.groupby(["species", "faculty", "academic_year", "week_number"]):
        row = {
            "species":       species,
            "faculty":       faculty,
            "academic_year": ay,
            "week_number":   int(wk),
            "n":             len(grp),
        }
        for col in metric_cols:
            row[f"mean_{col}"] = r2(grp[col].mean())
        rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# Progression
# ---------------------------------------------------------------------------

def build_progression(t):
    prog = t["progression"].merge(t["students"][["student_id", "species"]], on="student_id")
    enroll_prog = (
        t["enrollment"][["student_id", "academic_year", "programme_code", "programme_year"]]
        .drop_duplicates(subset=["student_id", "academic_year"])
    )
    prog = prog.merge(enroll_prog, on=["student_id", "academic_year"])
    prog = prog.merge(t["programmes"], on="programme_code")

    rows = []
    for (species, faculty, ay, py), grp in prog.groupby(["species", "faculty", "academic_year", "programme_year"]):
        n = len(grp)
        rows.append({
            "species":        species,
            "faculty":        faculty,
            "academic_year":  ay,
            "programme_year": int(py),
            "pass_pct":       r2(100 * (grp["year_outcome"] == "pass").sum() / n),
            "withdraw_pct":   r2(100 * (grp["status"] == "withdrawn").sum() / n),
            "repeat_pct":     r2(100 * (grp["status"] == "repeating").sum() / n),
            "n":              n,
        })
    return rows


# ---------------------------------------------------------------------------
# NSS
# ---------------------------------------------------------------------------

NSS_THEMES = [
    "teaching_quality", "learning_opportunities", "assessment_feedback",
    "academic_support", "organisation_management", "learning_resources",
    "student_voice", "overall_satisfaction",
]

def build_nss(t):
    nss = t["nss"]
    nss = nss[nss["survey_responded"] == True].copy()
    nss = nss.merge(t["students"][["student_id", "species"]], on="student_id")
    nss = nss.merge(t["programmes"], on="programme_code")

    rows = []
    for (species, faculty, ay), grp in nss.groupby(["species", "faculty", "academic_year"]):
        row = {"species": species, "faculty": faculty, "academic_year": ay, "n": len(grp)}
        for col in NSS_THEMES:
            if col in grp.columns:
                row[col] = r2(grp[col].mean())
        rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# Enrolment survey
# ---------------------------------------------------------------------------

SURVEY_COLS = [
    "career_clarity", "career_confidence",
    "belonging_peers", "belonging_programme",
    "academic_self_efficacy", "support_satisfaction",
]

def build_survey(t):
    survey = t["survey"]
    survey = survey[survey["survey_responded"] == True].copy()
    survey = survey.merge(t["students"][["student_id", "species"]], on="student_id")
    enroll_prog = (
        t["enrollment"][["student_id", "academic_year", "programme_code"]]
        .drop_duplicates(subset=["student_id", "academic_year"])
    )
    survey = survey.merge(enroll_prog, on=["student_id", "academic_year"])
    survey = survey.merge(t["programmes"], on="programme_code")

    rows = []
    for (species, faculty, ay, py), grp in survey.groupby(["species", "faculty", "academic_year", "programme_year"]):
        row = {
            "species":        species,
            "faculty":        faculty,
            "academic_year":  ay,
            "programme_year": int(py),
            "n":              len(grp),
        }
        for col in SURVEY_COLS:
            if col in grp.columns:
                row[col] = r2(grp[col].mean())
        rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# Graduate outcomes
# ---------------------------------------------------------------------------

def build_outcomes(t):
    grad = t["grad_out"].merge(t["students"][["student_id", "species"]], on="student_id")
    grad = grad.merge(t["programmes"], on="programme_code")
    grad["good_degree"]   = grad["degree_classification"].isin(GOOD_GRADES)
    grad["employed"]      = grad["outcome_type"] == "employed"
    grad["further_study"] = grad["outcome_type"] == "further_study"
    grad["professional"]  = grad["professional_level"] == "professional"

    rows = []
    for (species, faculty), grp in grad.groupby(["species", "faculty"]):
        employed_grp = grp[grp["employed"]]
        salary_counts = {}
        if len(employed_grp):
            for band, label in SALARY_LABELS.items():
                pct_val = r2(100 * (employed_grp["salary_band"] == band).sum() / len(employed_grp))
                salary_counts[label] = pct_val

        # Degree grade dist (all graduates, survey responded or not)
        g_dist = {g: r2(100 * (grp["degree_classification"] == g).sum() / len(grp))
                  for g in ["First", "2:1", "2:2", "Third"]}

        rows.append({
            "species":           species,
            "faculty":           faculty,
            "good_degree_pct":   r2(100 * grp["good_degree"].mean()),
            "employment_pct":    r2(100 * grp["employed"].mean()),
            "further_study_pct": r2(100 * grp["further_study"].mean()),
            "professional_pct":  r2(100 * grp["professional"].mean()) if len(employed_grp) else 0.0,
            "grade_dist":        g_dist,
            "salary_dist":       salary_counts,
            "n":                 len(grp),
        })
    return rows


# ---------------------------------------------------------------------------
# Overview
# ---------------------------------------------------------------------------

DISABILITY_GROUPS = {
    "mental_health_disability": "Mental health condition",
    "adhd":                     "ADHD",
    "physical_disability":      "Physical disability",
    "autistic_spectrum":        "Autistic spectrum",
    "deaf_or_hearing_impaired": "Deaf or hard of hearing",
    "dyslexia":                 "Dyslexia",
    "blind_or_visually_impaired": "Blind or visually impaired",
    "other_neurodivergence":    "Other neurodivergence",
    "specific_learning_disability": "Specific learning disability",
    "communication_difficulties": "Communication difficulties",
    "wheelchair_user":          "Wheelchair user",
    "requires_personal_care":   "Requires personal care",
}

def build_overview(t):
    s = t["students"]
    total = len(s)

    # Species
    species = [
        {"species": sp, "n": int(cnt), "pct": r2(100 * cnt / total)}
        for sp, cnt in s["species"].value_counts().items()
    ]

    # Clans
    clan_rows = (
        s.groupby(["species", "clan"])
         .size()
         .reset_index(name="n")
         .sort_values(["species", "n"], ascending=[True, False])
    )
    clans = [
        {"clan": row.clan, "species": row.species, "n": int(row.n),
         "pct_of_species": r2(100 * row.n / s[s["species"] == row.species].shape[0])}
        for row in clan_rows.itertuples()
    ]

    # Gender
    gender = [
        {"gender": g, "n": int(cnt), "pct": r2(100 * cnt / total)}
        for g, cnt in s["gender"].value_counts().items()
    ]

    # SES (1–8)
    ses = [
        {"rank": int(rank), "n": int(cnt), "pct": r2(100 * cnt / total)}
        for rank, cnt in sorted(s["socio_economic_rank"].value_counts().items())
    ]

    # First-gen
    first_gen_pct = r2(100 * s["first_gen"].sum() / total)

    # Disabilities — count students with any mention of each category
    dis_counts = {label: 0 for label in DISABILITY_GROUPS.values()}
    no_disability = 0
    for d in s["disabilities"].fillna("no_known_disabilities"):
        parts = str(d).split(",")
        if parts == ["no_known_disabilities"]:
            no_disability += 1
        else:
            for p in parts:
                p = p.strip()
                if p in DISABILITY_GROUPS:
                    dis_counts[DISABILITY_GROUPS[p]] += 1
    disabilities = [{"label": "No known disability", "n": no_disability, "pct": r2(100 * no_disability / total)}]
    disabilities += [
        {"label": label, "n": n, "pct": r2(100 * n / total)}
        for label, n in sorted(dis_counts.items(), key=lambda x: -x[1])
        if n > 0
    ]

    # Programmes by faculty — with unique student counts
    prog_full = pd.read_csv(REL / "dim_programmes.csv")
    enroll_counts = (
        t["enrollment"]
        .groupby("programme_code")["student_id"]
        .nunique()
        .to_dict()
    )
    faculties = []
    for faculty, grp in prog_full.groupby("faculty"):
        faculties.append({
            "name": faculty,
            "programme_count": len(grp),
            "programmes": sorted([
                {
                    "code": row.programme_code,
                    "name": row.programme_name,
                    "n_students": int(enroll_counts.get(row.programme_code, 0)),
                }
                for row in grp.itertuples()
            ], key=lambda x: x["name"]),
        })
    faculties.sort(key=lambda x: x["name"])

    # Enrolment by academic year
    enroll = t["enrollment"]
    enrolment_by_year = [
        {"academic_year": ay, "n": int(cnt)}
        for ay, cnt in enroll.groupby("academic_year")["student_id"].nunique().items()
    ]

    return {
        "total_students":    total,
        "species":           species,
        "clans":             clans,
        "gender":            gender,
        "ses":               ses,
        "first_gen_pct":     first_gen_pct,
        "disabilities":      disabilities,
        "faculties":         faculties,
        "enrolment_by_year": enrolment_by_year,
        "academic_years":    sorted(enroll["academic_year"].unique().tolist()),
    }


# ---------------------------------------------------------------------------
# Write
# ---------------------------------------------------------------------------

def write_json(data, filename):
    path = OUT / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, separators=(",", ":"))
    n = len(data) if isinstance(data, list) else "dict"
    kb = path.stat().st_size / 1024
    print(f"  → {filename}: {n} records, {kb:.0f} KB")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("Loading relational tables …")
    t = load()

    print("\nBuilding attainment …")
    att, clans = build_attainment(t)
    write_json(att,   "attainment.json")
    write_json(clans, "clans.json")

    print("Building engagement …")
    write_json(build_engagement(t), "engagement.json")

    print("Building progression …")
    write_json(build_progression(t), "progression.json")

    print("Building NSS …")
    write_json(build_nss(t), "nss.json")

    print("Building enrolment survey …")
    write_json(build_survey(t), "survey.json")

    print("Building graduate outcomes …")
    write_json(build_outcomes(t), "outcomes.json")

    print("Building overview …")
    write_json(build_overview(t), "overview.json")

    print("\nDone. Files written to", OUT)


if __name__ == "__main__":
    main()
