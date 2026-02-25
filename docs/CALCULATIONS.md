# Stonegrove University - Calculation Reference

**Last Updated**: 25 February 2026
**Version**: 2.2 (Engagement overhaul, progression scale fix, config extraction)

This document describes all formulas, modifiers, and assumptions used in the simulation. For transparency and reproducibility.

---

## Student Generation

### Species and Clan Sampling

- 60% Dwarf, 40% Elf
- Clan selection within species uses weighted recruitment (`_CLAN_RECRUITMENT_WEIGHTS` in `student_generation_pipeline.py`)
  - Dwarf weights skew toward lower-SES clans (Flint 0.20, Alabaster 0.18, ... Obsidian 0.05)
  - Elf weights skew toward higher-SES clans (Holly 0.25, Yew 0.22, ... Palm 0.08)
- This creates structural inequality in the intake population

### Socio-Economic Rank and Education

Sampled per-clan from `config/clan_socioeconomic_distributions.csv`:
- **SES rank** (1-8): clan-specific probability distribution
- **Education** (academic/vocational/no_qualifications): clan-specific probabilities
- Disadvantaged clans (Flint, Alabaster, Palm) are concentrated at SES ranks 1-3
- Elite clans (Baobab, Yew, Holly) are concentrated at SES ranks 6-8

### Disability Sampling

From the `health_tendencies` section of `config/clan_personality_specifications.yaml` — independent Bernoulli draws per disability type:
- Each disability has a **clan-specific** prevalence rate (not species-level)
- Students can have multiple disabilities (comorbidities)
- If no disabilities drawn, assigned `no_known_disabilities`
- `config/archive/disability_distribution.yaml` (per-species only) is archived — superseded

### Personality Traits

**Base Personality** (from clan specifications):
- Each clan has ranges for Big Five traits (Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism)
- Base value = uniform random within clan range

**Refined Personality** (adjusted by characteristics):
```
refined_trait = base_trait + modifiers
```

**Modifiers** (see `supporting_systems/personality_refinement_system.py`):
- **Disabilities**: e.g., autistic_spectrum: +0.1 conscientiousness, -0.1 extraversion
- **Socio-economic rank**: Lower rank -> slight decrease in conscientiousness
- **Education**: Academic background -> slight increase in conscientiousness
- **Age**: Older students -> slight increase in conscientiousness

All refined traits clamped to [0.0, 1.0].

### Motivation Dimensions

8 dimensions, each 0.0-1.0:
- Academic drive, values-based motivation, career focus, cultural experience
- Personal growth, social connection, intellectual curiosity, practical skills

**Nudging**: Personality traits influence motivation (e.g., high conscientiousness -> higher academic drive).

---

## Enrollment

### Programme Selection

**Clan Affinity** (from `config/clan_program_affinities.yaml`):
- Each clan has affinity scores (0.0-1.0) for each programme
- Affinity classified into levels using `affinity_levels` config
- Score = `0.05 + base_selection_probability * affinity_multiplier * raw_affinity`
- The `0.05` floor ensures every programme above the affinity threshold has a baseline probability, preventing extreme concentration in top-affinity programmes
- Programmes below `minimum_affinity_threshold` get probability 0

**Trait-Programme Fit** (from `config/trait_programme_mapping.csv`):
```
fit_score = sum(weight * programme_char_value * (student_trait - 0.5))
```
- Each row maps a programme characteristic to a student trait with a signed weight
- Positive weight = high trait attracts to high characteristic
- Negative weight = high trait repels (e.g., neuroticism vs stress_level)

**Combined Probability**:
```
probability = clan_score * (1.0 + fit_score)
probability = max(probability, 0.001)
```

**Selection**: Weighted random choice, normalised across all programmes.

---

## Engagement

### Base Engagement

**Attendance**:
```
base_attendance =
    conscientiousness * 0.4 +
    academic_drive * 0.3 +
    resilience * 0.2 +
    practical_skills_motivation * 0.1
```

**Participation**:
```
base_participation =
    extraversion * 0.4 +
    social_connection_motivation * 0.3 +
    leadership_tendency * 0.2 -
    social_anxiety * 0.1
```

**Academic Engagement**:
```
base_academic_engagement =
    academic_curiosity * 0.4 +
    intellectual_curiosity_motivation * 0.3 +
    openness * 0.2 +
    academic_drive * 0.1
```

