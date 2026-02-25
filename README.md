# Stonegrove University Individual-Level Modeling System

A simulation system for modeling individual student behavior, engagement, and academic progression at Stonegrove University — a fantasy higher education institution with Dwarves and Elves.

## Project Overview

This system generates unique students with personality traits, motivations, and behavioral patterns that influence their academic journey. It produces realistic datasets with emergent awarding gaps for use in teaching data analysis and educational research methods.

Key features:
- **Individual-level modeling** — all outcomes emerge from student-level characteristics, not top-down group effects
- **Longitudinal simulation** — 7 cohorts across 7 academic years with progression, repetition, withdrawal, and graduation
- **Config-driven** — all tunable parameters in YAML/CSV files, no hardcoded values
- **Emergent awarding gaps** — species/clan/SES differences visible in aggregate analysis, traceable to structural factors

## Quick Start

**Run all commands from the project root.**

### Prerequisites
```bash
pip install pandas numpy matplotlib seaborn scipy openpyxl xlrd PyYAML
```

### Run the full longitudinal pipeline
```bash
python run_longitudinal_pipeline.py
```
Generates 7 years of data: student generation -> enrollment -> engagement -> assessment -> progression, repeated per academic year with new cohorts and continuing students.

### Run single-year pipeline (Year 1 only)
```bash
python run_pipeline.py
```

## Project Structure

```
simulated-university/
├── config/                              # Configuration files (YAML + CSV)
│   ├── clan_personality_specifications.yaml
│   ├── clan_program_affinities.yaml
│   ├── clan_name_pools.yaml
│   ├── clan_socioeconomic_distributions.csv
│   ├── disability_distribution.yaml
│   ├── disability_assessment_modifiers.csv
│   ├── module_characteristics.csv
│   ├── programme_characteristics.csv
│   ├── trait_programme_mapping.csv
│   └── year_progression_rules.yaml
├── core_systems/                        # Pipeline stages
│   ├── student_generation_pipeline.py
│   ├── program_enrollment_system.py
│   ├── engagement_system.py
│   ├── assessment_system.py
│   └── progression_system.py
├── supporting_systems/                  # Utilities
│   ├── name_generator.py
│   ├── personality_refinement_system.py
│   └── motivation_profile_system.py
├── data/                                # Generated data (gitignored)
├── docs/                                # Documentation
│   ├── DESIGN.md                        # Architecture and longitudinal flow
│   ├── SCHEMA.md                        # Column definitions for all outputs
│   ├── CALCULATIONS.md                  # Formulas and modifiers reference
│   ├── DATA_IO_PLAN.md                  # Data flow and conventions
│   └── USER_GUIDE.md                    # How to run and read data
├── project_tracker/                     # Development tracking
│   ├── CURRENT.md                       # Priority queue
│   ├── BACKLOG.md                       # All open items
│   ├── DONE.md                          # Completed work
│   └── DESIGN_DECISIONS.md             # Rationale for key choices
├── Instructions and guides/             # Source materials and world-building
├── metaanalysis/                        # Analysis scripts
├── run_pipeline.py                      # Single-year pipeline
└── run_longitudinal_pipeline.py         # Full longitudinal pipeline
```

## Output Data

All generated CSVs are in `data/` (gitignored). Key files:

| File | Description |
|------|-------------|
| `stonegrove_individual_students.csv` | Student demographics, personality, motivation |
| `stonegrove_enrollment.csv` | Programme enrollment per student per year |
| `stonegrove_weekly_engagement.csv` | Weekly attendance, participation, engagement |
| `stonegrove_assessment_events.csv` | Module marks and grades |
| `stonegrove_progression_outcomes.csv` | Year-end pass/fail and progression decisions |
| `metadata.json` | Version, seed, timestamp for reproducibility |

See `docs/SCHEMA.md` for full column definitions.

## Configuration

### Tabular config (CSV, end-user editable)
- `clan_socioeconomic_distributions.csv` — SES rank and education distributions per clan
- `disability_assessment_modifiers.csv` — mark modifiers per disability
- `trait_programme_mapping.csv` — which student traits attract to which programme characteristics
- `programme_characteristics.csv` — programme attributes (social intensity, difficulty, etc.)
- `module_characteristics.csv` — module difficulty, assessment type

### Hierarchical config (YAML)
- `clan_personality_specifications.yaml` — Big Five personality ranges per clan + `health_tendencies` (per-clan disability prevalence)
- `clan_program_affinities.yaml` — clan-programme affinity scores + selection settings
- `year_progression_rules.yaml` — progression probabilities, trait modifier weights, `trait_modifier_scale`
- `engagement_modifiers.yaml` — disability/SES base adjustments, weekly std_extra, temporal arc
- `assessment_modifiers.yaml` — education and SES mark multipliers

## Documentation

- `docs/USER_GUIDE.md` — how to run the pipeline and read the data
- `docs/DESIGN.md` — architecture and longitudinal flow
- `docs/SCHEMA.md` — column definitions for all output files
- `docs/CALCULATIONS.md` — formulas, modifiers, and assumptions
- `project_tracker/DESIGN_DECISIONS.md` — rationale for key design choices
