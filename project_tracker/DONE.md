# Done

Short log of completed work. Add a line when something is finished.

- 2026-02: DESIGN.md, SCHEMA.md updated (academic_year calendar 1046-47…, enrollment status_change_at, assessment module_code/component_code, semester summaries dropped, config YAML/CSV split, 5 cohorts × 7 years, no assessment_distributions output, year_progression_rules.yaml).
- 2026-02: project_tracker folder added (CURRENT, BACKLOG, DONE, README).
- 2026-02: Folder tidy: engagement_visualization → metaanalysis/, PROJECT_SUMMARY → docs/, references updated.
- 2026-02: Refactoring: path consistency (data/, visualizations/), project-root run, imports, README, SCHEMA module list format.
- 2026-02: run_pipeline.py (single script for full pipeline); removed emoji from program_enrollment/engagement (Windows cp1252).
- 2026-02: Assessment system (core_systems/assessment_system.py); output stonegrove_assessment_events.csv with module_code, component_code.
- 2026-02: Assessment uses module_characteristics for assessment_type and difficulty; migration to CSV (module_characteristics.csv, programme_characteristics.csv); engagement_system reads CSV.
- 2026-02: Longitudinal pipeline (5 cohorts × 7 years; run_longitudinal_pipeline.py; enrollment, engagement, assessment, progression with academic_year; stonegrove_enrollment.csv, stonegrove_progression_outcomes.csv, metadata.json).
- 2026-02: Year 3 graduation logic – pass in programme_year 3 → status "graduated"; verified cohort graduation (~68%).
- 2026-02: Pipeline robustness: student_id fix (merge not concat in enroll_students_batch); engagement uses actual student_id not index; Series handling for duplicate columns; PIPELINE_FLOW.md.
