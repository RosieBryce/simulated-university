# Current focus

**Last updated**: Feb 2026

## Recently completed

- Emergent awarding gap (8.8pp Elf > Dwarf) from agent-level factors — see DESIGN_DECISIONS.md
- Config-driven programme selection (trait mapping CSV, affinity multipliers)
- High-severity bug fixes (disability sampling, assessment dates, SES/species modifiers)

## Priority queue

### 1. Remaining bugs (quick wins)
- `np.random.seed()` reset mid-pipeline (high severity — affects reproducibility)
- `modules_passed` counts rows not distinct modules (progression_system)
- `.values` strips index alignment (progression_system)
- Metadata says 5 cohorts but code generates 7

### 2. Semester structure (medium effort)
- Add semester 1/2 to modules in curriculum config
- Two assessment dates per academic year (Jan + May)
- Engagement system generates both semesters
- Fixes the "semester hardcoded to 1" and "semester missing academic_year" bugs

### 3. Validation script (important for confidence)
- Metaanalysis script checking progression rates, withdrawal rates, grade distributions, awarding gaps
- Needed before further tuning

### 4. Awarding gap refinement (after validation)
- Gender gap (via engagement patterns, not direct modifiers)
- Disability modifier tuning (decide Stonegrove's support story)
- Engagement system as gap amplifier (wider band, realistic variation)

### 5. Cleanup
- Delete `program_affinity_system.py` (replaced)
- Delete or integrate `module_characteristics_system.py` (unused)
- Remove unused imports
- Drop semester summaries from pipeline output

### 6. Documentation
- Update SCHEMA.md, CALCULATIONS.md for current longitudinal schema
- Update DATA_IO_PLAN.md for 7-year, 5-cohort flow
- Update README.md with links

## Blocked

- (none)
