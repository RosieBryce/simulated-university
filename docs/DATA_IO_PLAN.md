# Data Inputs and Outputs Plan

## Overview

This document defines where data comes from, where it goes, and how to keep the project maintainable across long gaps between sessions.

---

## Input Sources

| Source | Location | Format | Used By |
|--------|----------|--------|---------|
| Curriculum | `Instructions and guides/Stonegrove_University_Curriculum.xlsx` | XLSX (Programmes, Modules sheets) | program_enrollment_system, assessment_system |
| Clan specs | `config/clan_personality_specifications.yaml` | YAML | student_generation_pipeline, personality_refinement |
| Name pools | `config/clan_name_pools.yaml` | YAML | name_generator |
| Programme affinities | `config/clan_program_affinities.yaml` | YAML | program_enrollment_system (affinity scores + settings) |
| Disability distribution | `config/disability_distribution.yaml` | YAML (independent prevalence rates) | student_generation_pipeline |
| Module characteristics | `config/module_characteristics.csv` | CSV | engagement_system, assessment_system |
| Programme characteristics | `config/programme_characteristics.csv` | CSV | program_enrollment_system (trait-fit scoring) |
| Trait-programme mapping | `config/trait_programme_mapping.csv` | CSV | program_enrollment_system |
| Clan SES distributions | `config/clan_socioeconomic_distributions.csv` | CSV | student_generation_pipeline |
| Disability modifiers | `config/disability_assessment_modifiers.csv` | CSV | assessment_system |
| Progression rules | `config/year_progression_rules.yaml` | YAML | progression_system |
| World-building | `Instructions and guides/World-building/` | Markdown, XLSX | Reference only |

---

## Output Data (Generated)

All generated data lives in `data/` (gitignored — regenerate with `python run_longitudinal_pipeline.py`).

| File | Location | Produced By | Consumed By |
|------|----------|-------------|-------------|
| Individual students | `data/stonegrove_individual_students.csv` | student_generation_pipeline | program_enrollment_system |
| Enrollment | `data/stonegrove_enrollment.csv` | program_enrollment_system | engagement_system, assessment_system, progression_system |
| Weekly engagement | `data/stonegrove_weekly_engagement.csv` | engagement_system | assessment_system, metaanalysis |
| Assessment events | `data/stonegrove_assessment_events.csv` | assessment_system | progression_system, metaanalysis |
| Progression outcomes | `data/stonegrove_progression_outcomes.csv` | progression_system | next-year enrollment, metaanalysis |
| Metadata | `data/metadata.json` | run_longitudinal_pipeline | reproducibility |

---

## Data Flow

```
[Config YAML/CSV] ──────────────────────────────┐
[Curriculum XLSX] ──────────────────────────────┼──> student_generation_pipeline
                                                │            │
                                                │            v
                                                │   stonegrove_individual_students.csv
                                                │            │
                                                └──> program_enrollment_system <──┘
                                                             │
                                                             v
                                                 stonegrove_enrollment.csv
                                                    (per academic year)
                                                             │
                                              ┌──────────────┼──────────────┐
                                              v              v              v
                                     engagement_system   assessment_system
                                              │              │
                                              v              v
                                     weekly_engagement   assessment_events
                                                             │
                                                             v
                                                    progression_system
                                                             │
                                                             v
                                                  progression_outcomes
                                                             │
                                              ┌──────────────┘
                                              v
                                     next year's enrollment
                                     (continuing students)
```

Each academic year (1046-47 through 1052-53) runs the full pipeline. 7 cohorts, 7 years. New cohort each year + continuing/repeating students from previous year.

---

## Conventions

1. **All generated CSVs live in `data/`** — gitignored, regenerate with pipeline
2. **All config lives in `config/`** — YAML for hierarchical, CSV for tabular/end-user-editable
3. **Source materials stay in `Instructions and guides/`** — do not modify programmatically
4. **Paths**: Scripts use relative paths from project root
5. **Regeneration**: `python run_longitudinal_pipeline.py` (single command, full pipeline)

---

## Versioning and Reproducibility

- Config files are version-controlled; changes affect outputs
- Generated CSVs are gitignored (large, derived)
- `data/metadata.json` records git commit, seed, timestamp for reproducibility
- For reproducibility: same seed + same config + same code = same outputs
