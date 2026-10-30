# Stonegrove Simulation — Backlog

Items here are deferred because they require design decisions, interact with other changes in flight, or need a full pipeline re-run to validate.

---

## BUG: Mis-coded Modules sheet strands two thirds of students before graduation

**Added**: 2026-10-29
**Status**: Fixed and re-run on branch `claude/stoic-dirac-b41913` (2026-10-30, 138 min). `data/relational/` is regenerated and passes the Section 0 integrity checks; docs and site counts updated. **Released as v2.7.0** (Hub re-profile still to do, see below).

**What happens.** In the v2.6.0 dataset 27 of the 55 programmes never have a `programme_year` 3 enrolment, and `fact_good_honours` has rows for only 21 programmes. Science & Engineering has **zero** graduates; Health & Education has graduates from Somatic Wellbeing Enquiry only (538); Culture & Social Sciences from Geography and History only. Of 35,000 students, **16,873 simply vanish**: their last `fact_enrollment` row is status `enrolled` (14,885 at Year 2, 1,988 at Year 3) with no `fact_progression` row and nothing afterwards — not withdrawn, not graduated. 84% of the 6,039 graduates come from two faculties (Craft, Art & Architecture 3,648; Business & Law 1,451).

| Faculty | Entrants | Graduates | Share |
|---|---|---|---|
| Business & Law School | 2,849 | 1,451 | 51% |
| Craft, Art & Architecture | 7,459 | 3,648 | 49% |
| Culture & Social Sciences | 9,533 | 402 | 4% |
| Health & Education | 7,971 | 538 | 7% |
| Science & Engineering | 7,188 | 0 | 0% |

**Root cause — data, not code.** In the canonical curriculum `curriculum-and-lore/Stonegrove_University_Curriculum_v7.xlsx`, Modules sheet, the `Programme code` column is wrong on **385 of 660 rows**: 312 of them carry codes that do not exist in the Programmes sheet (`4_2_23`, `3_6_26`, `5_3_22`…). The `Programme` name column and the `Module Code` column (which encodes faculty/department/programme, e.g. `441102` → `4_1_1`) are both correct; only the code column is off. The pattern is an Excel fill-handle series: within each affected programme the code increments by one per row (Education Studies' four Year 1 modules are coded `4_1_1`, `4_1_2`, `4_1_3`, `4_1_4`), the classic autofill behaviour on text ending in a digit. It came in with the v7 faculty rework (`a28ca4c`). The twenty programmes in Business & Law and Craft, plus Geography and History, happened to be unaffected, which is why the headline tables looked plausible. `config/module_characteristics.csv` was derived from the sheet and carries the same 385 errors.

**How it propagates.** `ProgramEnrollmentSystem.get_modules_for_programme_year` (`core_systems/program_enrollment_system.py`) filters the Modules sheet on `Programme code` + `Year`, so 34 programmes get an empty module list for Year 2 and/or Year 3 (and a short list for Year 1 — Education Studies students take one module in their first year, not four). An empty list means no engagement rows, no assessment rows, and because `ProgressionSystem.compute_progression` aggregates *from* assessment rows, no progression row. `run_longitudinal_pipeline.main` builds next year's continuing cohort from the progression output, so the student is silently dropped. Graduate outcomes only ever sees students who passed a Year 3 with marks, so the programme never appears in `fact_good_honours` / `fact_graduate_outcomes`. NSS still surveys the stranded Year 3 students (it keys on `programme_year == 3` in the enrolment frame), which is why Physiotherapy, OT, Pharmacy and Social Work have NSS rows but no graduates.

**Tables affected.** `fact_enrollment` (dead-end rows), `fact_progression` (no rows for 16,873 student-years), `fact_assessment` and `fact_weekly_engagement` (missing years; `modules_total` of 1–3 instead of 4 in Year 1 for affected programmes), `fact_good_honours` and `fact_graduate_outcomes` (21 programmes instead of 55, 6,039 graduates instead of an expected ~13,000 from the five graduating cohorts), `fact_nss_responses` (Year 3 respondents with no marks), `dim_modules` (333 rows — only the modules anyone actually sat — instead of 642 distinct module codes). **Headline figures:** the ≈20pp Elf–Dwarf good-degree gap in `docs/index.html`, `docs/data/gap-summary.csv` and `docs/explore/` is computed from `fact_good_honours` (`scripts/aggregate_gap.py`), i.e. from a graduate population drawn almost entirely from two faculties. Dwarves are 59.8% of entrants but 53.3% of graduates. The gap (Dwarf 44.5% vs Elf 64.3%) will move once all 55 programmes graduate and will need re-calibrating against the documented 18–20pp band.

**Fix applied (this branch).**
- `Programme code` rewritten from the programme name on all 385 bad rows of the Modules sheet (openpyxl, in place; every other cell verified identical) and the matching 385 rows of `config/module_characteristics.csv` (column replaced verbatim, all other columns byte-identical). Before: 34 programmes with an empty year; after: 0, every programme has 4 modules in each of Years 1–3, and `AssessmentSystem.module_code_lookup` resolves all 660 (programme, title) pairs.
- New `scripts/validate_curriculum.py` — fails (exit 1) if any module row's code disagrees with its programme name, any code is unknown, any programme lacks modules in any year, or the CSV disagrees with the sheet. Run it before any pipeline run.
- `ProgramEnrollmentSystem._load_curriculum_data` now prints a WARNING listing any programme with an empty year at load time.

**Re-run result (2026-10-30).** Bundled with UK-style condonement (no module under 30, at most one in 30-39) and a (programme, year, title) module-code lookup that fixes Brewcraft. 35,000 students, 87,467 student-years, 20,492 graduates from all 55 programmes, `dim_modules` 642 rows. Year fail 5.8 / 5.3 / 10.5% (Y1 / Y2 / Y3; without condonement 17.5 / 15.5 / 23%), first-year non-continuation 6.3% (HESA roughly 5-6%), completion 83% for the four earliest cohorts (OfS B3 threshold 75%). Elf-Dwarf good-degree gap **22.9pp** (Elf 58.0%, Dwarf 35.1%), above the 18-20pp band; accepted by Rosie rather than recalibrated. Overall good-degree rate fell from 53.6% to about 45% because condoned weaker students now graduate. Year 3 fail rate is 1.8x Year 1 (validator warns).

**Still to do.**
1. Re-profile the Stonegrove Hub. The Hub lives on `feat/hub-phase0`, which does not have this branch's fix, so merge this branch into it first, then run `make_hub_extracts.py`, `generate_sources.py`, `build_estate.py`, `make_zips.py` and check `hub/source/values.yaml` for new null keys. Its storylines and in-world documents quote programme structure that has now changed (all 55 programmes graduate).
2. ~~Cut a new GitHub release~~ Done: v2.7.0, download button updated.
3. Module characteristics are keyed by module title alone: 23 titles shared across programmes differ in difficulty and collapse to one row, so `dim_modules.assessment_type` for 523801 shows the Year 3 value. Key them by (programme, year, title).
4. Resits are not modelled; Year 3 fails run at 1.8x Year 1.

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
