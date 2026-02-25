# Stonegrove University Simulation - Design Document

**Version**: 2.2 (Engagement overhaul, progression scale fix, config extraction)
**Last Updated**: 25 February 2026
**Status**: Active — longitudinal pipeline running

---

## Purpose & Vision

This is a **research sandbox** for exploring higher education systems through simulation. It models individual students over multiple years, generating realistic longitudinal data that mirrors how real university student record systems work.

### Goals

- **Open-source, shareable**: GitHub + supporting website
- **Audience**: UK HE professionals (learning technologists, data scientists, education developers), researchers, collaborators
- **Use cases**: AI hackathons, awarding gap analysis, intervention impact modeling, product prototyping
- **Philosophy**: Plain data outputs with transparent assumptions; users analyze as they please

### Scope

- **Current**: Individual-level student modeling (personality, motivation, enrollment, engagement)
- **Phase 2**: Assessment, performance, progression, attrition (Year 1 → Year 2 → Year 3 → graduation)
- **Future**: Support services (library, wellbeing, disability), interventions, extra-curriculars
- **Ultimate stretch**: Live web visualization (1 day = 1 minute)

---

## Core Design Principles

### 1. **Database-Like Structure**

Simulates how a real university student record system works:
- **Persistent `student_id`** across all years and attempts
- **Academic year = calendar year**: Format `"1046-47"`, `"1047-48"` (Middle Earth year codes). Start year: 1046-47. Not "student year 1, 2, 3" — use `programme_year` (1, 2, 3) for year of study.
- **Status-driven flow**: enrolled → pass/fail → progress/repeat/withdraw → graduated/withdrawn
- **Granular records**: One row per event (assessment, weekly engagement, etc.)

### 2. **Student-Level Detail**

Everything traces back to individual students. Aggregated stats are for validation, not primary outputs.

### 3. **Config-Driven, CSV-First**

- All important parameters editable (clan traits, programme affinities, disability impacts, progression rules)
- Prefer CSV over YAML for tabular configs (migration path defined)
- Calculations documented in `CALCULATIONS.md`

### 4. **Reproducible**

- Random seeds tracked in metadata
- Git tags for major versions
- Same seed → same results

### 5. **Transparent**

- Open policy on assumptions
- Protected characteristics included; users compute gaps themselves
- No hidden modifiers

---

## Data Model

### Core Entities

#### **Students** (`stonegrove_individual_students.csv`)
- Persistent identity: `student_id`
- Demographics: species, clan, gender, age
- Characteristics: personality traits, motivation dimensions, disabilities, socio-economic rank
- **Longitudinal**: Same student appears once per academic year (if enrolled)

#### **Enrollment** (`stonegrove_enrollment.csv`)
- One row per student per academic year
- Fields: `student_id`, `academic_year` (calendar, e.g. "1046-47"), `programme_code`, `programme_name`, `programme_year` (1, 2, 3), `status` (enrolled, repeating, withdrawn, graduated), **`status_change_at`** (start of year — when this status took effect; no in-year withdrawals, but analysts need this timestamp)
- Modules assigned: `year1_modules`, `year2_modules`, `year3_modules` (pipe-delimited lists)

#### **Engagement** (`stonegrove_weekly_engagement.csv`)
- One row per student per week per module
- Fields: `student_id`, `academic_year`, `week_number`, `module_title`, `attendance_rate`, `participation_score`, `academic_engagement`, `social_engagement`, `stress_level`
- Generated for all enrolled students each week

#### **Assessment** (`stonegrove_assessment_events.csv`)
- One row per student per module per assessment
- Fields: `student_id`, `academic_year`, **`module_code`**, **`component_code`** (for future: more assessments per module), `module_title`, `assessment_type`, `assessment_mark`, `grade`, `assessment_date`
- Generated at end of module (one assessment per module per year for now)

#### **Semester summaries**
- **Not a core output.** Analysts can derive from `stonegrove_weekly_engagement.csv` if needed. We do not produce `stonegrove_semester_engagement.csv` as part of the longitudinal design.

### Key Fields Across Tables

Every domain table includes:
- `student_id` (persistent)
- `academic_year` (calendar string: "1046-47", "1047-48", ...)
- `programme_code` (for filtering/joining)
- `programme_year` (1, 2, 3 — year of study in programme)

---

## Longitudinal Flow

### Year Progression Logic

1. **Year 1 Start**
   - Generate 500 new students
   - Enroll in programmes based on clan affinities + personality
   - Assign Year 1 modules
   - Generate weekly engagement (12 weeks)
   - Generate assessment marks (end of module)

2. **Year 1 End → Year 2 Decision**
   - Calculate pass/fail per module
   - Determine overall year outcome (pass if all modules ≥ 40)
   - **If pass**: Student may progress OR withdraw (probability + traits)
   - **If fail**: Student may repeat OR withdraw (probability + traits)
   - **If withdraw**: Status = "withdrawn", no more records

3. **Year 2 Start** (if progressed)
   - Same `student_id`, `academic_year` = "1047-48"
   - Assign Year 2 modules
   - Generate engagement + assessment

