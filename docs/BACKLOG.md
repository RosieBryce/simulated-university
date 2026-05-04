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
