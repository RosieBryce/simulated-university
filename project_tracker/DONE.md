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
- 2026-02: CLAUDE.md created for Claude Code onboarding.
- 2026-02: Code review — identified 20+ bugs, written up in BACKLOG.md.
- 2026-02: Config-driven programme selection — `trait_programme_mapping.csv`, affinity multipliers from YAML, removed keyword matching.
- 2026-02: Bug fixes — disability sampling (independent Bernoulli + comorbidities), assessment dates (May of second year), SES modifier (ranks 1–8), removed hardcoded species modifier.
- 2026-02: Emergent awarding gap (~8.8pp Elf > Dwarf) — clan-specific SES/education distributions, weighted clan recruitment, steeper SES/education/disability modifiers. All agent-level, no top-down group modifiers. See DESIGN_DECISIONS.md.
- 2026-02: `data/` added to .gitignore; removed from git history with filter-branch.
