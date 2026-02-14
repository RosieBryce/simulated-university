# Stonegrove University – User Guide

How to run the simulation pipeline and work with the generated data.

---

## Prerequisites

**Python 3.8+** with:

```bash
pip install pandas numpy matplotlib seaborn scipy openpyxl xlrd PyYAML
```

All commands below are run from the **project root** (`simulated-university/`).

---

## Running the Pipeline

### Full pipeline (single year, 500 students)

```bash
python run_pipeline.py
```

Runs all 5 steps in order:

### Longitudinal pipeline (5 cohorts × 7 years)

```bash
python run_longitudinal_pipeline.py
```

Runs the full longitudinal simulation: academic years 1046-47 to 1052-53, with new cohorts each year and progression/repeat/withdrawal. Outputs `stonegrove_enrollment.csv` (per DESIGN) and `data/metadata.json`.

**Single-year outputs:**

1. **Student generation** → `data/stonegrove_individual_students.csv`
2. **Program enrollment** → `data/stonegrove_enrolled_students.csv`
3. **Engagement** → `data/stonegrove_weekly_engagement.csv`, `data/stonegrove_semester_engagement.csv`
4. **Assessment** → `data/stonegrove_assessment_events.csv`
5. **Progression** → `data/stonegrove_progression_outcomes.csv`

Each step overwrites its output files. A full run takes about 30–60 seconds for 500 students.

### Individual steps

```bash
python core_systems/student_generation_pipeline.py
python core_systems/program_enrollment_system.py
python core_systems/engagement_system.py
python core_systems/assessment_system.py
python core_systems/progression_system.py
```

**Order matters.** Each step reads from the previous outputs. Run in sequence.

---

## Output Files

All outputs are written to `data/`.

| File | Description |
|------|--------------|
| `stonegrove_individual_students.csv` | Student demographics, personality, motivation (one row per student) |
| `stonegrove_enrolled_students.csv` | Program enrollment and Year 1 modules (merged with student data) |
| `stonegrove_weekly_engagement.csv` | Weekly engagement metrics per student per module |
| `stonegrove_semester_engagement.csv` | Semester summaries (engagement trends, risk factors) |
| `stonegrove_assessment_events.csv` | End-of-module marks and grades |
| `stonegrove_progression_outcomes.csv` | Year outcomes (pass/fail) and next-year status (progress/repeat/withdraw) |
| `stonegrove_enrollment.csv` | Longitudinal output: one row per student per academic year (with `status`, `status_change_at`, `programme_year`) |
| `data/metadata.json` | Version, seed, timestamp, cohort info (longitudinal runs only) |

Full column definitions: `docs/SCHEMA.md`

---

## Reading the Data

### Python (pandas)

```python
import pandas as pd

# Students
students = pd.read_csv("data/stonegrove_individual_students.csv")

# Enrolled (includes program, modules, affinity)
enrolled = pd.read_csv("data/stonegrove_enrolled_students.csv")

# Join students + enrollment (enrolled already has student cols)
# Use student_id as key
merged = enrolled  # already merged in pipeline

# Assessment marks
assessments = pd.read_csv("data/stonegrove_assessment_events.csv")

# Progression outcomes
progression = pd.read_csv("data/stonegrove_progression_outcomes.csv")
```

### Joining tables

Use `student_id` to link records:

```python
# Add progression status to enrolled students
enrolled = pd.read_csv("data/stonegrove_enrolled_students.csv")
prog = pd.read_csv("data/stonegrove_progression_outcomes.csv")
enrolled_with_status = enrolled.merge(
    prog[["student_id", "year_outcome", "status", "avg_mark"]],
    on="student_id",
    how="left"
)

# Average mark by species
assessments = pd.read_csv("data/stonegrove_assessment_events.csv")
enrolled = pd.read_csv("data/stonegrove_enrolled_students.csv")
combined = assessments.merge(enrolled[["student_id", "species", "clan"]], on="student_id", how="left")
combined.groupby("species")["assessment_mark"].mean()
```

### Excel / R / other tools

Open the CSVs directly. All files use standard CSV (comma-separated, UTF-8).  
Module lists may contain quoted commas (e.g. `"Module A, Part 1"`)—use a proper CSV parser.

---

## Key Columns

- **`student_id`**: Persistent ID across all tables
- **`academic_year`**: Calendar year (e.g. `"1046-47"`). Currently Year 1 only; multi-year coming.
- **`species`**, **`clan`**, **`gender`**: Demographics
- **`refined_*`**: Personality traits (0–1)
- **`motivation_*`**: Motivation dimensions (0–1)
- **`assessment_mark`**: Module mark (0–100); **`grade`**: First, 2:1, 2:2, Third, Fail
- **`status`** (progression): `enrolled` (progressed), `repeating`, `withdrawn`
- **`year_outcome`** (progression): `pass` or `fail`

---

## Configuration

Edit config files to change behaviour:

| Config | Purpose |
|--------|---------|
| `config/clan_personality_specifications.yaml` | Clan personality ranges, disability tendencies |
| `config/clan_program_affinities.yaml` | Clan–program affinity scores |
| `config/disability_distribution.yaml` | Disability prevalence by species |
| `config/year_progression_rules.yaml` | Pass threshold, base progression/repeat/withdrawal rates, modifiers |
| `config/module_characteristics.csv` | Module difficulty, assessment type |

After changing config, re-run the full pipeline to regenerate data.

---

## Visualizations

Optional analysis scripts:

```bash
python archive_population_model/enrollment_visualization.py   # Writes to visualizations/
python metaanalysis/engagement_visualization.py
python metaanalysis/assessment_visualization.py
```

---

## Reproducibility

The pipeline uses a fixed random seed (42 by default). Same code + config + seed → same output.

---

## Further reading

- **`docs/DESIGN.md`** – Architecture and longitudinal flow
- **`docs/SCHEMA.md`** – Full column definitions
- **`docs/CALCULATIONS.md`** – How marks, engagement, progression are computed
- **`docs/PROJECT_SUMMARY.md`** – Project status and next steps