4. **Repeat** for Years 2 → 3, 3 → graduation

**Note**: No in-year withdrawals. Status changes (enrolled/repeating/withdrawn/graduated) apply at **start of year** only; `status_change_at` records when the status took effect for analysts.

### Status Values

- `enrolled`: Active student in current year
- `repeating`: Re-taking a year (same `programme_year`, new `academic_year`)
- `withdrawn`: Left university (no more records)
- `graduated`: Completed programme (no more records)

### Programme Structure

- **Fixed lengths**: 3-year or 4-year programmes (from curriculum Excel)
- **No flexible durations**: Keeps model simple

---

## File Naming Convention

All outputs in `data/`:

- `stonegrove_individual_students.csv` - Student characteristics (one row per student per academic year)
- `stonegrove_enrollment.csv` - Enrollment records (one row per student per academic year; includes `status_change_at`)
- `stonegrove_weekly_engagement.csv` - Weekly engagement (one row per student per week per module)
- `stonegrove_assessment_events.csv` - Assessment marks (one row per student per module per assessment; includes `module_code`, `component_code`)
- `data/metadata.json` - Version, seed, generation timestamp

*(Semester summaries are not a core output; derive from weekly engagement if needed.)*

---

## Configuration Files

### Active YAML configs

- `config/clan_personality_specifications.yaml` — clan personality ranges + `health_tendencies` (per-clan disability prevalence rates)
- `config/clan_program_affinities.yaml` — clan–programme affinity scores + selection settings (multipliers, floor)
- `config/year_progression_rules.yaml` — base progression/repeat/withdrawal probabilities + trait modifier weights + `trait_modifier_scale`
- `config/engagement_modifiers.yaml` — per-disability base adjustments and noise std_extra; SES rank modifiers; temporal arc (early/midterm/exam)
- `config/assessment_modifiers.yaml` — education modifier (academic/vocational/no_qualifications) and SES rank mark multipliers

### Active CSV configs (tabular, Excel-editable)

- `config/module_characteristics.csv` — 353 modules: difficulty_level, assessment_type, mark_modifier
- `config/programme_characteristics.csv` — 44 programmes: stress_level, social_intensity, creativity_requirements
- `config/clan_socioeconomic_distributions.csv` — per-clan SES rank and education distributions
- `config/disability_assessment_modifiers.csv` — mark modifiers per disability type
- `config/trait_programme_mapping.csv` — maps student traits to programme characteristics for enrollment fit scoring
- `config/personality_refinement_modifiers.yaml` — trait adjustments for disability, SES, age

### Archived (config/archive/)

- `disability_distribution.yaml` — superseded by `health_tendencies` in `clan_personality_specifications.yaml`
- `clan_assessment_modifiers.csv` — archived by design: direct clan mark modifiers removed; gaps now emergent from SES/education/disability
- Various old YAML formats migrated to CSV

### No analyst-facing assessment config

Mark distributions are for internal validation only. Analysts work with raw assessment data.

### Source Data (Excel, read-only)

- `Instructions and guides/Stonegrove_University_Curriculum.xlsx` - Programme and module structure

---

## Pipeline Architecture

### Current Pipeline (Year 1 Only)

```
student_generation_pipeline.py
  → stonegrove_individual_students.csv

program_enrollment_system.py
  → stonegrove_enrolled_students.csv

engagement_system.py
  → stonegrove_weekly_engagement.csv
  → stonegrove_semester_engagement.csv
```

### Target Pipeline (Longitudinal, 5 cohorts × 7 years)

We are **not** only tracking one cohort. When we re-enrol a cohort to Level 2, we **also** intake a **new** Level 1 cohort. We run **5 cohorts** in total.

- **First cohort**: Year 1 (1046-47) → Year 2 (1047-48) → Year 3 (1048-49) → **graduate** end of 1048-49 (3 years).
- **Then** 4 more cohorts graduate in 1049-50, 1050-51, 1051-52, 1052-53.
- **Total simulation**: **7 academic years** (1046-47 through 1052-53).

So in 1047-48 we have: Cohort 1 in Year 2, Cohort 2 in Year 1. In 1048-49: Cohort 1 in Year 3, Cohort 2 in Year 2, Cohort 3 in Year 1. And so on.

```
For each academic_year from "1046-47" to "1052-53":

1. New cohort (Year 1 only): student_generation_pipeline.py
   → Generate new Level 1 students for this year (e.g. 500)

2. program_enrollment_system.py
   → Enroll all active students (new cohort + progressing/repeating from previous year) in programmes, assign modules for their programme_year

3. engagement_system.py
   → Generate weekly engagement for current academic_year

4. assessment_system.py (NEW)
   → Generate assessment marks at end of modules

5. progression_system.py (NEW)
   → Calculate pass/fail, determine progression/repeat/withdrawal (status change at start of next year)
   → Produce next academic_year enrollment view

6. Append/write outputs for this academic_year (enrollment, engagement, assessment)

7. metaanalysis/validate_model_outputs.py (optional)
   → Check distributions, correlations, edge cases
```

