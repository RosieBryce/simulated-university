# Current focus

**Last updated**: 25 Feb 2026

## Completed this session (25 Feb 2026)

- **NSS system built and wired** — `core_systems/nss_system.py` + `config/nss_modifiers.yaml`. 7 themes + overall_satisfaction (1–5). Generates one response per Yr3 student (including repeating Yr3) per academic year. 2,325 responses across 5 cohorts.
- **NSS calibrated to real UK NSS benchmarks** — org & management lowest (~60% positive); A&F most variable (mark-sensitive, SD=0.68); student_voice ~67%; overall_satisfaction ~69%.
- **Gender clan overrides wired** — `_determine_gender` now supports full `gender_distribution` dict per clan (as well as `neuter_probability` shorthand). Neuter probabilities: obsidian 12%, slate 12% (genderless deity Durren), yew 11% (androgynous aesthetic), alabaster 12%, all others 10%.
- **Sample data on git** — all pipeline outputs committed. Weekly engagement (~68 MB) split into per-year files in `data/weekly_engagement/` (3–12 MB each). Legacy/relational/archive dirs gitignored.
- **Relational schema updated** — `build_relational_outputs.py` now produces 10 tables (was 8). Added `fact_graduate_outcomes` and `fact_nss_responses`. Fixed: `combined_mark` in `fact_assessment`; `semester` in `fact_weekly_engagement` and `dim_modules`; correct four assessment dates in `dim_academic_years`. Loader handles both combined weekly file and per-year splits.

## Previously completed (earlier in Feb 2026)

- **Semester structure wired** — `config/module_characteristics.csv` has `semester` column. Weekly engagement has `semester` column.
- **Two assessment components per module** — MIDTERM + FINAL rows, `combined_mark = 0.4 × MIDTERM + 0.6 × FINAL`.
- **Assessment dates per semester** — S1: Nov 1 / Dec 15; S2: Mar 15 / May 15.
- **Progression updated** — FINAL rows + `combined_mark`. Withdrawal: 5–6%.
- **Withdrawal-after-fail refinement** — year investment effect (Y1 more likely to withdraw after fail than Y3) + prior repeat discouragement wired in `year_progression_rules.yaml`.
- **Graduate outcomes system** — `core_systems/graduate_outcomes_system.py` + `config/graduate_outcomes.yaml`. Degree classification (Y2 1/3, Y3 2/3), employment/sector/salary/professional level. SES gradient on salary and professional employment.
- **Gender awarding gap** — design decision: flat by design, no modifier.
- **Disability modifier tuning** — decision: leave gap (6.3pp overall, ~5pp across all SES bands) for analysts/users.
- **`metaanalysis/student_paths.py`** — per-student trajectories, archetype distributions, species/SES breakdowns, case studies, coherence checks.
- **SCHEMA.md v2.2** — all tables documented including `stonegrove_graduate_outcomes.csv` and `stonegrove_nss_responses.csv`.

---

## Priority queue (next up)

### 1. Module trailing
Students who pass the year overall but have one module < 40 trail it as a RESIT in the following year. Complex: touches `progression_system.py` (detect trailing modules), `assessment_system.py` (generate RESIT rows), `docs/SCHEMA.md`. See backlog for full spec.

### 2. `caring_responsibilities` in student model
Add field to `student_generation_pipeline.py` first, then re-introduce the progression modifier in `_apply_modifiers`. Currently dead code (removed from progression; field never generated).

### 3. Status rolls / life events
Optional random events at year start (e.g. family crisis, sudden free time). See backlog.

---

## Blocked

(none)

## Design decisions (standing)

- **No direct clan mark modifier** — `config/archive/clan_assessment_modifiers.csv` archived; gaps must emerge from SES/education/disability. Do not re-wire.
- **No caring_responsibilities in progression** — field not generated; removed from modifier code. Add to student generation *first* before re-introducing the progression modifier.
- **Gender gap flat** — intentional; do not add direct gender modifier.
- **12-week engagement arc per module** — not split by semester; `semester` column = module assignment only.
