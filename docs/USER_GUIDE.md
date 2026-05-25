# Stonegrove University – User Guide

How to run the simulation pipeline and work with the generated data.

---

## Prerequisites

**Python 3.10+** with:

```bash
pip install -r requirements.txt
```

All commands run from the **project root** (`simulated-university/`).

---

## Running the Pipeline

```bash
python run_longitudinal_pipeline.py
```

Runs the full longitudinal simulation: 7 academic years (1046-47 to 1052-53), 5,000 new students per year. Re-enrols continuing students each year based on prior-year progression outcomes. Automatically calls `build_relational_outputs.py` at the end.

**Runtime: ~30–45 minutes** (dominated by engagement and assessment generation across ~89,000 student-years).

After the pipeline, regenerate the site summary CSVs:

```bash
python scripts/aggregate_gap.py
python scripts/aggregate_engagement.py
```

Validate outputs:

```bash
python metaanalysis/validate_outputs.py
```

---

## Output Files

The pipeline writes raw outputs to `data/` and clean relational tables to `data/relational/`.

**Use `data/relational/` for analysis** — the raw `data/stonegrove_*.csv` files are intermediates.

### Dimensions (one row per entity)

| File | Description | Rows |
|------|-------------|------|
| `dim_students.csv` | Species, clan, gender, age, education, SES, disability status, `first_gen`. One row per student. | ~35,000 |
| `dim_programmes.csv` | 55 programmes across 5 faculties: name, faculty, department. | 55 |
| `dim_modules.csv` | 333 modules: title, programme, year, semester, assessment type. | 333 |
| `dim_academic_years.csv` | Academic year calendar with semester and assessment dates. | 7 |

### Facts (one row per event)

| File | Description | Rows |
|------|-------------|------|
| `fact_enrollment.csv` | Programme, year of study, module allocation, enrolment status. | ~89,000 |
| `fact_weekly_engagement_YYYY-YY.csv` | Attendance, participation, academic/social engagement, VLE metrics. One file per academic year. | ~400,000/yr |
| `fact_assessment.csv` | MIDTERM and FINAL component marks per module per student, with assessment date and weight (50/50). | ~468,000 |
| `fact_progression.csv` | Year outcome, modules passed, avg mark, next-year status. | ~58,000 |
| `fact_enrolment_survey.csv` | Annual survey: career thinking, belonging, self-efficacy, support satisfaction. ~82% response. | ~89,000 |
| `fact_good_honours.csv` | Final degree classification and weighted average mark for every graduate. | ~6,100 |
| `fact_graduate_outcomes.csv` | Post-graduation survey: employment, salary band, professional level. ~70% response rate. | ~6,100 |
| `fact_nss_responses.csv` | NSS-style satisfaction scores for all Yr3 students. ~68% response rate. | ~23,000 |

Full column definitions: `docs/SCHEMA.md`

---

## Reading the Data

### Python (pandas)

```python
import pandas as pd

RELATIONAL = "data/relational"

# Dimensions
students    = pd.read_csv(f"{RELATIONAL}/dim_students.csv")
programmes  = pd.read_csv(f"{RELATIONAL}/dim_programmes.csv")
modules     = pd.read_csv(f"{RELATIONAL}/dim_modules.csv")

# Facts
enrollment  = pd.read_csv(f"{RELATIONAL}/fact_enrollment.csv")
assessment  = pd.read_csv(f"{RELATIONAL}/fact_assessment.csv")
progression = pd.read_csv(f"{RELATIONAL}/fact_progression.csv")
nss         = pd.read_csv(f"{RELATIONAL}/fact_nss_responses.csv")
honours     = pd.read_csv(f"{RELATIONAL}/fact_good_honours.csv")
outcomes    = pd.read_csv(f"{RELATIONAL}/fact_graduate_outcomes.csv")
survey      = pd.read_csv(f"{RELATIONAL}/fact_enrolment_survey.csv")

# Weekly engagement — one file per academic year
import glob
eng_files = sorted(glob.glob(f"{RELATIONAL}/fact_weekly_engagement_*.csv"))
engagement = pd.concat([pd.read_csv(f) for f in eng_files], ignore_index=True)
```

### Joining tables

All tables join on `student_id`. Most also join on `academic_year`.

```python
# Assessment marks with species and SES
marks_with_demo = assessment.merge(
    students[["student_id", "species", "clan", "socio_economic_rank"]],
    on="student_id", how="left"
)

# Awarding gap: good degree rate by species
grads_with_species = honours.merge(students[["student_id", "species"]], on="student_id")
grads_with_species["good_degree"] = grads_with_species["degree_classification"].isin(["First", "2:1"])
grads_with_species.groupby("species")["good_degree"].mean()

# NSS scores — respondents only
nss_respondents = nss[nss["survey_responded"] == True]
nss_respondents.groupby(nss_respondents["academic_year"])["overall_satisfaction"].mean()
```

### Key columns

- **`student_id`** — persistent across all tables and all years
- **`academic_year`** — e.g. `"1046-47"`; join key for time-varying facts
- **`assessment_weight`** — always `0.5` in `fact_assessment`; both components carry equal weight
- **`component_code`** — `"MIDTERM"` or `"FINAL"` in `fact_assessment`
- **`survey_responded`** — boolean in NSS and graduate outcomes; filter to `True` before analysing scores
- **`programme_year`** — 1, 2, or 3 within the degree

---

## Key Design Decisions

- **No direct species/clan modifier on marks.** The ~18pp Elf–Dwarf good degree gap emerges from SES, prior education, and disability distributions only.
- **Gender gap is flat by design.**
- **first_gen** — first-generation student flag (~32% of cohort); used in enrolment survey self-efficacy. Backlog: wire into progression and assessment.
- **Assessment marks are not pre-combined.** `fact_assessment` gives you the raw MIDTERM and FINAL marks (equal weight); computing a module average is part of the analysis task.
- **Degree classifications live in `fact_good_honours`**, not in `fact_assessment` — computed internally from Y2/Y3 marks on a 1/3:2/3 weighting.
- **Survey non-respondents are present** in NSS and graduate outcomes with `survey_responded=False` and null score columns — the count of eligible students is known.

---

## Reproducibility

All systems accept a `seed` parameter. The top-level seed is set in `run_longitudinal_pipeline.py`:

```python
BASE_SEED = 42          # global seed
seed = BASE_SEED + i * 1000  # per-year seed (i = year index 0–6)
```

Running with the same seed produces the same dataset. Metadata (seed, git commit, timestamp, runtime) is written to `data/metadata.json` after each run.

---

## Extending the Pipeline

- **New student trait**: add a `sample_*` function in `student_generation_pipeline.py` and add to the student dict. Wire into downstream systems as needed (see `docs/BACKLOG.md` for the `first_gen` example).
- **New config**: YAML for hierarchical data (personality ranges, progression rules), CSV for tabular data (programme/module characteristics).
- **New fact table**: create a new system class with a `generate_*` method, wire into `run_year()` in `run_longitudinal_pipeline.py`, add a `build_fact_*` function in `build_relational_outputs.py`.
- **Curriculum changes**: edit `curriculum-and-lore/Stonegrove_University_Curriculum.xlsx` (canonical source), regenerate `config/programme_characteristics.csv` and `config/module_characteristics.csv`, re-run the pipeline.
