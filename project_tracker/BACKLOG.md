# Backlog

Items to do next. Move to CURRENT when starting. Aligned with DESIGN.md Phase 1–3 migration path and Phase 2 success criteria.

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
- [ ] **Update DATA_IO_PLAN.md** – 7-year, 5-cohort flow and new file list.
- [ ] SCHEMA.md, CALCULATIONS.md – update for longitudinal schema (status, status_change_at, programme_year, academic_year everywhere).
- [ ] Update README.md with links to docs.

## Validation (DESIGN Success Criteria)
- [ ] **Metaanalysis / validate_model_outputs.py** – internal checks: progression rates (e.g. 80–90% Y1→Y2), withdrawal (5–15%), grade distributions, awarding gaps visible.
- [ ] No analyst-facing assessment config (internal only).

## Optional / nice-to-have
- [ ] **Config path constant** – shared `paths.py` or env for `data/`, `config/`, `visualizations/`.
- [x] Single run script `run_pipeline.py` at root.

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
