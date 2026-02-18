# Backlog

Items to do next. Move to CURRENT when starting. Aligned with DESIGN.md Phase 1–3 migration path and Phase 2 success criteria.

---

## Bug fixes (code review, Feb 2026)

### High severity

- [x] **BUG: Disability sampling treats categorical distribution as independent Bernoullis** (`student_generation_pipeline.py:48-54`) – Fixed: config restructured as independent prevalence rates (comorbidities allowed). `no_known_disabilities` removed from config; assigned automatically when no disabilities drawn. Zero empty strings now.
- [x] **BUG: Dates off by one year** (`run_longitudinal_pipeline.py:32`) – Fixed: `_assessment_date()` now uses second calendar year (May). `_status_change_at()` was actually correct (September of first year = start of academic year).
- [x] **BUG: Clan mark modifiers are dead code** (`assessment_system.py:155-161`) – Fixed: new `config/clan_assessment_modifiers.csv` with modifiers for all 14 clans based on clan personality profiles. Loaded at init, no hardcoded clan names.
- [x] **BUG: SES modifier missing ranks 6-8** (`assessment_system.py:174-178`) – Fixed: mapping now covers all 8 ranks (0.88 to 1.12), monotonic gradient.
- [x] **BUG: Species modifier hardcoded, not config-driven** (`assessment_system.py:205`) – Fixed: removed. Species-level variation now emerges naturally from clan modifiers.
- [x] **BUG: Global `np.random.seed()` reset mid-pipeline** (`assessment_system.py:78`, `progression_system.py:37`) – Fixed: both systems now use `np.random.default_rng(seed)` as instance-level RNG instead of resetting global state.
- [x] **BUG: Mark distribution lacks discriminative power** (`assessment_system.py:195-201`) – Fixed: with working clan/SES modifiers, marks now differentiate meaningfully (~12pt spread by clan, ~18pt spread by SES).

### Medium severity

- [ ] **BUG: Personality column prefix mismatch in ModuleCharacteristicsSystem** (`supporting_systems/module_characteristics_system.py`) – Looks for `conscientiousness` but pipeline produces `refined_conscientiousness`. All personality-dependent module modifiers silently fall back to 0.5. Note: this file is currently unused by the pipeline (see cleanup section), but should be fixed if it gets integrated.
- [ ] **BUG: Semester hardcoded to 1** (`engagement_system.py:459`) – `generate_engagement_data` always passes `semester=1`. Semesters are 1 and 2 within each academic year, so this means semester 2 is never generated. Either generate both semesters or clarify that the pipeline only models one semester per year.
- [ ] **BUG: Semester engagement records missing `academic_year`** (`engagement_system.py:462-473`) – The semester engagement dict never includes `academic_year`, making multi-year semester data impossible to filter by year.
- [ ] **BUG: Weekly engagement clusters in narrow band** (`engagement_system.py:186-230,288-298`) – Base engagement range is ~[0.30, 0.85]; weekly variation std dev is only ~0.12. No shared within-week shocks across modules, no "bad weeks", seasonal patterns, or exam stress. Data is unrealistically smooth.
- [x] **BUG: `modules_passed` counts rows not distinct modules** (`progression_system.py:208-210`) – Fixed: now uses `nunique()` on `module_code` for passed assessments.
- [x] **BUG: `.values` strips index alignment** (`progression_system.py:210`) – Fixed: removed `.values`, letting pandas align by index.
- [x] **BUG: Metadata says 5 cohorts but code generates 7** (`run_longitudinal_pipeline.py:256`) – Fixed: metadata now has `cohorts_total` (7 enrolled) and `cohorts_graduating` (5 complete a 3-year programme). Docstring clarified.
- [ ] **BUG: `_determine_gender` clan overrides bypassed** (`student_generation_pipeline.py:87`) – `sample_gender()` is hardcoded 45/45/10 and the result is passed to `name_gen.generate_name()`. Clan-specific gender overrides defined in `clan_name_pools.yaml` are never applied.
- [x] **BUG: Engagement modifier docstring examples are wrong** (`assessment_system.py:183-185`) – Fixed: docstring now shows correct formula and values.

### Cleanup

- [x] **Remove `supporting_systems/program_affinity_system.py`** – Deleted. Enrollment system uses config-driven scoring.
- [x] **Remove `supporting_systems/module_characteristics_system.py`** – Deleted. Assessment and engagement systems load module characteristics directly from CSV.
- [x] **Remove unused imports** – Removed `datetime`/`timedelta` from `engagement_system.py`.
- [x] **Drop semester summaries as core output** – Longitudinal pipeline does not save semester summaries. Already done.
- [ ] **Add sample data to git** – split weekly engagement by academic year (one CSV per year, ~28 MB each) so users can download sample data without running the pipeline. Other data files are small enough to commit directly.

---

## Phase 1: Longitudinal foundation (DESIGN Migration Path)

