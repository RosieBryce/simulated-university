# Stonegrove University — Synthetic Higher Education Dataset

A synthetic data generator for a fictional fantasy university, producing realistic UK-style student lifecycle data for use in data analysis teaching, education research, and awarding gap investigation.

Stonegrove University is set at the meeting point of ancient forest and mountain. Its students are Dwarves and Elves, sorted into 14 clans, studying across 44 programmes in 4 faculties. The fantasy setting sidesteps privacy concerns entirely while preserving the structural patterns that make real higher education data interesting: awarding gaps, engagement arcs, progression risk, NSS variation, and graduate outcomes.

## What's in the dataset

A full relational schema across 10 tables — 4 dimension tables and 6 fact tables — covering 7 academic years with 5,000 new students enrolling each year.

| Table | Description | ~Rows |
|---|---|---|
| `dim_students` | Species, clan, Big Five personality, 8 motivation dimensions, disability, SES, prior qualifications | 35,000 |
| `dim_programmes` | 44 programmes: difficulty, social intensity, career prospects, creativity, research intensity | 44 |
| `dim_modules` | 353 modules: difficulty, assessment type, stress, group work, semester | 353 |
| `dim_academic_years` | Academic year calendar with semester and assessment dates | 7 |
| `fact_enrollment` | Programme, year of study, module allocation, enrolment status | 89,000 |
| `fact_weekly_engagement` | Attendance, participation, academic/social engagement, stress — per student per module per week | 2,800,000 |
| `fact_assessment` | Module marks, UK grade classifications (First, 2:1, 2:2, Third, Fail), component and date | 468,000 |
| `fact_progression` | Year outcome, modules passed, average mark, next-year status | 89,000 |
| `fact_nss_responses` | Synthetic NSS scores across 7 themes + overall satisfaction | 23,000 |
| `fact_graduate_outcomes` | Degree classification, employment sector, salary band, time to first professional outcome | 19,500 |

All tables join on `student_id` + `academic_year`. See `docs/SCHEMA.md` for full column definitions.

The dataset is committed directly to this repository under `data/relational/`. Weekly engagement is split into per-year files (`fact_weekly_engagement_YYYY-YY.csv`) due to file size.

## Key features

- **Individual-level** — all outcomes emerge from student characteristics, not top-down group effects
- **Emergent awarding gaps** — an ~18pp good degree attainment gap between Elves and Dwarves arises from SES, prior education, and disability distributions, with no direct species modifier on marks
- **Longitudinal** — 7 cohorts across 7 academic years with progression, repetition, withdrawal, and graduation
- **Config-driven** — all parameters in YAML/CSV, no hardcoded values; reproducible via seed

## Quick start

```bash
pip install -r requirements.txt
python run_longitudinal_pipeline.py
```

This runs all 7 pipeline stages across 7 academic years and builds the full relational schema automatically. Runtime: ~10–15 minutes.

To regenerate the summary CSVs used by the public site:

```bash
python scripts/aggregate_gap.py
python scripts/aggregate_engagement.py
```

To validate outputs against expected ranges:

```bash
python metaanalysis/validate_outputs.py
```

## Project structure

```
simulated-university/
├── config/                         # All tunable parameters
│   ├── clan_personality_specifications.yaml
│   ├── clan_program_affinities.yaml
│   ├── year_progression_rules.yaml
│   ├── graduate_outcomes.yaml
│   ├── nss_modifiers.yaml
│   ├── module_characteristics.csv
│   └── ...
├── core_systems/                   # Pipeline stages (run in order)
│   ├── student_generation_pipeline.py
│   ├── program_enrollment_system.py
│   ├── engagement_system.py
│   ├── assessment_system.py
│   ├── progression_system.py
│   ├── graduate_outcomes_system.py
│   ├── nss_system.py
│   └── build_relational_outputs.py
├── supporting_systems/             # Shared utilities
├── data/
│   └── relational/                 # The dataset (committed to git)
├── docs/                           # Documentation + public site
│   ├── SCHEMA.md
│   ├── DESIGN.md
│   ├── CALCULATIONS.md
│   ├── PIPELINE_FLOW.md
│   └── index.html                  # GitHub Pages site
├── metaanalysis/
│   └── validate_outputs.py
├── scripts/
│   ├── aggregate_gap.py
│   └── aggregate_engagement.py
├── curriculum-and-lore/            # Curriculum source + world-building
├── requirements.txt
└── run_longitudinal_pipeline.py
```

## Configuration

**Tabular (CSV — editable in Excel):**
- `module_characteristics.csv` — difficulty, assessment type, semester per module
- `programme_characteristics.csv` — programme attributes
- `clan_socioeconomic_distributions.csv` — SES and prior education distributions per clan
- `disability_assessment_modifiers.csv` — mark modifiers per disability type
- `trait_programme_mapping.csv` — trait-to-programme affinity weights

**Hierarchical (YAML):**
- `clan_personality_specifications.yaml` — Big Five ranges and disability prevalence per clan
- `clan_program_affinities.yaml` — clan-programme affinity scores
- `year_progression_rules.yaml` — progression probabilities and trait modifier weights
- `graduate_outcomes.yaml` — employment sector, salary band, and outcome distributions
- `nss_modifiers.yaml` — theme weights and mark/engagement sensitivity

## Documentation

- `docs/SCHEMA.md` — column definitions for all 10 tables
- `docs/DESIGN.md` — architecture and longitudinal flow
- `docs/CALCULATIONS.md` — formulas, modifiers, and assumptions
- `docs/PIPELINE_FLOW.md` — student_id assignment and join conventions
- `docs/USER_GUIDE.md` — how to run, modify, and extend the pipeline
