# Current focus

**Last updated**: 25 Feb 2026

## Recently completed (this session)

- **Disability sampling wired per-clan** — `health_tendencies` section of `clan_personality_specifications.yaml` now drives disability prevalence. `disability_distribution.yaml` (per-species only) archived.
- **Enrollment concentration fixed** — uniform floor added (`0.05 + base * multiplier * affinity`); affinity multipliers flattened (3.0/2.0/1.5/0.5 → 2.0/1.5/1.2/0.8). Top-5 programme share down from ~68% to ~42%.
- **Engagement system overhauled** — AR(1) autocorrelated week deviations (alpha=0.4, fixed std=0.12); temporal arc (early enthusiasm, midterm crunch, exam stress); disability base adjustments + std_extra; SES rank modifiers. All driven from `config/engagement_modifiers.yaml`.
- **Engagement system bug fixes** — semester now uses `prog_year` (was hardcoded 1); `academic_year` added to semester summaries.
- **Assessment modifiers extracted to config** — `config/assessment_modifiers.yaml` created. Education gap softened: 1.10/0.92/0.85 → 1.06/0.96/0.92 (observed gap: 23pp → ~14pp).
- **Progression scale fixed** — `trait_modifier_scale: 4` in YAML replaces hardcoded `× 10`. Withdrawal rate: 2.6% → 7.4% (UK HE target 5–8%). `caring_responsibilities` dead code removed.
- **All docs and trackers updated** to reflect current state.

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

### 1. Validate emergent gaps
- Run metaanalysis scripts to confirm: species gap visible? By clan? By SES? Can analyst trace to structural factors?
- `metaanalysis/validate_outputs.py` exists — check it covers awarding gap checks

### 2. Semester structure (medium effort)
- Assign each module to semester 1 or 2 (in curriculum Excel or module_characteristics.csv)
- Two assessment dates per year (Jan + May)
- Engagement system generates both semesters

### 3. Gender awarding gap
- Currently flat by design; could emerge from engagement patterns rather than a direct modifier
- Decide approach before implementing

### 4. Disability modifier tuning
- Decide Stonegrove's support story: embedded reasonable adjustments (modifiers → ~1.0) or barriers still present (current values)

### 5. Later
- **Gender clan overrides** — `_determine_gender` ignores clan-specific gender distributions in `clan_name_pools.yaml`; hardcoded 45/45/10
- **Withdrawal-after-fail refinement** — Y1 vs Y2/Y3 investment effect; prior repeat history
- **Add caring_responsibilities to student model** — field was removed as dead code; needs to be generated before it can be used in progression
- Sample data on git
- Status rolls, interventions, case study extraction

## Blocked

(none)

## Design decisions (standing)

- **No direct clan mark modifier** — `config/archive/clan_assessment_modifiers.csv` archived; gaps must emerge from SES/education/disability. Do not re-wire.
- **No caring_responsibilities in progression** — field not generated; removed from modifier code. Add to student generation first if this becomes a priority.
- **Gender gap flat** — intentional; do not add direct gender modifier.
