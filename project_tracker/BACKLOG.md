# Backlog

Items to do next. Move to CURRENT when starting.

---

## Refactoring (do before next feature)

### Path & run consistency
- [ ] **student_generation_pipeline**: Output to `data/stonegrove_individual_students.csv` (currently writes to cwd without `data/` prefix).
- [ ] **archive enrollment_visualization**: Update to read `data/stonegrove_enrolled_students.csv` and write `visualizations/stonegrove_enrollment_analysis.png` (currently uses root paths).
- [ ] **README pipeline instructions**: Standardise on "run all from project root" with `python core_systems/script.py` (currently says `cd core_systems` for student gen, which breaks paths).
- [ ] **Imports**: student_generation_pipeline imports `name_generator`, `personality_refinement_system`, `motivation_profile_system` from supporting_systems — ensure these work when run from project root (may need `sys.path` or `-m`).

### Docs vs implementation
- [ ] **SCHEMA.md**: Module lists use CSV comma+quoting (via `csv` module), not pipe. Update SCHEMA to say "CSV-formatted (comma-separated, quoted where needed)".

### Optional / nice-to-have
- [ ] **Single run script**: Add `run_pipeline.py` at root that runs all steps in order (students → enrollment → engagement), so users don't have to remember the sequence.
- [ ] **Config path constant**: Consider a shared `paths.py` or env for `data/`, `config/`, `visualizations/` so paths aren't scattered.

---

## Pipeline & data model (after refactoring)

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