**Social Engagement**:
```
base_social_engagement =
    extraversion * 0.5 +
    social_connection_motivation * 0.3 +
    leadership_tendency * 0.2
```

**Stress**:
```
base_stress =
    neuroticism * 0.4 +
    social_anxiety * 0.3 +
    (1 - resilience) * 0.2 +
    (1 - personal_growth_motivation) * 0.1
```

All values clamped to [0.1, 0.95].

### Module Modifiers

**Difficulty Impact**:
```
difficulty_modifier = (difficulty - 0.5) * 0.2  # +/-10% effect
if conscientiousness > 0.6:
    attendance += difficulty_modifier * 0.5
    academic_engagement += difficulty_modifier
else:
    attendance -= difficulty_modifier * 0.3
    academic_engagement -= difficulty_modifier * 0.5
```

**Social Requirements Impact**:
```
social_modifier = (extraversion - 0.5) * social_requirements * 0.4
participation += social_modifier
```

**Creativity Requirements Impact**:
```
creativity_modifier = (openness - 0.5) * creativity_requirements * 0.3
academic_engagement += creativity_modifier
```

### Disability and SES Modifiers (base adjustments)

From `config/engagement_modifiers.yaml`:
- **Disability modifiers**: per-disability adjustments to base attendance, academic_engagement, stress, and `std_extra` (additional weekly noise). E.g. `mental_health_disability`: attendance -0.08, academic_engagement -0.06, stress +0.12, std_extra +0.06.
- **SES rank modifiers**: lower SES → lower attendance, higher stress. E.g. rank 1: attendance -0.10, stress +0.12. Applied once to base values before weekly generation.

### Temporal Arc

Also from `config/engagement_modifiers.yaml`. Applied per-week as additive shifts to base values:
- **Weeks 1–2 (early)**: attendance +0.04, academic_engagement +0.03, stress -0.04 (fresher enthusiasm)
- **Weeks 6–8 (midterm)**: attendance -0.03, stress +0.12
- **Weeks 10–12 (exam)**:
  - All students: stress +0.18
  - High conscientiousness (≥ 0.6): attendance +0.03, academic_engagement +0.05
  - Low conscientiousness (< 0.6): attendance -0.06

### Weekly Variation (AR(1) autocorrelated)

A shared weekly deviation is generated for each student using a first-order autoregressive process:
```
# alpha = 0.4 (week-to-week persistence)
scale = sqrt(1 - alpha²) * noise_std
devs[i] = alpha * devs[i-1] + normal(0, scale)
```
- `noise_std` = 0.12 (fixed, not proportional to base value)
- `std_extra` from disability config adds extra noise for affected students
- The same deviation applies to all modules in a given week (a bad week is bad everywhere)
- Stress deviation is **inverted**: a positive week deviation reduces stress

```
metric_value = base_value + week_deviation + temporal_mod + small_module_noise(std=0.05)
stress_value = base_stress - week_deviation + temporal_stress_mod
metric_value = clamp(metric_value, 0.0, 1.0)
```

---

## Assessment

### Base Mark Generation

**Distribution Selection** (weighted):
- 70% -> normal(mean=60, std=8)
- 15% -> normal(mean=75, std=6)  (high performers)
- 15% -> normal(mean=45, std=10) (struggling)

### Performance Modifiers

All modifiers are multiplicative and applied at the individual student level.

**Clan Modifier**: Always 1.0 (no direct clan effect — gaps emerge from underlying factors).

**Disability Modifiers** (from `config/disability_assessment_modifiers.csv`):
- `requires_personal_care`: x0.88
- `blind_or_visually_impaired`: x0.90
- `communication_difficulties`: x0.90
- `specific_learning_disability`: x0.92
- `mental_health_disability`: x0.93
- `dyslexia`: x0.93
- `adhd`: x0.94
- `deaf_or_hearing_impaired`: x0.94
- `physical_disability`: x0.96
- `other_neurodivergence`: x0.96
- `autistic_spectrum`: x0.97
- `wheelchair_user`: x0.98
- Multiple disabilities compound multiplicatively.

**Education Modifier** (from `config/assessment_modifiers.yaml`):
- Academic: x1.06
- Vocational: x0.96
- No qualifications: x0.92
- Softened from earlier values (was 1.10/0.92/0.85) — gap was ~23pp, target ~12–15pp

