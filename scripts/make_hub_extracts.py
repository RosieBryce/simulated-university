#!/usr/bin/env python3
"""
Generate the Stonegrove Hub's Planning and Insight data extracts and the
named-figure dictionary (values.yaml) from data/relational/.

Called at the end of core_systems/build_relational_outputs.py, so a pipeline
run with a new seed regenerates the Planning and Insight library and every
figure quoted in an in-world Hub document.

Writes:
    hub/source/Planning and Insight/Data Extracts/1052-53/*.csv and *.xlsx
    hub/source/values.yaml

The extracts are small (a few thousand rows at most) and cover the Faculty
of Health and Education only. Nothing here copies the full dataset.

Run from the project root:
    python scripts/make_hub_extracts.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REL = PROJECT_ROOT / "data" / "relational"
HUB_SOURCE = PROJECT_ROOT / "hub" / "source"
EXTRACT_DIR = HUB_SOURCE / "Planning and Insight" / "Data Extracts" / "1052-53"
VALUES_PATH = HUB_SOURCE / "values.yaml"

FACULTY = "Health & Education"
SNAPSHOT_YEAR = "1052-53"
YEARS = ["1048-49", "1049-50", "1050-51", "1051-52", "1052-53"]
GOOD = {"First", "2:1"}

# In-world "NSS 1052" means the survey of finalists in academic year 1051-52,
# published August 1052. So the in-world year label is the END of the
# academic year.
def inworld_year(academic_year: str) -> int:
    return int(academic_year[:4]) + 1


# ----------------------------------------------------------------------
def load() -> dict[str, pd.DataFrame]:
    def rd(name: str) -> pd.DataFrame:
        return pd.read_csv(REL / f"{name}.csv")
    t = {k: rd(k) for k in ["dim_students", "dim_programmes", "fact_enrollment",
                            "fact_good_honours", "fact_nss_responses", "fact_progression",
                            "fact_assessment"]}
    prog = t["dim_programmes"]
    t["he_programmes"] = prog[prog["faculty"] == FACULTY].copy()
    return t


def pct(x: float) -> float | None:
    return None if pd.isna(x) else round(float(x) * 100, 1)


def mean1(x: float) -> float | None:
    return None if pd.isna(x) else round(float(x), 2)


# ----------------------------------------------------------------------
def build_extracts(t: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    hep = t["he_programmes"][["programme_code", "programme_name", "department"]]
    students = t["dim_students"][["student_id", "species", "clan", "gender", "socio_economic_rank", "first_gen", "disabilities"]]

    # Enrolments, snapshot year, by programme, year of study and species
    en = t["fact_enrollment"].merge(hep, on="programme_code")
    en_snap = en[en["academic_year"] == SNAPSHOT_YEAR].merge(students[["student_id", "species"]], on="student_id")
    enrolments = (en_snap.groupby(["department", "programme_name", "programme_year", "species"])
                  .size().rename("students").reset_index())

    # Good honours by graduating year, programme and species (five years)
    gh = t["fact_good_honours"].merge(hep, on="programme_code").merge(students, on="student_id")
    gh = gh[gh["academic_year_graduated"].isin(YEARS)].copy()
    gh["good_honours"] = gh["degree_classification"].isin(GOOD)
    good_by_prog = (gh.groupby(["academic_year_graduated", "department", "programme_name", "species"])
                    .agg(graduates=("student_id", "size"), good_honours=("good_honours", "sum"))
                    .reset_index())
    good_by_prog["good_honours_rate"] = (good_by_prog["good_honours"] / good_by_prog["graduates"] * 100).round(1)

    # Good honours individual-level, anonymised (student_id only), for the analysis exercise
    gh_rows = gh[["student_id", "academic_year_graduated", "programme_name", "species", "clan",
                  "gender", "socio_economic_rank", "first_gen", "disabilities",
                  "degree_classification", "degree_weighted_avg"]].sort_values(["academic_year_graduated", "student_id"])

    # NSS by programme, year and theme (respondents only), five years
    nss = t["fact_nss_responses"].merge(hep, on="programme_code")
    nss = nss[(nss["survey_responded"] == True) & (nss["academic_year"].isin(YEARS))]
    themes = ["teaching_quality", "learning_opportunities", "assessment_feedback", "academic_support",
              "organisation_management", "learning_resources", "student_voice", "overall_satisfaction"]
    nss_by_prog = (nss.groupby(["academic_year", "department", "programme_name"])
                   .agg(respondents=("student_id", "size"), **{th: (th, "mean") for th in themes})
                   .reset_index())
    nss_by_prog[themes] = nss_by_prog[themes].round(2)
    nss_by_prog.insert(1, "nss_year", nss_by_prog["academic_year"].map(inworld_year))

    # Progression by programme and year of study, snapshot year
    pg = (t["fact_progression"]
          .merge(en[["student_id", "academic_year", "programme_code", "programme_year"]], on=["student_id", "academic_year"])
          .merge(hep, on="programme_code"))
    pg_snap = pg[pg["academic_year"] == SNAPSHOT_YEAR]
    progression = (pg_snap.groupby(["department", "programme_name", "programme_year", "year_outcome"])
                   .size().rename("students").reset_index())

    # Assessment summary: mean FINAL mark by programme and species, snapshot year
    asm = t["fact_assessment"]
    asm = asm[(asm["academic_year"] == SNAPSHOT_YEAR) & (asm["component_code"] == "FINAL")]
    asm = (asm.merge(en_snap[["student_id", "programme_name", "department"]].drop_duplicates(), on="student_id")
              .merge(students[["student_id", "species"]], on="student_id"))
    assessment = (asm.groupby(["department", "programme_name", "species"])
                  .agg(assessments=("assessment_mark", "size"), mean_mark=("assessment_mark", "mean"))
                  .reset_index())
    assessment["mean_mark"] = assessment["mean_mark"].round(1)

    return {
        "he_enrolments_1052-53": enrolments,
        "he_good_honours_by_programme_species_5yr": good_by_prog,
        "he_graduates_individual_anonymised_5yr": gh_rows,
        "he_nss_by_programme_theme_5yr": nss_by_prog,
        "he_progression_1052-53": progression,
        "he_assessment_summary_1052-53": assessment,
    }


# ----------------------------------------------------------------------
def build_values(t: dict[str, pd.DataFrame], ex: dict[str, pd.DataFrame]) -> dict:
    v: dict = {}
    hep = t["he_programmes"]
    students = t["dim_students"][["student_id", "species"]]

    # Awarding gap, faculty level, by in-world graduating year
    gh = t["fact_good_honours"].merge(hep, on="programme_code").merge(students, on="student_id")
    gh["good"] = gh["degree_classification"].isin(GOOD)
    for ay in YEARS:
        y = inworld_year(ay)
        sub = gh[gh["academic_year_graduated"] == ay]
        rate = sub.groupby("species")["good"].mean()
        elf, dwarf = rate.get("Elf", float("nan")), rate.get("Dwarf", float("nan"))
        v[f"he_good_degree_rate_elf_{y}"] = pct(elf)
        v[f"he_good_degree_rate_dwarf_{y}"] = pct(dwarf)
        v[f"he_good_degree_gap_{y}"] = None if pd.isna(elf) or pd.isna(dwarf) else round(float(elf - dwarf) * 100, 1)
        v[f"he_graduates_{y}"] = int(len(sub))
    # Programme-level, snapshot graduating year, where graduates exist
    sub = gh[gh["academic_year_graduated"] == SNAPSHOT_YEAR]
    for code, name in zip(hep["programme_code"], hep["programme_name"]):
        slug = name.lower().replace(" and ", "_").replace(" ", "_").replace("-", "_")
        s = sub[sub["programme_code"] == code]
        v[f"{slug}_graduates_1053"] = int(len(s))
        rate = s.groupby("species")["good"].mean() if len(s) else pd.Series(dtype=float)
        v[f"{slug}_good_degree_rate_elf_1053"] = pct(rate.get("Elf", float("nan")))
        v[f"{slug}_good_degree_rate_dwarf_1053"] = pct(rate.get("Dwarf", float("nan")))

    # NSS, faculty and named programmes, by in-world NSS year
    nss = t["fact_nss_responses"].merge(hep, on="programme_code")
    nss = nss[nss["survey_responded"] == True]
    for ay in YEARS:
        y = inworld_year(ay)
        sub = nss[nss["academic_year"] == ay]
        v[f"he_nss_overall_{y}"] = mean1(sub["overall_satisfaction"].mean())
        v[f"he_nss_assessment_feedback_{y}"] = mean1(sub["assessment_feedback"].mean())
        v[f"he_nss_respondents_{y}"] = int(len(sub))
        for slug, name in [("ot", "Occupational Therapy"), ("swe", "Somatic Wellbeing Enquiry"),
                           ("pharmacy", "Pharmacy"), ("physio", "Physiotherapy"), ("social_work", "Social Work")]:
            p = sub[sub["programme_name"] == name]
            v[f"{slug}_nss_overall_{y}"] = mean1(p["overall_satisfaction"].mean())
            v[f"{slug}_nss_assessment_feedback_{y}"] = mean1(p["assessment_feedback"].mean())
        for dept in ("Education", "Health"):
            d = sub[sub["department"] == dept]
            v[f"{dept.lower()}_nss_overall_{y}"] = mean1(d["overall_satisfaction"].mean())
            v[f"{dept.lower()}_nss_assessment_feedback_{y}"] = mean1(d["assessment_feedback"].mean())

    # Enrolments
    en = t["fact_enrollment"].merge(hep, on="programme_code")
    snap = en[en["academic_year"] == SNAPSHOT_YEAR]
    v["he_enrolled_1052"] = int(len(snap))
    v["health_enrolled_1052"] = int((snap["department"] == "Health").sum())
    v["education_enrolled_1052"] = int((snap["department"] == "Education").sum())
    v["nursing_enrolled_1052"] = int((snap["programme_name"] == "Nursing and Care").sum())
    v["nursing_year1_1052"] = int(((snap["programme_name"] == "Nursing and Care") & (snap["programme_year"] == 1)).sum())
    v["nursing_year2_1052"] = int(((snap["programme_name"] == "Nursing and Care") & (snap["programme_year"] == 2)).sum())
    v["nursing_year3_1052"] = int(((snap["programme_name"] == "Nursing and Care") & (snap["programme_year"] == 3)).sum())
    v["ot_enrolled_1052"] = int((snap["programme_name"] == "Occupational Therapy").sum())

    # Progression, Nursing and Care, snapshot year
    pg = ex["he_progression_1052-53"]
    nc = pg[pg["programme_name"] == "Nursing and Care"]
    tot = int(nc["students"].sum())
    fails = int(nc[nc["year_outcome"] == "fail"]["students"].sum())
    v["nursing_fail_rate_1052"] = None if not tot else round(float(fails) / tot * 100, 1)

    v["_generated_from"] = "data/relational via scripts/make_hub_extracts.py"
    v["_snapshot_academic_year"] = SNAPSHOT_YEAR
    v["_note"] = ("Keys ending _NNNN use the in-world year: for NSS and graduation that is the end of the "
                  "academic year (1051-52 -> 1052). null means the data has no rows for it; documents must "
                  "not quote a null key.")
    return v


# ----------------------------------------------------------------------
def write_extracts(ex: dict[str, pd.DataFrame]) -> None:
    EXTRACT_DIR.mkdir(parents=True, exist_ok=True)
    for name, df in ex.items():
        csv_path = EXTRACT_DIR / f"{name}.csv"
        df.to_csv(csv_path, index=False)
        print(f"  {csv_path.relative_to(PROJECT_ROOT)}  {len(df):,} rows")
    # One workbook with every summary table (not the individual-level one)
    xlsx_path = EXTRACT_DIR / "he_summary_tables_1052-53.xlsx"
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as xw:
        for name, df in ex.items():
            if "individual" in name:
                continue
            sheet = name.replace("he_", "")[:31]
            df.to_excel(xw, sheet_name=sheet, index=False)
    print(f"  {xlsx_path.relative_to(PROJECT_ROOT)}")

    # In-world sources note. Markdown source; the Hub build renders it to docx.
    note = EXTRACT_DIR / "Data sources and definitions.md"
    note.write_text(
        "---\n"
        "title: Data sources and definitions\n"
        "format: docx\n"
        "author: erra-measurine\n"
        "created: 1052-10-01\n"
        "modified: 1053-03-31\n"
        "label: Internal\n"
        "sensitive: false\n"
        "site: planning\n"
        "library: pi-extracts\n"
        "path: 1052-53\n"
        "storylines: [awarding-gap, nss-dip]\n"
        "skills: [2]\n"
        "generated: true\n"
        "---\n\n"
        "# Data sources and definitions\n\n"
        "Extracts in this folder are cut from the institutional student record for the Faculty of "
        "Health and Education. They are refreshed when the record is rebuilt. Do not edit them in place; "
        "ask Planning and Insight for a new cut.\n\n"
        "## Files\n\n"
        "| File | Grain | Notes |\n|---|---|---|\n"
        "| he_enrolments_1052-53.csv | programme, year of study, species | Headcount at census |\n"
        "| he_good_honours_by_programme_species_5yr.csv | graduating year, programme, species | Good honours = First or 2:1 |\n"
        "| he_graduates_individual_anonymised_5yr.csv | one row per graduate | Student ID only. Confidential if joined to names. |\n"
        "| he_nss_by_programme_theme_5yr.csv | NSS year, programme | Respondents only. Means on a 1 to 5 scale. |\n"
        "| he_progression_1052-53.csv | programme, year of study, outcome | Pass or fail at year end |\n"
        "| he_assessment_summary_1052-53.csv | programme, species | Mean final-component mark |\n"
        "| he_summary_tables_1052-53.xlsx | all of the above | One sheet per table |\n\n"
        "## Definitions\n\n"
        "- **Good honours**: First or Upper Second class degree.\n"
        "- **Awarding gap**: good honours rate for Elf graduates minus the rate for Dwarf graduates, in percentage points.\n"
        "- **NSS year**: the year the survey is published. NSS 1052 surveyed finalists in 1051-52.\n"
        "- **Finalists**: students in Year 3. All twelve of the Faculty's programmes are three-year honours "
        "programmes, so every programme has finalists in the NSS and graduates with a classification.\n"
        "- **Species** is recorded as declared at enrolment.\n\n"
        "## Caveats\n\n"
        "Programme-level figures with fewer than 20 graduates should not be reported externally. "
        "The full institutional dataset, for all faculties, is published for research use; see the "
        "University's open data page.\n",
        encoding="utf-8",
    )
    print(f"  {note.relative_to(PROJECT_ROOT)}")


def main() -> int:
    print("make_hub_extracts: reading data/relational ...")
    t = load()
    ex = build_extracts(t)
    print("Writing extracts:")
    write_extracts(ex)
    values = build_values(t, ex)
    HUB_SOURCE.mkdir(parents=True, exist_ok=True)
    VALUES_PATH.write_text(yaml.safe_dump(values, sort_keys=True, allow_unicode=True, width=100), encoding="utf-8")
    nulls = sorted(k for k, val in values.items() if val is None)
    print(f"  {VALUES_PATH.relative_to(PROJECT_ROOT)}  {len(values)} keys, {len(nulls)} null")
    if nulls:
        print("  null keys (documents must not quote these): " + ", ".join(nulls[:12]) + (" ..." if len(nulls) > 12 else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
