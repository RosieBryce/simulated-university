# Current focus

**Last updated**: 25 Feb 2026

## Recently completed (this session)

- **Semester structure wired** — `config/module_characteristics.csv` now has `semester` column (1=Autumn, 2=Spring). First ceil(n/2) modules per (programme_code, year) group go to S1. 221 S1, 132 S2 modules.
- **Two assessment components per module** — `assessment_system.py` now generates MIDTERM + FINAL rows per student per module. MIDTERM uses weeks 1–8 engagement; FINAL uses all 12 weeks. `combined_mark = 0.4 × MIDTERM + 0.6 × FINAL` stored on FINAL rows.
- **Assessment dates per semester** — `_assessment_dates()` helper: S1 → Nov 1 (midterm), Dec 15 (final); S2 → Mar 15 (midterm), May 15 (final). 4 distinct dates per academic year.
- **Progression updated** — filters to FINAL rows, uses `combined_mark` (fallback to `assessment_mark` for legacy data). Withdrawal rate 5.9% (within 5–8% target).
- **Weekly engagement has `semester` column** — sourced from `_module_chars[m]['semester']` per weekly record.
- **`SemesterEngagement` dataclass renamed** — `semester` field → `programme_year`; new `semester: int` field added; arc alignment comment added.
- **`metaanalysis/student_paths.py` created** — per-student trajectories, path archetype distributions, species/SES breakdowns, case studies, coherence checks. All coherence checks pass.
- **SCHEMA.md updated** — v2.1: semester column, component_code MIDTERM/FINAL, combined_mark, progression note.

## Previously completed
- Disability sampling wired per-clan
- Enrollment concentration fixed
- Engagement system overhauled (AR(1), temporal arc, disability/SES modifiers)
- Engagement system bug fixes
- Assessment modifiers extracted to config; education gap softened
- Progression scale fixed (withdrawal rate: 2.6% → 7.4%)

## Previously completed

- Validation script built and all 4 WARNs resolved
- Emergent awarding gap (~6–9pp Elf > Dwarf) from agent-level factors
- All high-severity bugs fixed (disability sampling, dates, SES, species modifier, seed reset, modules_passed)
- Pipeline crash fixes; engagement append bug fixed
- Relational schema: 4 dims + 4 facts in data/relational/
- Module codes from curriculum Excel; assessment year-level bug fixed
- Config fully populated (353 modules, 44 programmes); config folder cleaned

---

## Priority queue

### ~~1. Validate emergent gaps~~ — done
### ~~2. Semester structure~~ — done
### ~~3. Gender awarding gap~~ — design decision: flat by design, no modifier, not implementing
### ~~4. Disability modifier tuning~~ — decision: leave for analysts/users to explore
- Gap as-is: 6.3pp overall (no disability 61.7 vs has disability 55.4)
- Consistent ~5pp across all SES bands (not a SES confound)
- Comorbidities compound: 1 disability → 5pp, 2 → 10pp, 3 → 15pp
- Modifiers range 0.88 (requires_personal_care) to 0.98 (wheelchair_user)
- Users can test "embedded reasonable adjustments" by nudging modifiers toward 1.0

### 5. Next up
- **Module trailing** — single failing module trails into next year as RESIT (see backlog)
- **Withdrawal-after-fail refinement** — Y1 vs Y2/Y3 investment effect; prior repeat history
- **Gender clan overrides** — `_determine_gender` ignores clan-specific gender distributions; hardcoded 45/45/10
- **Add caring_responsibilities to student model** — needs student generation first
- Sample data on git
- Status rolls, interventions, case study extraction

## Blocked

(none)

## Design decisions (standing)

- **No direct clan mark modifier** — `config/archive/clan_assessment_modifiers.csv` archived; gaps must emerge from SES/education/disability. Do not re-wire.
- **No caring_responsibilities in progression** — field not generated; removed from modifier code. Add to student generation first if this becomes a priority.
- **Gender gap flat** — intentional; do not add direct gender modifier.
