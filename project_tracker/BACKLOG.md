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

### High severity

- [x] **DESIGN DECISION: Clan assessment modifier not wired in** — `_get_clan_modifier` returns 1.0 by design. `config/archive/clan_assessment_modifiers.csv` is archived. Awarding gap emerges from SES/education/disability at individual level, not from a direct clan mark modifier. Do not re-wire.

- [x] **BUG: Continuing students assessed on year-1 modules regardless of programme_year** (`assessment_system.py`) — Fixed: `generate_assessment_data` reads `programme_year` and uses `year{prog_year}_modules` column to select the correct module set for each student's year of study.

### Medium severity

- [ ] **BUG: Personality column prefix mismatch in ModuleCharacteristicsSystem** (`supporting_systems/module_characteristics_system.py`) – Looks for `conscientiousness` but pipeline produces `refined_conscientiousness`. Note: this file is currently unused by the pipeline; fix if it gets integrated.
- [x] **BUG: Semester hardcoded to 1** (`engagement_system.py`) – Fixed: semester now derived from `prog_year`; the engagement rewrite no longer hardcodes semester=1.
- [x] **BUG: Semester engagement records missing `academic_year`** (`engagement_system.py`) – Fixed: `academic_year` now included in semester summary dicts.
- [x] **BUG: Weekly engagement clusters in narrow band** (`engagement_system.py`) – Fixed: AR(1) autocorrelated week deviations (alpha=0.4, fixed std=0.12), temporal arc (early/midterm/exam), disability base adjustments + std_extra, SES rank modifiers. All driven from `config/engagement_modifiers.yaml`.
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
- [ ] **Add caring_responsibilities to student model** – for progression modifier (other stuff going on). Note: dead code removed from `_apply_modifiers` in progression_system.py; must be added to student generation *first* before re-introducing the progression modifier.
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

## Module trailing (resit/carry-forward)

- [ ] **Implement single-module trailing in subsequent academic years** — currently a student either passes the whole year or repeats the whole year. In reality, students who pass the year overall but have one module below 40 can "trail" that module into the next year and resit it alongside their new year's work. Logic: after progression, identify students with `year_outcome = pass` but one or more FINAL `combined_mark < 40`; flag those modules as trailed; generate a resit assessment row in the following academic year's data (new `component_code = "RESIT"`), engagement-weighted as appropriate. The student progresses to the next year regardless; a failed resit typically triggers a year repeat or cap on final classification. Requires changes to: `progression_system.py` (detect trailing modules), `assessment_system.py` (generate resit rows), and `docs/SCHEMA.md`.

## Semester structure and assessment timing
- [x] **Add semester to modules** – `config/module_characteristics.csv` has `semester` column (1=Autumn, 2=Spring). 221 S1, 132 S2 modules across 353 total. Engagement records also have `semester` column.
- [x] **Two assessment dates per academic year** – `_assessment_dates()` in `assessment_system.py`. S1: Nov 1 (midterm), Dec 15 (final). S2: Mar 15 (midterm), May 15 (final). 4 distinct dates per academic year.
- [x] **Engagement by semester** – weekly records have `semester` column from `_module_chars`. The 12-week arc is per-module and filterable by semester. (Arc is not split into two 6-week runs; the 12-week arc per module is the intended design.)
- [x] **Two assessment components per module (midterm + final)** — MIDTERM + FINAL rows per student per module. MIDTERM uses weeks 1–8 engagement; FINAL uses all 12 weeks. `combined_mark = 0.4 × MIDTERM + 0.6 × FINAL` on FINAL rows. Progression uses `combined_mark` from FINAL rows only.

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
