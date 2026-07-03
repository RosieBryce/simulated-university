# Stonegrove Simulation — Backlog

Items here are deferred because they require design decisions, interact with other changes in flight, or need a full pipeline re-run to validate.

---

## Wire `first_gen` into Other Calculations

**Added**: 2026-05-03
**Status**: Deferred — `first_gen` is generated and used in the Enrolment Survey, but not yet wired into:

- **Progression log-odds model** (`config/year_progression_rules.yaml` + `core_systems/progression_system.py`): first-gen students have lower persistence rates in real UK data (~3–5pp lower continuation). Add as a small negative log-odds modifier (e.g. −0.15 to −0.25).
- **Assessment difficulty modifier** (`core_systems/assessment_system.py`): first-gen students may underperform relative to personality predictions, particularly in Year 1. Consider a small mark penalty (e.g. −2 to −3 marks on base mark before noise).
- **dim_students** in relational schema: `build_relational_outputs.py` already pulls all columns from `stonegrove_individual_students.csv`, so `first_gen` will appear in the relational output automatically once the pipeline is re-run.

**Why deferred**: Changing the mark and progression distributions affects the awarding gap and overall pass rates. Needs a pipeline re-run and re-validation before merging.

---

## Module Trailing (Resits)

**Added**: (from planning session)
**Status**: Deferred — needs bigger-picture thinking first

Interacts with:
- Award algorithm (resit marks in Year N+1, cap on classification)
- Assessment schema (new RESIT component_code)
- Possibly faculty rework (new module codes)

Recommend: tackle after a stable pipeline baseline exists (post all current changes merged and validated).

---

## BUG: Enrolment Survey — three dead signal paths

**Added**: 2026-07-03
**Status**: Confirmed bugs — all three cause a designed signal to silently collapse to its 0.5 fallback. Fixes are small but change the survey score distributions, so they need a pipeline re-run to validate.

1. **Column name mismatch** (`core_systems/enrolment_survey_system.py:293`): reads `row.get("programme_code")` but the enrolled dataframe column is `program_code`. `career_prospects` is always 0.5, so the programme signal in `career_clarity`/`career_confidence` is dead.
2. **Nonexistent motivation dimension** (`core_systems/enrolment_survey_system.py:284`): reads `motivation_career_development`, but the generated dimension is `career_focus` (column `motivation_career_focus`). Always 0.5.
3. **Engagement proxy never populated** (`core_systems/enrolment_survey_system.py:245-247, 281`): looks for `academic_engagement`/`participation_score`/`attendance_rate` on the enrolled dataframe, which has no engagement columns — the system is never passed `weekly_df`. Result: response rate is flat 0.82 for everyone (config promises engagement-nudged non-response), and the engagement terms in `support_satisfaction` and `belonging_*` do nothing. Fix: pass `weekly_df` into `generate_responses` in `run_year` and aggregate per student (as NSS does).

Net effect: `fact_enrolment_survey` currently runs on year-arc, SES, personality, and first_gen only.

---

## BUG: Degree classification ignores Year 2 marks

**Added**: 2026-07-03
**Status**: Confirmed bug.

`run_year` passes only the **current year's** `assessment_df` as `all_assessment_df` to `GraduateOutcomesSystem.generate_outcomes` (`run_longitudinal_pipeline.py` step 5). Graduating students only have Y3 rows in it, so the documented Y2 ⅓ : Y3 ⅔ weighting silently collapses to a Y3-only mean (`_compute_degree_classifications` normalises by the weight it actually finds). Affects `degree_classification` and `degree_weighted_avg` in `fact_graduate_outcomes` and `fact_good_honours` — i.e. the headline awarding-gap numbers.

Fix: accumulate assessment history across years in the main loop (mirroring `accumulated_progression`) and pass that instead. Needs re-run + re-validation of the attainment gap afterwards.

---

## BUG: `is_repeat_year` inconsistent between Enrolment Survey and NSS

**Added**: 2026-07-03
**Status**: Confirmed inconsistency.

- NSS: flags students **currently** repeating (status == 'repeating' this year). Correct.
- Enrolment survey (`core_systems/enrolment_survey_system.py:235-237`): flags anyone who has **ever** had status='repeating' in prior progression history — a student who repeated Y1 stays flagged in their Y2 and Y3 survey rows forever.

Fix: derive from the student's current-year status (as NSS does), or rename to `has_ever_repeated` if the historical meaning is wanted. Document whichever in SCHEMA.md.

---

## Realism: No persistent student ability term

**Added**: 2026-07-03
**Status**: Design gap — needs design decision + re-calibration.

Each year's marks are drawn fresh from the same trimodal base distribution; a student's year-to-year mark correlation arises only weakly via personality → engagement → mark modifier. Real students' marks are strongly autocorrelated across years. Consider a per-student latent ability term (drawn once at generation, feeding the base mark) so longitudinal analyses on the data behave realistically. Interacts with the awarding-gap calibration — needs re-validation.

---

## Realism: No compensation/condonement in progression

**Added**: 2026-07-03
**Status**: Design gap — interacts with Module Trailing (Resits) item above.

`ProgressionSystem` fails the year if **any** module's combined mark is below 40. UK regulations typically allow condoned passes (e.g. one module 30–39 with a passing average). Currently a strong student with one bad module faces the same repeat/withdraw roll as an across-the-board failer. Tackle together with resits.

---

## Realism: NSS re-surveys repeating Year 3 students

**Added**: 2026-07-03
**Status**: Design gap — minor.

A student who repeats Y3 gets an NSS row in both years. Real NSS surveys each student once (in their expected final year). Either exclude previously surveyed students or document the current behaviour as intentional (the `is_repeat_year` flag does make the duplicates identifiable).

---

## Realism: Graduate Outcomes non-response is uniform random

**Added**: 2026-07-03
**Status**: Design gap — minor.

`survey_responded` in graduate outcomes is a flat 70% coin flip. Real Graduate Outcomes response skews by outcome and demographics (unemployed and lower-SES graduates respond less), which matters if anyone uses the dataset to teach non-response bias. Consider a log-odds response model like the NSS one (engagement-nudged), driven by outcome_type and SES.

---