### Progression & multi-year flow
- [x] **Create progression_system.py** – pass/fail per module; year outcome (all modules ≥ 40); progression/repeat/withdrawal (student-level, emergent from marks + traits + motivation). Includes modifiers for significant disability, caring responsibilities (when field exists).
- [x] **Add config/year_progression_rules.yaml** – base probabilities + individual modifiers.
- [ ] **Progression: withdrawal-after-fail logic** – refine after more pipeline runs: (a) year-in-programme – Y1 repeat has lower withdrawal likelihood than Y2/Y3 (investment effect); (b) previous repeat at any level increases withdrawal likelihood.
- [ ] **Add caring_responsibilities to student model** – for progression modifier (other stuff going on).
- [x] **Update enrollment system** – handle multiple years; one row per student per academic_year; add `status` (enrolled/repeating/withdrawn/graduated), `status_change_at`, `programme_year`.
- [x] **Rename output** – `stonegrove_enrolled_students.csv` → `stonegrove_enrollment.csv` (per DESIGN: one row per student per academic year).
- [x] **Add `academic_year`** – calendar format ("1046-47", …) to all domain tables (enrollment, weekly engagement, assessment events).
- [x] **Update engagement_system** – work with `academic_year`; generate per cohort per year.
- [x] **Run 5 cohorts × 7 years** – loop academic_year 1046-47 → 1052-53; new cohort each year; first cohort graduates year 3, then 4 more cohorts.

### Pipeline structure
- [x] **Integrate progression into run_pipeline.py** – add step 5 (progression_system) after assessment; append/write outputs per academic_year.
- [x] **Add data/metadata.json** – version, seed, timestamp, config_versions, cohort_size, years_generated, academic_years list, cohorts count (per DESIGN Versioning).

### Output changes (per DESIGN)
- [ ] **Drop semester summaries as core output** – DESIGN: derive from weekly engagement if needed; remove or demote `stonegrove_semester_engagement.csv` from pipeline.
- [ ] Ensure assessment events include `module_code`, `component_code` (done).

## Phase 2: Config (DESIGN – mostly done)
- [x] Migrate `module_characteristics` and `programme_characteristics` to CSV.
- [x] Add `config/year_progression_rules.yaml`.

## Phase 3: Documentation
- [x] **USER_GUIDE.md** – how to run pipeline, read data (started).
- [x] **Update DATA_IO_PLAN.md** – Updated for 7-year flow, all config/output files, data flow diagram.
- [x] SCHEMA.md, CALCULATIONS.md – Updated: progression_outcomes table added, all assessment modifiers current, awarding gap section, enrollment formula updated.
- [x] Update README.md – Rewritten: current project structure, config files, output files, documentation links.

## Validation (DESIGN Success Criteria)
- [ ] **Metaanalysis / validate_model_outputs.py** – internal checks: progression rates (e.g. 80–90% Y1→Y2), withdrawal (5–15%), grade distributions, awarding gaps visible.
- [ ] No analyst-facing assessment config (internal only).

## Optional / nice-to-have
- [ ] **Config path constant** – shared `paths.py` or env for `data/`, `config/`, `visualizations/`.
- [x] Single run script `run_pipeline.py` at root.

## Semester structure and assessment timing
- [ ] **Add semester to modules** – assign each module to semester 1 or 2 (in curriculum Excel or module_characteristics.csv). ~Half of each year's modules per semester.
- [ ] **Two assessment dates per academic year** – semester 1 assessments in January (e.g. 1047-01-15), semester 2 in May (e.g. 1047-05-15). Update `generate_assessment_data` to use per-module semester dates.
- [ ] **Engagement by semester** – engagement system currently generates 12 weeks all as semester 1. Split into two runs of 12 weeks each (or whatever the semester length should be). Engagement data should be filterable by semester.

## Awarding gap (agent-level emergence)
- [x] **Design awarding gap to emerge from individual-level factors** – Done: ~8.8pp Elf > Dwarf gap from clan-specific SES/education distributions, weighted clan recruitment, steeper modifiers. See DESIGN_DECISIONS.md.
- [x] **Tune SES/education distributions by species or clan** – Done: `config/clan_socioeconomic_distributions.csv` with per-clan SES rank probabilities and education background distributions.
- [ ] **Validate emergent gap** – metaanalysis script to check: are there visible awarding gaps by species? By clan? By SES? Are they realistic in magnitude? Can an analyst trace them to underlying factors?
- [ ] **Gender awarding gap** – male students often underperform females in real data. Currently gender has no effect on marks. Could add gender-differentiated engagement patterns or a small modifier. Should emerge from behaviour (e.g., engagement patterns) not a direct mark modifier.
- [ ] **Tune disability modifiers** – current values (all ≤1.0) represent a university without fully embedded reasonable adjustments. Real-world disability gap has largely closed through curriculum-embedded adjustments. Decide what story Stonegrove tells: good support (modifiers ~1.0) or barriers still present (current values). Some neurodivergent conditions may confer strengths in specific assessment types.
- [ ] **Engagement system as gap amplifier** – engagement already modifies marks (0.88–1.12). Widening the band, adding realistic weekly variation (bad weeks, exam stress), or making engagement more sensitive to SES/personality would amplify compounding effects over years.

## Later
- [ ] **Status rolls at start of each academic year** – optional later phase: roll for statuses like 'family thing happening',or 'suddenly more time' -- randome chance events roll?
- [ ] Support services, interventions, extra-curriculars.
- [ ] Case study extraction tools (phase N).

---

## What's next (after progression + longitudinal)

1. **5 cohorts × 7 years loop** – full longitudinal simulation.
2. **Enrollment/output restructure** – `stonegrove_enrollment.csv`, `academic_year` everywhere, `status_change_at`.
3. **Validation scripts** – metaanalysis to check progression/withdrawal rates, grade distributions.
4. **USER_GUIDE.md** – run pipeline, read data.
5. **Interventions phase** – support services, extra-curriculars (later).
