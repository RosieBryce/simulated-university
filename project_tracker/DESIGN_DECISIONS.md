# Design Decisions

Record of significant design choices and rationale. Newest first.

---

## Awarding gap: agent-level emergence (Feb 2026)

### Problem
The simulation needs a visible awarding gap between demographic groups (species, clan, SES) that analysts can investigate. Initial implementation had no meaningful gap — all students scored similarly regardless of background.

### Design principle
**All gaps must emerge from individual-level (agent-level) factors, not top-down group modifiers.** An analyst should be able to trace any group-level pattern back to structural differences in individual students' circumstances. This mirrors real-world awarding gaps, which arise from compounding socioeconomic disadvantage, not from institutions deliberately marking groups differently.

### What we rejected
- **Direct clan mark modifiers** (`config/clan_assessment_modifiers.csv`) — created and then removed. A per-clan multiplier on marks is a top-down group effect. It would produce a gap but wouldn't be analytically interesting because the cause is the modifier itself, not discoverable structural factors.
- **Hardcoded species modifier** (`mod *= 1.1 if elf else 0.95`) — same problem, plus not config-driven.

### What we implemented
Four mechanisms that compound at the individual level:

1. **Clan-specific SES distributions** (`config/clan_socioeconomic_distributions.csv`)
   - Each clan has a different probability distribution across SES ranks 1–8
   - Disadvantaged clans (Flint, Alabaster, Palm) are concentrated at ranks 1–3
   - Elite clans (Baobab, Yew, Holly) are concentrated at ranks 6–8
   - Since Dwarf clans skew lower and Elf clans skew higher, a species gap emerges

2. **Clan-specific education distributions** (same CSV)
   - Each clan has different probabilities for academic/vocational/no_qualifications
   - Elite clans have 75–85% academic; disadvantaged clans have 25–30% academic
   - Education background affects marks via the education modifier

3. **Weighted clan recruitment** (`_CLAN_RECRUITMENT_WEIGHTS` in `student_generation_pipeline.py`)
   - Stonegrove recruits more students from lower-SES Dwarf clans and higher-SES Elf clans
   - This amplifies the structural inequality in the intake population
   - Dwarf weights: Flint 0.20, Alabaster 0.18 ... Obsidian 0.05
   - Elf weights: Holly 0.25, Yew 0.22 ... Palm 0.08

4. **Steeper individual modifiers** (`assessment_system.py`)
   - SES modifier: 0.80 (rank 1) to 1.20 (rank 8) — was 0.88–1.12
   - Education modifier: academic 1.10, vocational 0.92, no_qualifications 0.85 — was 1.05/0.98/1.0
   - Disability modifiers: config-driven from `config/disability_assessment_modifiers.csv`, all ≤1.0

### Result
~8.8pp species gap (Elf 64.0 vs Dwarf 55.2) with clear within-group variation — Obsidian Dwarves (64.7) outperform Palm Elves (57.3). Gap is traceable: Dwarves average SES rank 3.9 vs Elves 5.6; 53% Dwarves have academic education vs 72% Elves.

### Future tuning levers (not yet implemented)
- **Gender distributions** — male students could underperform females, adding another gap dimension
- **Engagement system** — engagement already modifies marks; widening the engagement band or adding more realistic weekly variation would amplify compounding effects over years
- **Disability modifiers** — current values represent a university without fully embedded reasonable adjustments. Could be tuned toward 1.0 to model better support. The real-world disability gap has largely closed, partly through curriculum-embedded adjustments.
- **Base mark distribution std dev** — tightening would make modifier effects relatively larger

---

## Programme selection: config-driven trait mapping (Feb 2026)

### Problem
Programme selection used hardcoded keyword matching (`'design' in program_name.lower()`) with tiny additive modifiers (±0.05). A separate unused file (`program_affinity_system.py`, ~270 lines) had more elaborate logic but also hardcoded programme name lists.

### What we implemented
- New `config/trait_programme_mapping.csv` — maps programme characteristics to student traits with signed weights (17 rows). End-users can edit in Excel.
- `calculate_enrollment_probability()` now uses: clan affinity (from YAML config with affinity_levels/multipliers) × (1 + trait fit score). No hardcoded programme names anywhere.
- Trait fit formula: `Σ(weight × programme_char_value × (student_trait - 0.5))` — centres on neutral, so average students get ~0 effect, extreme students get meaningful pushes.

### Result
Verified correlations: conscientiousness vs academic_difficulty r=0.32, extraversion vs social_intensity r=0.15. Programme distributions remain plausible with more within-clan variation.

---

## Disability sampling: independent prevalence (Feb 2026)

### Problem
Config had a categorical distribution (summing to 1.0) but code treated values as independent Bernoulli probabilities. `no_known_disabilities` was in the config with ~65% probability, drawn alongside other disabilities. ~26% of students had empty disability strings.

### What we implemented
- Restructured `config/disability_distribution.yaml` as independent prevalence rates per species
- Removed `no_known_disabilities` from config — it's the automatic fallback when no disabilities are drawn
- Students can now have multiple disabilities (comorbidities)
- Dwarves and Elves have different prevalence profiles (e.g., Dwarves: higher ADHD 12% vs 3%)