### Pipeline Execution

- **Must run full pipeline**: Cannot run just student generation
- **Sequential**: Each step depends on previous outputs
- **Reproducible**: Seed passed through all systems

---

## Assessment Model

### Timing

- **End of module**: One assessment per module per year
- **No mid-term assessments**: Keep it simple

### Calculation

- **Purely assessment-based**: Marks → grades
- **Engagement affects marks**: Modifier from weekly engagement (attendance, participation, academic engagement)
- **Modifiers**: Species, disability, clan, socio-economic status (documented in CALCULATIONS.md)

### Output

- One row per student per module per assessment
- Fields: `student_id`, `academic_year`, **`module_code`**, **`component_code`** (for future: more assessments per module), `module_title`, `assessment_type`, `assessment_mark`, `grade`, `assessment_date`

---

## Progression Model

### Student-Level Decisions

- **Not top-down**: No "X% of students progress"
- **Emergent**: Each student's outcome based on:
  - Assessment marks (pass/fail threshold)
  - Personality traits (conscientiousness → more likely to progress)
  - Motivation (academic drive → more likely to progress)
  - Random variation

### Rules (in `config/year_progression_rules.yaml`)

- Short file: **base probability** (e.g. default progression rate) **plus** individual modifiers (by trait, motivation, performance). Everything else is modelled at student level.
- Pass threshold: e.g. all modules ≥ 40
- Progression / withdrawal / repeat: base rate + modifiers

---

## Documentation Structure

### `docs/`

- **DESIGN.md** (this file) - Overall architecture
- **DATA_IO_PLAN.md** - Inputs/outputs, regeneration order
- **SCHEMA.md** - Column definitions for all CSVs
- **CALCULATIONS.md** - Formulas, modifiers, assumptions
- **USER_GUIDE.md** - How to run the pipeline, read data

### `README.md`

- Quick start
- Project overview
- Links to docs

### `docs/PROJECT_SUMMARY.md`

- Pick-up guide (where are we, what's next)
- Expected files checklist

### `project_tracker/`

- **Tickets and progress**: Record tickets, log work, track current focus and backlog. For both human and AI — so either can pick up and see what's next.
- See `project_tracker/README.md` for how to use.

---

## Versioning & Metadata

### `data/metadata.json`

```json
{
  "model_version": "v2.0-longitudinal",
  "git_commit": "abc123...",
  "random_seed": 42,
  "generation_timestamp": "2026-02-13T10:30:00Z",
  "config_versions": {
    "clan_traits": "v1.0",
    "progression_rules": "v1.0"
  },
  "cohort_size": 500,
  "years_generated": 7,
  "academic_years": ["1046-47", "1047-48", "1048-49", "1049-50", "1050-51", "1051-52", "1052-53"],
  "cohorts": 5
}
```

### Git Tags

- Major milestones: `v1.0-population`, `v2.0-longitudinal`, `v3.0-interventions`
- Referenced in docs

---

## Migration Path (completed)

Phases 1–3 are complete as of February 2026:

- All domain tables include `academic_year` and `programme_year`
- `assessment_system.py` and `progression_system.py` built and running
- Enrollment system handles multi-year flow (new cohorts + continuing students)
- Engagement system generates temporal arc, AR(1) weekly variation, disability/SES modifiers
- Module and programme characteristics migrated from YAML to CSV
- `year_progression_rules.yaml`, `engagement_modifiers.yaml`, `assessment_modifiers.yaml` in place
- SCHEMA.md, CALCULATIONS.md, USER_GUIDE.md written and maintained

See `project_tracker/BACKLOG.md` for remaining open work (semester structure, gender gap, validation scripts).

---

## Open Questions / Future Work

- Support services (library, wellbeing, disability) - **Later**
- Extra-curricular activities - **Later**
- Intervention modeling - **Later**
- Case study generation tools - **Phase N**
- Example notebooks - **Eventually**
- Live web visualization - **Ultimate stretch**

---

## Success Criteria

### Phase 2 (Assessment + Progression)

- Generate assessment marks for Year 1
- Calculate pass/fail per module
- Determine year outcomes (pass/fail)
- Model progression (progress/repeat/withdraw)
- Generate Year 2 enrollment records
- Repeat for Years 2 → 3, 3 → graduation
- Generate 7 years of data (5 cohorts; first cohort graduates in year 3, then 4 more cohorts)
- All CSVs use calendar `academic_year` ("1046-47", …), include `programme_year`, `status`, and enrollment includes `status_change_at`
- Assessment events include `module_code`, `component_code`

### Documentation

- SCHEMA.md complete
- CALCULATIONS.md complete
- USER_GUIDE.md complete
- All assumptions documented

### Validation

- Progression rates realistic (e.g., 80-90% Year 1 → Year 2)
- Withdrawal rates realistic (e.g., 5-15% per year)
- Grade distributions realistic (skewed toward 56-64)
- Awarding gaps visible in data (users can compute)