**Socio-Economic Modifier** (ranks 1–8, from `config/assessment_modifiers.yaml`):
```
{1: 0.91, 2: 0.93, 3: 0.95, 4: 0.97, 5: 1.03, 6: 1.05, 7: 1.07, 8: 1.09}
```

**Module Difficulty Modifier**:
- From `config/module_characteristics.csv` difficulty_level, or inferred from title
- Converted via `_difficulty_to_mark_modifier()`: difficulty 0.5 -> 1.0, 0.9 -> 0.9

### Engagement Modifier

Per student per module, from weekly engagement data:
```
avg_engagement = mean(attendance_rate, participation_score, academic_engagement)
engagement_modifier = clamp(0.88 + 0.24 * avg_engagement, 0.88, 1.12)
```
- Low engagement (0.0) -> 0.88
- Neutral (0.5) -> 1.0
- High engagement (1.0) -> 1.12

### Final Mark Calculation

```
final_mark = base_mark * disability_modifier * education_modifier *
              socio_economic_modifier * module_modifier * engagement_modifier

final_mark += random_normal(0, 5)  # individual variation
final_mark = clamp(round(final_mark, 1), 0, 100)
```

### Grade Assignment

```
if mark >= 70: grade = "First"
elif mark >= 60: grade = "2:1"
elif mark >= 50: grade = "2:2"
elif mark >= 40: grade = "Third"
else: grade = "Fail"
```

---

## Progression

### Pass/Fail Determination

**Per Module**: `assessment_mark >= 40` (configurable via `pass_threshold` in YAML).

**Year Outcome**: Pass if all modules pass; fail otherwise.

### Progression Decision

Uses log-odds model with trait-based modifiers (from `config/year_progression_rules.yaml`).

**If Year Passed**: Roll between `enrolled` (progressed) and `withdrawn`.
- Base progression probability ~0.90
- Modified by conscientiousness, academic_drive, average mark, significant disability

**If Year Failed**: Roll between `repeating` and `withdrawn`.
- Base repeat probability ~0.60
- Modified by conscientiousness, academic_drive

**Year 3 Pass**: Automatically `graduated` (no roll).

**Modifiers** applied via log-odds transformation:
```
log_odds = log(p / (1-p))
log_odds += modifier_weight * (trait_value - 0.5) * scale
adjusted_p = 1 / (1 + exp(-log_odds))
```
`scale` is read from `config/year_progression_rules.yaml` → `trait_modifier_scale` (currently **4**).
Maps trait range [0, 1] to ±(0.5 × scale) in log-odds space. Scale=10 was too aggressive (swamped base rates, giving ~2.6% withdrawal); scale=4 gives ~7% withdrawal, within UK HE target 5–8%.

---

## Awarding Gap Design

The species awarding gap (~8-12pp, Elf > Dwarf) emerges from **individual-level factors only**:

1. **Clan-specific SES distributions** — disadvantaged clans concentrated at low SES ranks
2. **Clan-specific education distributions** — disadvantaged clans have fewer academic backgrounds
3. **Weighted clan recruitment** — more students from lower-SES Dwarf clans, higher-SES Elf clans
4. **Clan-specific disability prevalence** — per-clan rates in `health_tendencies` section of `clan_personality_specifications.yaml`
5. **Steeper individual modifiers** — SES (0.80-1.20), education (0.85-1.10) create meaningful spread

No top-down species or clan mark modifiers. All group-level patterns are traceable to individual characteristics. See `project_tracker/DESIGN_DECISIONS.md`.

---

## Random Seeds

- Pipeline uses `np.random.default_rng(seed)` in assessment and progression systems
- Each academic year gets seed = `BASE_SEED + year_index * 1000`
- Student generation uses global seed per cohort

---

## Validation Targets

### Assessment
- Mark distribution: centred around 55-65
- Pass rate: ~80-90% per module
- Species gap: ~8-12pp (Elf > Dwarf)

### Progression
- Year 1 -> Year 2: ~80-90%
- Withdrawal rate: ~5-15% per year
- Repeat rate: ~5-10% per year

---

**See Also**: `docs/SCHEMA.md` for column definitions, `project_tracker/DESIGN_DECISIONS.md` for design rationale.
