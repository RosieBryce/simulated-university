#!/usr/bin/env python3
"""
Migration: generate complete module_characteristics.csv for all 353 modules.

Values are derived from faculty profile, department, year level, and title keywords.
Run once from project root. Output overwrites config/module_characteristics.csv.
"""

from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CURRICULUM_PATH = PROJECT_ROOT / "Instructions and guides" / "Stonegrove_University_Curriculum.xlsx"
OUT_PATH = PROJECT_ROOT / "config" / "module_characteristics.csv"


def clip(v, lo, hi):
    return max(lo, min(hi, v))


# ---------------------------------------------------------------------------
# Core derivation logic
# ---------------------------------------------------------------------------

def derive_characteristics(module_title: str, year: int, faculty: str, department: str) -> dict:
    t = module_title.lower()
    f = faculty.lower()
    d = department.lower()

    # --- Base values by year ---
    difficulty        = {1: 0.35, 2: 0.55, 3: 0.70}.get(year, 0.50)
    stress            = {1: 0.35, 2: 0.50, 3: 0.65}.get(year, 0.50)
    independent_study = {1: 0.40, 2: 0.55, 3: 0.70}.get(year, 0.50)

    # --- Faculty base profile ---
    if "applied forging" in f:
        practical  = 0.78; social = 0.50; creativity = 0.62; group = 0.48
        atype = "practical"
    elif "hearth and transformation" in f:
        practical  = 0.60; social = 0.78; creativity = 0.68; group = 0.68
        atype = "mixed"
    elif "integrative inquiry" in f:
        practical  = 0.28; social = 0.55; creativity = 0.72; group = 0.48
        independent_study += 0.05
        atype = "essay"
    elif "living lore" in f:
        practical  = 0.38; social = 0.65; creativity = 0.72; group = 0.52
        atype = "essay"
    else:
        practical  = 0.50; social = 0.50; creativity = 0.55; group = 0.50
        atype = "mixed"

    # --- Department refinements ---
    if "forge arts" in d or "metallurgy" in d:
        practical = 0.88; group = 0.38; creativity = 0.68
    elif "food and sustenance" in d:
        practical = 0.82; social = 0.58; group = 0.52
    elif "mechanics and engineering" in d:
        practical = 0.72; difficulty = min(difficulty + 0.05, 0.92)
    elif "stonework" in d or "structural alchemy" in d:
        practical = 0.72; creativity = 0.68
    elif "community labour" in d or "cooperative" in d:
        group = 0.70; social = 0.68
    elif "education" in d or "eldership" in d or "mentoring" in d:
        social = 0.80; group = 0.62
    elif "healing" in d or "embodied knowledge" in d:
        social = 0.72; practical = 0.65; creativity = 0.68
    elif "hospitality" in d or "conflict" in d:
        social = 0.85; group = 0.72
    elif "rites" in d or "rest" in d or "renewal" in d:
        social = 0.72; creativity = 0.72; practical = 0.55
    elif "ecologies of knowledge" in d:
        practical = 0.20; difficulty = max(difficulty, 0.55); independent_study = min(independent_study + 0.08, 0.92)
    elif "learning futures" in d:
        practical = 0.32; social = 0.58
    elif "transdisciplinary" in d:
        practical = 0.50; creativity = 0.78
    elif "language and symbol" in d:
        practical = 0.35; creativity = 0.72; social = 0.60
    elif "oral histories" in d or "memorycraft" in d:
        practical = 0.45; creativity = 0.68; social = 0.72
    elif "philosophy" in d or "ethics" in d:
        practical = 0.15; difficulty = max(difficulty, 0.58); independent_study = min(independent_study + 0.08, 0.92)
    elif "political myth" in d or "governance" in d:
        practical = 0.28; social = 0.65

    # --- Title keyword: assessment type ---
    if any(w in t for w in ["capstone", "dissertation", "thesis"]):
        atype = "project"
        difficulty        = max(difficulty, 0.80)
        stress            = max(stress, 0.75)
        independent_study = max(independent_study, 0.82)
    elif any(w in t for w in ["studio", "portfolio", "prototype", "curate a", "construct a",
                               "design and build", "develop a", "build a", "build and test",
                               "design a", "design an", "re-map", "perform or"]):
        atype = "project"
    elif any(w in t for w in ["lab", "practicum", "practical", "hands-on", "embodied skills lab",
                               "fieldwork"]):
        if "applied forging" in f or "healing" in d or "food" in d:
            atype = "practical"
        else:
            atype = "mixed"
    elif any(w in t for w in ["history of", "histories and", "philosophy of", "theory of",
                               "theories of", "ethics of", "ethics and", "epistemolog",
                               "comparative", "policy,", "power and", "power as", "what is a",
                               "what counts"]):
        if atype != "practical":
            atype = "essay"

    # --- Title keyword: difficulty ---
    if any(w in t for w in ["introduction to", "foundations of", "fundamentals of",
                              "foundations in", "what is a", "what counts", "principles of"]):
        difficulty = difficulty * 0.82
        stress     = stress * 0.82
    if any(w in t for w in ["advanced", "complex", "specialist", "beyond", "futures of",
                              "comparative", "reconstructing", "speculative"]):
        difficulty = min(difficulty + 0.08, 0.92)

    # --- Title keyword: social / group ---
    if any(w in t for w in ["collaborative", "collective", "community", "cooperative", "mutual",
                              "shared", "seminar", "circle", "circles", "together", "multi-"]):
        social = min(social + 0.08, 0.92)
        group  = min(group  + 0.08, 0.88)
    if any(w in t for w in ["dialogue", "mediation", "facilitat", "listening", "interview",
                              "inter-species", "across difference"]):
        social = min(social + 0.06, 0.92)

    # --- Title keyword: independent study ---
    if any(w in t for w in ["independent", "self-directed", "reflective", "journaling",
                              "personal", "solo", "individual"]):
        independent_study = min(independent_study + 0.10, 0.90)
        group             = max(group - 0.10, 0.12)

    # --- Title keyword: creativity ---
    if any(w in t for w in ["creative", "design", "artistic", "aesthetic", "making",
                              "craft", "imagine", "invent", "speculative", "reimagin"]):
        creativity = min(creativity + 0.06, 0.92)

    # --- Description ---
    description = _make_description(module_title, department, year, atype)

    return {
        "difficulty_level":             round(clip(difficulty,        0.20, 0.92), 2),
        "social_requirements":          round(clip(social,            0.15, 0.92), 2),
        "creativity_requirements":      round(clip(creativity,        0.20, 0.92), 2),
        "practical_theoretical_balance":round(clip(practical,         0.12, 0.92), 2),
        "stress_level":                 round(clip(stress,            0.20, 0.88), 2),
        "group_work_intensity":         round(clip(group,             0.12, 0.90), 2),
        "independent_study_requirement":round(clip(independent_study, 0.25, 0.92), 2),
        "assessment_type":              atype,
        "description":                  description,
    }


