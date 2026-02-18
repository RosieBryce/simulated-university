# Current focus

**Last updated**: Feb 2026

## Recently completed

- Emergent awarding gap (8.8pp Elf > Dwarf) from agent-level factors
- Config-driven programme selection (trait mapping CSV, affinity multipliers)
- All high-severity bugs fixed (disability sampling, dates, SES, species, seed reset)
- Medium-severity bugs fixed (modules_passed counting, .values alignment, metadata cohorts)
- Cleanup: deleted unused program_affinity_system.py and module_characteristics_system.py, removed unused imports
- Documentation: CALCULATIONS.md, SCHEMA.md, DATA_IO_PLAN.md, README.md all updated

## Priority queue

### 1. Semester structure (medium effort)
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
