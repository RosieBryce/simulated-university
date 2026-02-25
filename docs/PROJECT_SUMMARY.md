# Stonegrove University — Project Summary & Pick-Up Guide

**Last updated**: 25 February 2026

---

## Where Are We?

The full longitudinal pipeline is **live and running**. All five core stages are implemented. The simulation generates 7 years of data across 5 cohorts with realistic individual-level awarding gaps.

| Stage | Status |
|-------|--------|
| Student generation (personality, disability, SES, motivation) | ✅ Done |
| Programme enrollment (clan affinities + trait fit) | ✅ Done |
| Weekly engagement (AR(1) variation, temporal arc, disability/SES mods) | ✅ Done |
| Assessment (module marks, engagement modifier, SES/education mods) | ✅ Done |
| Progression (pass/fail, log-odds model, 7.4% withdrawal) | ✅ Done |
| Longitudinal loop (5 cohorts × 7 years) | ✅ Done |

### Key metrics (single-year pipeline, ~500 students)

- Pass rate: ~87%, Repeat: ~8%, Withdraw: ~7.4%
- Elf > Dwarf awarding gap: ~6–9pp (emergent from SES/education/disability)
- Progression to Year 2: ~84%
- No direct species or clan mark modifiers — all gaps agent-level

---

## Key Files to Read First

1. **`project_tracker/CURRENT.md`** — what's live and what's next
2. **`docs/DESIGN.md`** — architecture, academic_year calendar, 5 cohorts × 7 years
3. **`docs/CALCULATIONS.md`** — all formulas and modifier values
4. **`docs/SCHEMA.md`** — CSV column definitions
5. **`CLAUDE.md`** (project root) — pipeline commands and architecture summary

---

## Regenerate Data

```bash
# Full longitudinal simulation (5 cohorts × 7 years)
python run_longitudinal_pipeline.py

# Single year (for quick iteration)
python run_pipeline.py
```

---

## Expected Output Files

| File | Produced by |
|------|-------------|
| `data/stonegrove_individual_students.csv` | student_generation_pipeline |
| `data/stonegrove_enrollment.csv` | program_enrollment_system |
| `data/stonegrove_weekly_engagement.csv` | engagement_system |
| `data/stonegrove_assessment_events.csv` | assessment_system |
| `data/stonegrove_progression_outcomes.csv` | progression_system |
| `data/metadata.json` | run_longitudinal_pipeline |

---

## Project Structure

```
simulated-university/
├── config/                          # All tunable parameters
│   ├── clan_personality_specifications.yaml  # Big Five + health_tendencies (per-clan disability)
│   ├── clan_program_affinities.yaml          # Clan–programme affinity scores
│   ├── clan_name_pools.yaml                  # Name generation pools
│   ├── clan_socioeconomic_distributions.csv  # Per-clan SES and education distributions
│   ├── disability_assessment_modifiers.csv   # Mark modifiers per disability
│   ├── engagement_modifiers.yaml             # Disability/SES engagement mods + temporal arc
│   ├── assessment_modifiers.yaml             # Education and SES mark multipliers
│   ├── module_characteristics.csv            # 353 modules: difficulty, assessment_type
│   ├── programme_characteristics.csv         # 44 programmes: stress, social, creativity
│   ├── personality_refinement_modifiers.yaml # Trait adjustments for disability/SES/age
│   ├── trait_programme_mapping.csv           # Trait → programme fit scoring
│   ├── year_progression_rules.yaml           # Progression probabilities + trait_modifier_scale
│   └── archive/                              # Deprecated configs (disability_distribution.yaml, etc.)
├── core_systems/                    # Pipeline stages (run in order)
│   ├── student_generation_pipeline.py
│   ├── program_enrollment_system.py
│   ├── engagement_system.py
│   ├── assessment_system.py
│   ├── progression_system.py
│   └── build_relational_outputs.py
├── supporting_systems/              # Used by student generation
│   ├── name_generator.py
│   ├── personality_refinement_system.py
│   └── motivation_profile_system.py
├── data/                            # Generated output (gitignored)
├── docs/                            # Documentation
├── project_tracker/                 # CURRENT, BACKLOG, DONE, DESIGN_DECISIONS
├── metaanalysis/                    # Validation and analysis scripts
├── Instructions and guides/         # Curriculum Excel + world-building
└── archive_population_model/        # Deprecated population-level approach
```

---

## Open Work (summary)

See `project_tracker/BACKLOG.md` for full detail. Key remaining items:

- **Semester structure** — assign modules to semesters, two assessment dates per year
- **Gender awarding gap** — currently flat by design; could emerge from engagement patterns
- **Disability modifier tuning** — decide Stonegrove's support story (barriers vs embedded adjustments)
- **Validate emergent gaps** — metaanalysis script to confirm species/SES/clan gaps are visible and traceable
- **Gender clan overrides** — `_determine_gender` ignores clan-specific gender distributions
- **Withdrawal-after-fail refinement** — programme year investment effect (Y1 vs Y2/Y3 repeaters)

---

**See also**: `project_tracker/DESIGN_DECISIONS.md` for rationale on key choices (awarding gap design, config-driven enrollment, disability sampling approach).
