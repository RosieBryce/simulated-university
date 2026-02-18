# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Stonegrove University is a **synthetic data generator** for a fictional fantasy university. It simulates realistic higher-education student lifecycle data (UK-style) using a Middle-Earth-inspired setting (Dwarves, Elves, 14 clans) to avoid privacy concerns. The output CSVs mirror real student record systems for use in education research, AI hackathons, and awarding gap analysis.

## Running the Pipeline

All commands run from the project root. Install deps with `pip install -r requirements.txt`.

```bash
# Full longitudinal simulation: 5 cohorts × 7 academic years (1046-47 to 1052-53)
python run_longitudinal_pipeline.py

# Single-year pipeline (all 5 stages sequentially)
python run_pipeline.py

# Individual stages (must run in order)
python core_systems/student_generation_pipeline.py
python core_systems/program_enrollment_system.py
python core_systems/engagement_system.py
python core_systems/assessment_system.py
python core_systems/progression_system.py
```

There is no test suite, linter config, or build system. Validation is done via metaanalysis scripts:
```bash
python metaanalysis/difficulty_analysis.py
python metaanalysis/engagement_visualization.py
```

## Architecture

### Pipeline Flow (strictly sequential, each stage reads the previous output)

1. **Student Generation** (`core_systems/student_generation_pipeline.py`) — 500 students/cohort with species, clan, Big Five personality, 8 motivation dimensions, disabilities, SES. Uses `PersonalityRefinementSystem`, `MotivationProfileSystem`, `ClanNameGenerator` from `supporting_systems/`.
2. **Enrollment** (`core_systems/program_enrollment_system.py`) — Assigns students to 1 of 44 programmes across 4 faculties using clan-programme affinities + personality modifiers. Assigns Year 1/2/3 modules.
3. **Engagement** (`core_systems/engagement_system.py`) — Generates 12 weeks × modules of attendance, participation, academic/social engagement, stress. Personality traits drive metrics (e.g., conscientiousness→attendance r=0.856).
4. **Assessment** (`core_systems/assessment_system.py`) — End-of-module marks with UK-style distribution, modified by module difficulty and engagement metrics.
5. **Progression** (`core_systems/progression_system.py`) — Pass/fail/withdraw/repeat decisions via log-odds model with trait-based modifiers from `config/year_progression_rules.yaml`.

**Longitudinal loop**: `run_longitudinal_pipeline.py` wraps stages 1-5 in a 7-year loop. Each year generates a fresh cohort AND re-enrolls continuing students from prior years. All outputs accumulate across years.

### Joining Key

All CSV tables join on `student_id` + `academic_year`. See `docs/PIPELINE_FLOW.md` for student_id assignment and column dedup details.

### Configuration

- **YAML** for hierarchical configs: clan personality ranges, clan-programme affinities, disability distributions, name pools, progression rules
- **CSV** for tabular configs: `config/module_characteristics.csv`, `config/programme_characteristics.csv`
- All systems accept a `seed` parameter for reproducibility. Metadata is written to `data/metadata.json`.

### Key Design Decisions

- The canonical curriculum source is `Instructions and guides/Stonegrove_University_Curriculum.xlsx` (44 programmes, 4 faculties, Year 1/2/3 modules).
- "Species" is used instead of "Race" throughout the codebase.
- Tabular configs are CSV (editable in Excel); hierarchical configs are YAML.

## Documentation

- `docs/DESIGN.md` — Architecture and longitudinal flow
- `docs/SCHEMA.md` — All CSV column definitions
- `docs/CALCULATIONS.md` — Formulas and modifiers
- `docs/PIPELINE_FLOW.md` — student_id assignment and column dedup
- `docs/PROJECT_SUMMARY.md` — Pick-up guide and project status
- `project_tracker/CURRENT.md` and `project_tracker/BACKLOG.md` — Task tracking
