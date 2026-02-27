# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Stonegrove University is a **synthetic data generator** for a fictional fantasy university. It simulates realistic higher-education student lifecycle data (UK-style) using a Middle-Earth-inspired setting (Dwarves, Elves, 14 clans) to avoid privacy concerns. The output is a relational schema of 10 tables for use in education research, AI hackathons, and awarding gap analysis.

## Running the Pipeline

All commands run from the project root. Install deps with `pip install -r requirements.txt`.

```bash
# Full longitudinal simulation: 7 cohorts × 7 academic years (1046-47 to 1052-53)
# Automatically builds relational schema at the end
python run_longitudinal_pipeline.py

# Individual stages (must run in order)
python core_systems/student_generation_pipeline.py
python core_systems/program_enrollment_system.py
python core_systems/engagement_system.py
python core_systems/assessment_system.py
python core_systems/progression_system.py
python core_systems/graduate_outcomes_system.py
python core_systems/nss_system.py

# Build relational schema from pipeline outputs
python core_systems/build_relational_outputs.py

# Regenerate site summary CSVs (run after pipeline)
python scripts/aggregate_gap.py
python scripts/aggregate_engagement.py
```

Validation (reads from `data/relational/`):
```bash
python metaanalysis/validate_outputs.py
```

## Architecture

### Pipeline Flow (strictly sequential)

1. **Student Generation** (`core_systems/student_generation_pipeline.py`) — 5,000 students/cohort with species, clan, Big Five personality, 8 motivation dimensions, disabilities, SES. Uses `PersonalityRefinementSystem`, `MotivationProfileSystem`, `ClanNameGenerator` from `supporting_systems/`.
2. **Enrollment** (`core_systems/program_enrollment_system.py`) — Assigns students to 1 of 44 programmes across 4 faculties using clan-programme affinities + personality modifiers. Assigns Year 1/2/3 modules.
3. **Engagement** (`core_systems/engagement_system.py`) — Generates 12 weeks × modules of attendance, participation, academic/social engagement, stress. Personality traits drive metrics (e.g., conscientiousness→attendance r=0.856).
4. **Assessment** (`core_systems/assessment_system.py`) — Two components per module (MIDTERM + FINAL). `combined_mark = 0.4×MIDTERM + 0.6×FINAL` on FINAL rows. UK-style mark distribution modified by difficulty and engagement.
5. **Progression** (`core_systems/progression_system.py`) — Pass/fail/withdraw/repeat decisions via log-odds model with trait-based modifiers from `config/year_progression_rules.yaml`. Filters to `component_code == 'FINAL'`, uses `combined_mark`.
6. **Graduate Outcomes** (`core_systems/graduate_outcomes_system.py`) — Degree classification (Y2 1/3, Y3 2/3 weighting), employment sector, salary band, professional level. SES gradient on salary and professional employment.
7. **NSS** (`core_systems/nss_system.py`) — One response per Year 3 student per academic year. 7 themes + overall satisfaction (1–5). Calibrated to UK NSS benchmarks.

**Longitudinal loop**: `run_longitudinal_pipeline.py` wraps stages 1–7 across 7 academic years, re-enrolling continuing students from prior years. `build_relational_outputs.py` runs automatically at the end.

### Relational Schema

10 tables in `data/relational/`: 4 dims + 6 facts. Weekly engagement is stored as 7 per-year files (`fact_weekly_engagement_YYYY-YY.csv`) — no combined file. All tracked in git except the (no longer generated) combined weekly file.

Joining key: `student_id` + `academic_year`. See `docs/PIPELINE_FLOW.md`.

### Configuration

- **YAML** for hierarchical configs: clan personality ranges, clan-programme affinities, disability distributions, name pools, progression rules, NSS modifiers, graduate outcomes
- **CSV** for tabular configs: `config/module_characteristics.csv`, `config/programme_characteristics.csv`
- All systems accept a `seed` parameter for reproducibility. Metadata written to `data/metadata.json`.

### Key Design Decisions

- The canonical curriculum source is `curriculum-and-lore/Stonegrove_University_Curriculum.xlsx` (44 programmes, 4 faculties, Year 1/2/3 modules).
- "Species" is used instead of "Race" throughout the codebase.
- No direct clan/species mark modifier — the ~18pp good degree attainment gap (Elf vs Dwarf) emerges from SES, prior education, and disability distributions only.
- Gender awarding gap is flat by design.
- Tabular configs are CSV (editable in Excel); hierarchical configs are YAML.

## Documentation

- `docs/DESIGN.md` — Architecture and longitudinal flow
- `docs/SCHEMA.md` — All CSV column definitions
- `docs/CALCULATIONS.md` — Formulas and modifiers
- `docs/PIPELINE_FLOW.md` — student_id assignment and column dedup
- `docs/USER_GUIDE.md` — How to run and extend the pipeline
- `docs/index.html` — Public-facing GitHub Pages site

## Public Site

`docs/` contains a static GitHub Pages site. Enable via: Settings → Pages → master / /docs.

After any pipeline rerun, regenerate site data:
```bash
python scripts/aggregate_gap.py
python scripts/aggregate_engagement.py
```