def _make_description(title: str, department: str, year: int, atype: str) -> str:
    t = title.lower()
    year_label = {1: "Foundation", 2: "Intermediate", 3: "Advanced"}.get(year, "Core")
    if any(w in t for w in ["capstone", "dissertation", "thesis"]):
        return f"Final-year integrative project in {department}: {title.rstrip('.')}."
    if any(w in t for w in ["introduction to", "foundations of", "fundamentals of", "foundations in"]):
        return f"Introductory {department.lower()} module establishing core concepts and practices."
    return f"{year_label} module in {department}: {title.rstrip('.')}."


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # Load curriculum
    xl = pd.read_excel(CURRICULUM_PATH, sheet_name="Modules")
    progs = pd.read_excel(CURRICULUM_PATH, sheet_name="Programmes")
    mods = xl.merge(progs[["Programme code", "Faculty", "Department"]], on="Programme code", how="left")

    rows = []
    for _, r in mods.iterrows():
        chars = derive_characteristics(
            module_title=str(r["Module Title"]),
            year=int(r["Year"]),
            faculty=str(r["Faculty"]),
            department=str(r["Department"]),
        )
        row = {
            "module_code":  str(r["Module Code"]),
            "module_title": str(r["Module Title"]),
            "programme_code": str(r["Programme code"]),
            "year": int(r["Year"]),
            **chars,
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    col_order = [
        "module_code", "module_title", "programme_code", "year",
        "difficulty_level", "social_requirements", "creativity_requirements",
        "practical_theoretical_balance", "stress_level", "group_work_intensity",
        "independent_study_requirement", "assessment_type", "description",
    ]
    df[col_order].to_csv(OUT_PATH, index=False)

    print(f"Written: {OUT_PATH}")
    print(f"  {len(df)} modules")
    print()
    print("Assessment type breakdown:")
    print(df["assessment_type"].value_counts().to_string())
    print()
    print("Difficulty by year:")
    print(df.groupby("year")["difficulty_level"].describe()[["mean","min","max"]].round(2).to_string())
    print()
    print("Practical balance by faculty:")
    xl2 = xl.merge(progs[["Programme code","Faculty"]], on="Programme code", how="left")
    df2 = df.copy()
    df2["Faculty"] = xl2["Faculty"].values
    print(df2.groupby("Faculty")["practical_theoretical_balance"].mean().round(2).to_string())


if __name__ == "__main__":
    main()
