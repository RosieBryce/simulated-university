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

**Runtime: ~2 hours** (dominated by engagement and assessment generation across ~89,000 student-years).

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
| `dim_students.csv` | Species, clan, personality, motivation, SES, disabilities, `first_gen`. One row per student. | ~35,000 |
| `dim_programmes.csv` | 55 programmes across 5 faculties: difficulty, career prospects, social intensity. | 55 |
| `dim_modules.csv` | 333 modules: difficulty, assessment type, stress level, semester, programme linkage. | 333 |
| `dim_academic_years.csv` | Academic year calendar with semester and assessment dates. | 7 |

### Facts (one row per event)

| File | Description | Rows |
|------|-------------|------|
| `fact_enrollment.csv` | Programme, year of study, module allocation, enrolment status. | ~89,000 |
| `fact_weekly_engagement_YYYY-YY.csv` | Attendance, participation, engagement, stress, VLE metrics. One per academic year. | ~400,000/yr |
| `fact_assessment.csv` | MIDTERM + FINAL marks per module per student. `combined_mark` on FINAL rows. | ~468,000 |
| `fact_progression.csv` | Year outcome, modules passed, avg mark, next-year status. | ~58,000 |
| `fact_enrolment_survey.csv` | Annual survey: career thinking, belonging, self-efficacy, support satisfaction. ~82% response. | ~89,000 |
| `fact_graduate_outcomes.csv` | Degree classification, employment sector, salary band. ~70% survey response. | ~19,500 |
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
finals = assessment[assessment["component_code"] == "FINAL"]
grads  = outcomes[outcomes["survey_responded"] == True]
grads_with_species = grads.merge(students[["student_id", "species"]], on="student_id")
grads_with_species["good_degree"] = grads_with_species["degree_classification"].isin(["First", "2:1"])
grads_with_species.groupby("species")["good_degree"].mean()

# NSS scores — respondents only
nss_respondents = nss[nss["survey_responded"] == True]
nss_respondents.groupby(nss_respondents["academic_year"])["overall_satisfaction"].mean()
```

### Key columns

- **`student_id`** — persistent across all tables and all years
- **`academic_year`** — e.g. `"1046-47"`; join key for time-varying facts
- **`combined_mark`** — on FINAL rows in `fact_assessment`; use this for analysis (not `assessment_mark`)
- **`survey_responded`** — boolean in NSS and graduate outcomes; filter to `True` before analysing scores
- **`component_code`** — `"MIDTERM"` or `"FINAL"` in `fact_assessment`; progression uses FINAL rows only
- **`programme_year`** — 1, 2, or 3 within the degree

---

## Key Design Decisions

- **No direct species/clan modifier on marks.** The ~18pp Elf–Dwarf good degree gap emerges from SES, prior education, and disability distributions only.
- **Gender gap is flat by design.**
- **first_gen** — first-generation student flag (~32% of cohort); used in enrolment survey self-efficacy. Backlog: wire into progression and assessment.
- **`combined_mark`** is the definitive mark. Progression and degree classification use FINAL rows with `combined_mark = 0.4 × MIDTERM + 0.6 × FINAL`.
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
