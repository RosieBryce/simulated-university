# Current focus

**Last updated**: Feb 2026

## Recently completed

- Emergent awarding gap (8.8pp Elf > Dwarf) from agent-level factors
- Config-driven programme selection (trait mapping CSV, affinity multipliers)
- All high-severity bugs fixed (disability sampling, dates, SES, species, seed reset)
- Medium-severity bugs fixed (modules_passed counting, .values alignment, metadata cohorts)
- Cleanup: deleted unused program_affinity_system.py and module_characteristics_system.py, removed unused imports
- Documentation: CALCULATIONS.md, SCHEMA.md, DATA_IO_PLAN.md, README.md all updated
- Pipeline crash fix: removed mid-loop engagement disk write; engagement now accumulates in memory and writes once at end
- Engagement append bug fixed: re-running the pipeline no longer doubles rows (clean overwrite every run)
- Deprecated/orphaned CSVs archived: university_population, enrolled_population, assessment_marks, curriculum_assessment_marks, enrolled_students, semester_engagement

## Priority queue

### 1. Relational database outputs
- Normalise CSV outputs into a clean star schema: dim_students, dim_modules, dim_programmes, dim_academic_years, fact_enrollment, fact_weekly_engagement, fact_assessment, fact_progression
- Remove denormalised columns (demographics repeated per row, module characteristics repeated per engagement row)
- Add student_id to individual_students output
- See schema agreed in session: 4 dims, 4 facts

### 2. Assessment year-level bug (HIGH — affects all progression analysis)
- Continuing students (year 2/3) assessed on year-1 modules instead of their actual year-level modules
- Fix in assessment_system.py — must use programme_year to select correct module set
- dim_modules will fill out to ~96/131/126 per year once fixed

### 3. Config fine-tuning
- Tune after database outputs are sorted
- Includes: clan/SES modifiers, disability modifiers, engagement band width, gender gap, awarding gap validation

### 3. Semester structure (medium effort)
- Add semester 1/2 to modules in curriculum config
- Two assessment dates per academic year (Jan + May)
- Engagement system generates both semesters
- Fixes the "semester hardcoded to 1" and "semester missing academic_year" bugs

### 2. Validation script
- Metaanalysis script checking progression rates, withdrawal rates, grade distributions, awarding gaps
- Needed before further tuning

### 3. Awarding gap refinement
- Gender gap (via engagement patterns, not direct modifiers)
- Disability modifier tuning (decide Stonegrove's support story)
- Engagement system as gap amplifier (wider band, realistic variation)

### 4. Remaining medium bugs
- Personality column prefix mismatch in ModuleCharacteristicsSystem (now deleted — N/A)
- Gender clan overrides bypassed (sample_gender hardcoded 45/45/10)
- Weekly engagement clusters in narrow band

### 5. Later
- Progression: withdrawal-after-fail refinement
- Caring responsibilities field
- Sample data on git
- Status rolls, interventions, case study extraction

## Blocked

- (none)
