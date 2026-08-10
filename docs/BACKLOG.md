# Stonegrove Simulation — Backlog

Items here are deferred because they require design decisions, interact with other changes in flight, or need a full pipeline re-run to validate.

---

## Wire `first_gen` into Other Calculations

**Added**: 2026-05-03
**Status**: Code complete 2026-08-08 — **awaiting its own pipeline re-run and re-validation.**

Wired into both targets:

- **Progression log-odds** (`core_systems/progression_system.py` + `config/year_progression_rules.yaml`): `first_gen_progression: -0.20`, `first_gen_withdrawal: 0.15`. Nets ~+1.4pp withdrawal among passing first-gen students.
- **Assessment marks** (`core_systems/assessment_system.py` + `config/assessment_modifiers.yaml`): `first_gen_modifiers` keyed by programme year — `{1: 0.96, 2: 0.99, 3: 1.00}`, ≈ −2.4/−0.6/0 marks on a base-60 student. Concentrated in the transition year.
- **dim_students**: already carried through by `build_relational_outputs.py`; no change needed.

Both read their coefficients from config with a default of no-effect, so the code is inert if the config keys are removed.

**Calibration (2026-08-08)**: coefficients were chosen from a measured counterfactual against the corrected 19.06pp baseline, not estimated. Key finding: **Y1 carries zero weight in the degree average**, so the largest penalty (Y1, −2.4 marks) does not touch the awarding gap at all — it acts through progression, Y1 pass/fail and the enrolment survey. Only the Y2 modifier moves the gap.

Measured options: `.96/.98/.99` → 19.99pp (+0.93pp); **`.96/.99/1.0` → 19.30pp (+0.24pp, chosen)**; `.96/1.0/1.0` → 19.06pp (no change). The chosen set keeps the full Year 1 effect doing real work on continuation while leaving headroom inside the documented ~18–20pp band for the progression effect, which the counterfactual could not predict (it holds the graduating population fixed; worth ~±0.5–1pp).

`first_gen` is treated as a legitimate sixth emergent channel alongside SES, education and disability. No compensating change was made to the SES or education modifiers.

**Still to do**: re-run and re-validate. If the gap overshoots ~20pp, the SES gradient is the dial to shave first.

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

## ~~BUG: Enrolment Survey — three dead signal paths~~ RESOLVED

**Added**: 2026-07-03
**Fixed**: `9fba2a0` (2026-07-04) · **Validated**: 2026-08-08 pipeline re-run
**Status**: Done. `fact_enrolment_survey` changed in the re-run, as expected; all other tables unaffected.

1. **Column name mismatch** (`core_systems/enrolment_survey_system.py:293`): reads `row.get("programme_code")` but the enrolled dataframe column is `program_code`. `career_prospects` is always 0.5, so the programme signal in `career_clarity`/`career_confidence` is dead.
2. **Nonexistent motivation dimension** (`core_systems/enrolment_survey_system.py:284`): reads `motivation_career_development`, but the generated dimension is `career_focus` (column `motivation_career_focus`). Always 0.5.
3. **Engagement proxy never populated** (`core_systems/enrolment_survey_system.py:245-247, 281`): looks for `academic_engagement`/`participation_score`/`attendance_rate` on the enrolled dataframe, which has no engagement columns — the system is never passed `weekly_df`. Result: response rate is flat 0.82 for everyone (config promises engagement-nudged non-response), and the engagement terms in `support_satisfaction` and `belonging_*` do nothing. Fix: pass `weekly_df` into `generate_responses` in `run_year` and aggregate per student (as NSS does).

Net effect: `fact_enrolment_survey` currently runs on year-arc, SES, personality, and first_gen only.

---

## ~~BUG: Degree classification ignores Year 2 marks~~ RESOLVED

**Added**: 2026-07-03
**Fixed**: `9fba2a0` (2026-07-04) · **Validated**: 2026-08-08 pipeline re-run
**Status**: Done. This was the only fix to move a headline number: the Elf–Dwarf good-degree gap went from **16.7pp → 19.03pp** once Y2 marks were correctly folded back in at ⅓ weight. Pass rate, withdrawal rate, mean mark, SES gap and the flat gender gap were all unchanged. The corrected 19.03pp now matches the ~19pp figure `docs/CALCULATIONS.md` already documented as the design target — the bug had been suppressing the gap below its intended calibration.

`run_year` passes only the **current year's** `assessment_df` as `all_assessment_df` to `GraduateOutcomesSystem.generate_outcomes` (`run_longitudinal_pipeline.py` step 5). Graduating students only have Y3 rows in it, so the documented Y2 ⅓ : Y3 ⅔ weighting silently collapses to a Y3-only mean (`_compute_degree_classifications` normalises by the weight it actually finds). Affects `degree_classification` and `degree_weighted_avg` in `fact_graduate_outcomes` and `fact_good_honours` — i.e. the headline awarding-gap numbers.

Fix: accumulate assessment history across years in the main loop (mirroring `accumulated_progression`) and pass that instead. Needs re-run + re-validation of the attainment gap afterwards.

---

## ~~BUG: `is_repeat_year` inconsistent between Enrolment Survey and NSS~~ RESOLVED

**Added**: 2026-07-03
**Fixed**: `9fba2a0` (2026-07-04) · **Validated**: 2026-08-08 pipeline re-run
**Status**: Done. Enrolment survey now derives the flag from current-year status, matching NSS.

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
