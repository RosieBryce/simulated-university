# Current focus

**Last updated**: 25 Feb 2026

## Recently completed

- Validation script built and all 4 WARNs resolved:
  - Graduate/withdrawal rate (was 0%): fixed validate_outputs.py to read `status` not `year_outcome`
  - SES gap (was 27.6pp): SES modifier narrowed from 0.80–1.20 to 0.91–1.09 → now 14.7pp
  - Difficulty→mark correlation (was +0.022): strengthened modifier slope + added deterministic within-year difficulty jitter to migration → now -0.121
  - Mark progression now realistic: Year 1: 61.2, Year 2: 59.3, Year 3: 56.8
- Emergent awarding gap (6.0pp Elf > Dwarf) from agent-level factors
- All high-severity bugs fixed (disability sampling, dates, SES, species, seed reset, modules_passed)
- Pipeline crash fix + engagement append bug fixed
- Relational schema: 4 dims + 4 facts in data/relational/ (build_relational_outputs.py)
- Module codes sourced from curriculum Excel (one-time migration, no more runtime computation)
- Assessment year-level bug fixed: year 2/3 students now assessed on correct modules
- Config fully populated: all 353 modules, all 44 programmes, no nulls
- Config folder cleaned: 8 unused files archived, 10 active files remain

## Priority queue

### 1. Awarding gap and modifier tuning
- Wire in clan assessment modifier (config/archive/clan_assessment_modifiers.csv ready)
- Gender gap (via engagement patterns, not direct modifiers)
- Disability modifier tuning (decide Stonegrove's support story)
- Engagement band too narrow — widen for more realistic variation

### 3. Remaining medium bugs
- Gender clan overrides bypassed (sample_gender hardcoded 45/45/10)
- Semester hardcoded to 1 (engagement_system.py:459)
- Semester engagement records missing academic_year

### 4. Semester structure (medium effort)
- Assign each module to semester 1 or 2 in curriculum Excel
- Two assessment dates per year (Jan + May)
- Engagement system generates both semesters

### 5. Later
- Progression: withdrawal-after-fail refinement
- Caring responsibilities field
- Sample data on git
- Status rolls, interventions, case study extraction

## Blocked

- (none)
