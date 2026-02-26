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

- [x] **BUG: Personality column prefix mismatch in ModuleCharacteristicsSystem** (`supporting_systems/module_characteristics_system.py`) – Moot: `module_characteristics_system.py` was deleted (cleanup). Assessment and engagement systems load module characteristics directly from CSV.
- [x] **BUG: Semester hardcoded to 1** (`engagement_system.py`) – Fixed: semester now derived from `prog_year`; the engagement rewrite no longer hardcodes semester=1.
- [x] **BUG: Semester engagement records missing `academic_year`** (`engagement_system.py`) – Fixed: `academic_year` now included in semester summary dicts.
- [x] **BUG: Weekly engagement clusters in narrow band** (`engagement_system.py`) – Fixed: AR(1) autocorrelated week deviations (alpha=0.4, fixed std=0.12), temporal arc (early/midterm/exam), disability base adjustments + std_extra, SES rank modifiers. All driven from `config/engagement_modifiers.yaml`.
- [x] **BUG: `modules_passed` counts rows not distinct modules** (`progression_system.py:208-210`) – Fixed: now uses `nunique()` on `module_code` for passed assessments.
- [x] **BUG: `.values` strips index alignment** (`progression_system.py:210`) – Fixed: removed `.values`, letting pandas align by index.
- [x] **BUG: Metadata says 5 cohorts but code generates 7** (`run_longitudinal_pipeline.py:256`) – Fixed: metadata now has `cohorts_total` (7 enrolled) and `cohorts_graduating` (5 complete a 3-year programme). Docstring clarified.
- [x] **BUG: `_determine_gender` clan overrides bypassed** – Fixed: `_determine_gender` now reads `neuter_probability` (and full `gender_distribution` dict) per clan from `clan_name_pools.yaml`. Neuter probabilities set: obsidian/slate 12% (deity Durren), yew 11%, alabaster 12%, all others 10%.
- [x] **BUG: Engagement modifier docstring examples are wrong** (`assessment_system.py:183-185`) – Fixed: docstring now shows correct formula and values.

### Cleanup

- [x] **Remove `supporting_systems/program_affinity_system.py`** – Deleted. Enrollment system uses config-driven scoring.
- [x] **Remove `supporting_systems/module_characteristics_system.py`** – Deleted. Assessment and engagement systems load module characteristics directly from CSV.
- [x] **Remove unused imports** – Removed `datetime`/`timedelta` from `engagement_system.py`.
- [x] **Drop semester summaries as core output** – Longitudinal pipeline does not save semester summaries. Already done.
- [x] **Add sample data to git** – All pipeline outputs committed. Weekly engagement split into `data/weekly_engagement/` per-year files (3–12 MB each). Blanket `data/` gitignore replaced with targeted ignores for combined weekly file, legacy, relational, archive dirs.

---

## Phase 1: Longitudinal foundation (DESIGN Migration Path)

### Progression & multi-year flow
- [x] **Create progression_system.py** – pass/fail per module; year outcome (all modules ≥ 40); progression/repeat/withdrawal (student-level, emergent from marks + traits + motivation). Includes modifiers for significant disability, caring responsibilities (when field exists).
- [x] **Add config/year_progression_rules.yaml** – base probabilities + individual modifiers.
- [x] **Progression: withdrawal-after-fail logic** – Done: year investment effect (`year_withdrawal_after_fail`: Y1 +0.35, Y2 -0.25, Y3 -0.55) and prior repeat discouragement (`prior_repeat_withdrawal`: +0.45) wired in `config/year_progression_rules.yaml`.
- [x] **Update enrollment system** – handle multiple years; one row per student per academic_year; add `status` (enrolled/repeating/withdrawn/graduated), `status_change_at`, `programme_year`.
- [x] **Rename output** – `stonegrove_enrolled_students.csv` → `stonegrove_enrollment.csv` (per DESIGN: one row per student per academic year).
- [x] **Add `academic_year`** – calendar format ("1046-47", …) to all domain tables (enrollment, weekly engagement, assessment events).
- [x] **Update engagement_system** – work with `academic_year`; generate per cohort per year.
- [x] **Run 5 cohorts × 7 years** – loop academic_year 1046-47 → 1052-53; new cohort each year; first cohort graduates year 3, then 4 more cohorts.

### Pipeline structure
- [x] **Integrate progression into run_pipeline.py** – add step 5 (progression_system) after assessment; append/write outputs per academic_year.
- [x] **Add data/metadata.json** – version, seed, timestamp, config_versions, cohort_size, years_generated, academic_years list, cohorts count (per DESIGN Versioning).

### Output changes (per DESIGN)
- [x] **Drop semester summaries as core output** – `stonegrove_semester_engagement.csv` removed; pipeline does not output semester summaries. Derived from weekly engagement if needed.
- [x] Ensure assessment events include `module_code`, `component_code` (done).

## Phase 2: Config (DESIGN – mostly done)
- [x] Migrate `module_characteristics` and `programme_characteristics` to CSV.
- [x] Add `config/year_progression_rules.yaml`.

## Phase 3: Documentation
- [x] **USER_GUIDE.md** – how to run pipeline, read data (started).
- [x] **Update DATA_IO_PLAN.md** – Updated for 7-year flow, all config/output files, data flow diagram.
- [x] SCHEMA.md, CALCULATIONS.md – Updated: progression_outcomes table added, all assessment modifiers current, awarding gap section, enrollment formula updated.
- [x] Update README.md – Rewritten: current project structure, config files, output files, documentation links.

## Optional / nice-to-have
- [ ] **Config path constant** – shared `paths.py` or env for `data/`, `config/`, `visualizations/`.
- [x] Single run script `run_pipeline.py` at root.

## Graduate outcomes

- [x] **Model graduate outcomes** — Done: `core_systems/graduate_outcomes_system.py` + `config/graduate_outcomes.yaml`. 1,966 graduates across 5 cohorts. Degree classification (Y2 1/3, Y3 2/3), employment/sector/salary/professional level. SES gradient on salary and professional employment. No direct species/clan modifier. Wired into longitudinal pipeline; outputs to `stonegrove_graduate_outcomes.csv`.

## NSS (National Student Survey)

- [x] **Model NSS responses** — Done: `core_systems/nss_system.py` + `config/nss_modifiers.yaml`. 7 themes + overall_satisfaction (1–5 integer). One response per Yr3 student per year, including repeating Yr3 students (`is_repeat_year` flag). Score model: base + engagement + mark signal (A&F) + SES + disability + personality + correlated student bias + independent per-theme noise. Calibrated to real UK NSS benchmarks: org & management lowest (~60%); A&F most variable (mark-sensitive); overall_satisfaction ~69%. Outputs to `stonegrove_nss_responses.csv`.

---

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
- [x] **Engagement system as gap amplifier** – engagement already modifies marks (0.88–1.12). Widening the band, adding realistic weekly variation (bad weeks, exam stress), or making engagement more sensitive to SES/personality would amplify compounding effects over years.


---

## What's next (after progression + longitudinal)

1. [x] **5 cohorts × 7 years loop** – full longitudinal simulation. Done.
2. [x] **USER_GUIDE.md** – run pipeline, read data. Done: `docs/USER_GUIDE.md` exists.
