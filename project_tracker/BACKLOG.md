# Backlog

Items to do next. Move to CURRENT when starting.

## Pipeline & data model

- [ ] Implement assessment system (end-of-module marks; output `stonegrove_assessment_events.csv` with `module_code`, `component_code`).
- [ ] Implement progression system (pass/fail, progression/repeat/withdrawal; status at start of year; `status_change_at`).
- [ ] Switch to calendar `academic_year` ("1046-47", …) everywhere; 7 years, 5 cohorts.
- [ ] Add `status_change_at` to enrollment output.
- [ ] Migrate `module_characteristics` and `programme_characteristics` to CSV; add `year_progression_rules.yaml`.

## Documentation & meta

- [ ] USER_GUIDE.md (how to run pipeline, read data).
- [ ] Update DATA_IO_PLAN.md for 7-year, 5-cohort flow and new file list.
- [ ] Metaanalysis / validation scripts (internal checks only; no analyst-facing assessment config).

## Later

- [ ] Support services, interventions, extra-curriculars (later phase).
- [ ] Case study extraction tools (phase N).
