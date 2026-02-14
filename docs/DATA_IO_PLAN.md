# Data Inputs and Outputs Plan

## Overview

This document defines where data comes from, where it goes, and how to keep the project maintainable across long gaps between sessions.

---

## Input Sources

| Source | Location | Format | Used By |
|--------|----------|--------|---------|
| Curriculum | `Instructions and guides/Stonegrove_University_Curriculum.xlsx` | XLSX (Programmes, Modules sheets) | program_enrollment_system |
| Clan specs | `config/clan_personality_specifications.yaml` | YAML | student_generation_pipeline, personality_refinement |
| Name pools | `config/clan_name_pools.yaml` | YAML | name_generator |
| Program affinities | `config/clan_program_affinities.yaml` | YAML | program_enrollment_system |
| Disability distribution | `config/disability_distribution.yaml` | YAML | student_generation_pipeline |
| Module characteristics | `config/module_characteristics.yaml` → **`config/module_characteristics.csv`** | YAML (migrating to CSV) | engagement_system, module_characteristics_system |
| Programme characteristics | `config/program_characteristics.yaml` → **`config/programme_characteristics.csv`** | YAML (migrating to CSV) | engagement_system |
| Year progression rules | **`config/year_progression_rules.yaml`** (new) | YAML | progression_system |
| World-building | `Instructions and guides/World-building/` | Markdown, XLSX | Reference only |

*Clan personality, clan programme affinities, disability distribution stay YAML.*

### Pending: XLSX Import

- [ ] Import all XLSX files into a canonical data structure (e.g. `data/curriculum/` or config-driven)
- [ ] Document schema for each source

---

## Output Data (Generated)

| File | Location | Produced By | Consumed By |
|------|----------|-------------|-------------|
| Individual students | `data/stonegrove_individual_students.csv` | student_generation_pipeline | program_enrollment_system |
| Enrollment | `data/stonegrove_enrollment.csv` | program_enrollment_system | engagement_system, assessment_system, progression_system |
| Weekly engagement | `data/stonegrove_weekly_engagement.csv` | engagement_system | visualizations, metaanalysis |
| Assessment events | `data/stonegrove_assessment_events.csv` | (future) assessment_system | metaanalysis, analysts |
| Metadata | `data/metadata.json` | pipeline runner | reproducibility |

*Semester summaries are not a core output; derive from weekly engagement if needed. Academic year is calendar format (e.g. "1046-47"). Simulation: 7 years, 5 cohorts. See docs/DESIGN.md.*

---

## Data Flow

```
[Config YAMLs + module/programme CSV] ──┐
[Curriculum XLSX] ──────────────────────┼──► student_generation_pipeline ──► stonegrove_individual_students.csv
                                       │              │
                                       └──► program_enrollment_system ◄───┘
                                                          │
                                                          ▼
                                            stonegrove_enrollment.csv (academic_year, status_change_at)
                                                          │
                                    ┌─────────────────────┼─────────────────────┐
                                    ▼                     ▼                     ▼
                    engagement_system ──► weekly_engagement   assessment_system ──► assessment_events
                                    │         (no semester as core output)
                                    └─────────────────────► metaanalysis, visualizations
```

---

## Conventions

1. **All generated CSVs live in `data/`** – no outputs in root or core_systems
2. **All config lives in `config/`** – YAML for human-editable parameters
3. **Source materials stay in `Instructions and guides/`** – do not modify programmatically
4. **Paths**: Scripts use `data/` prefix when run from project root (see core_systems)
5. **Regeneration**: Full pipeline order: students → enrollment → engagement (each depends on previous)

---

## Regeneration Order

**Current (Year 1 only):**
1. `python core_systems/student_generation_pipeline.py`
2. `python core_systems/program_enrollment_system.py`
3. `python core_systems/engagement_system.py`

**Target (longitudinal, 7 years, 5 cohorts):** For each academic year "1046-47" … "1052-53": new cohort + enrollment + engagement + assessment + progression; see docs/DESIGN.md.

---

## Versioning and Reproducibility

- Config files are version-controlled; changes affect outputs
- Generated CSVs are typically *not* committed (large, derived); add to `.gitignore` if desired
- For reproducibility: document config hash or tag when publishing results
