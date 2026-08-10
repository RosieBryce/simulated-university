# Stonegrove University - Calculation Reference

**Last Updated**: 25 May 2026
**Version**: 2.5 (attendance retuned; assessment_weight added; fact_good_honours split)

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
    0.20 +
    conscientiousness * 0.4 +
    academic_drive * 0.3 +
    resilience * 0.2 +
    practical_skills_motivation * 0.1
```
The `0.20` intercept anchors the average student (all traits 0.5) at ~0.70. Without it, the trait-weighted sum alone produces ~0.50 for an average student. The plausible range runs from ~0.30 (low-trait, high-disability) to ~0.95 (clipped ceiling). The lower intercept (previously 0.35) was reduced to create more headroom for the temporal arc and disability/SES modifiers to produce visible variation at aggregate level.

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
- **Weeks 6–8 (midterm)**: attendance -0.10, stress +0.12
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
- `requires_personal_care`: x0.85
- `blind_or_visually_impaired`: x0.87
- `specific_learning_disability`: x0.88
- `communication_difficulties`: x0.88
- `mental_health_disability`: x0.90
- `dyslexia`: x0.90
- `adhd`: x0.91
- `deaf_or_hearing_impaired`: x0.91
- `physical_disability`: x0.93
- `other_neurodivergence`: x0.94
- `autistic_spectrum`: x0.96
- `wheelchair_user`: x0.97
- Multiple disabilities compound multiplicatively.
- Disability also affects marks indirectly via the engagement path (lower attendance/academic engagement → lower engagement modifier). Both paths are intentional and cumulative.

**Education Modifier** (from `config/assessment_modifiers.yaml`):
- Academic: x1.10
- Vocational: x0.93
- No qualifications: x0.85
- Spread widened from earlier values (was 1.06/0.96/0.92) to achieve Elf–Dwarf good degree rate gap of ~19pp. Combined with disability path and SES gradient, the gap emerges from the composition of individual factors without any direct clan modifier. Calibrated to match the UK ethnicity awarding gap (~18–20pp, OfS data).

**Socio-Economic Modifier** (ranks 1–8, from `config/assessment_modifiers.yaml`):
```
{1: 0.91, 2: 0.93, 3: 0.95, 4: 0.97, 5: 1.03, 6: 1.05, 7: 1.07, 8: 1.09}
```

**First-Generation Modifier** (from `config/assessment_modifiers.yaml`, keyed by programme year):
```
{1: 0.96, 2: 0.99, 3: 1.00}    # ≈ −2.4 / −0.6 / 0 marks on a base-60 student
```
Applied only when `first_gen` is True. The effect fades across the three years, reflecting
first-in-family students underperforming relative to their prior attainment in the transition
year and closing that gap as they acclimatise. A programme year with no entry, or absent
config, yields 1.0 (no effect).

Note the Y1 penalty is the largest but does **not** affect degree classification, since Y1
carries zero weight in the degree average — it acts through progression, Y1 pass/fail and the
enrolment survey instead. Only the Y2 modifier moves the awarding gap (measured +0.24pp).

Note this compounds with the SES gradient rather than being independent of it: `first_gen` is
itself sampled from SES rank, so low-SES students are affected by both. That double-counting is
intentional — see **Awarding Gap Design** below.

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

### Component Weighting

```
combined_mark = 0.4 × MIDTERM + 0.6 × FINAL
```

This weighting is reflected in `fact_assessment` via the `assessment_weight` column (`MIDTERM = 0.4`, `FINAL = 0.6`). The combined mark is used internally by the progression system and degree classification algorithm but is not pre-computed in the relational output — analysts calculate it themselves from the component marks and weights.

### Grade Assignment

```
if mark >= 70: grade = "First"
elif mark >= 60: grade = "2:1"
elif mark >= 50: grade = "2:2"
elif mark >= 40: grade = "Third"
else: grade = "Fail"
```
Grades are not included in `fact_assessment`. Final degree classifications appear in `fact_good_honours`, derived from the Y2/Y3 weighted average (see Graduate Outcomes below).

---

## Progression

### Pass/Fail Determination

**Per Module**: `assessment_mark >= 40` (configurable via `pass_threshold` in YAML).

**Year Outcome**: Pass if all modules pass; fail otherwise.

### Progression Decision

Uses log-odds model with trait-based modifiers (from `config/year_progression_rules.yaml`).

**If Year Passed**: Roll between `enrolled` (progressed) and `withdrawn`.
- Base progression probability ~0.90
- Modified by conscientiousness, academic_drive, average mark, significant disability, first_gen

**If Year Failed**: Roll between `repeating` and `withdrawn`.
- Base repeat probability ~0.60
- Modified by conscientiousness, academic_drive
- Withdrawal side additionally modified by first_gen, year-in-programme, and prior repeat history

**Year 3 Pass**: Automatically `graduated` (no roll).

**Modifiers** applied via log-odds transformation:
```
log_odds = log(p / (1-p))
log_odds += modifier_weight * (trait_value - 0.5) * scale
adjusted_p = 1 / (1 + exp(-log_odds))
```
`scale` is read from `config/year_progression_rules.yaml` → `trait_modifier_scale` (currently **4**).
Maps trait range [0, 1] to ±(0.5 × scale) in log-odds space. Scale=10 was too aggressive (swamped base rates, giving ~2.6% withdrawal); scale=4 gives ~7% withdrawal, within UK HE target 5–8%.

Flag-based modifiers are flat additions to log-odds rather than trait-scaled:
```
first_gen_progression: -0.20     # first-in-family → lower continuation
first_gen_withdrawal:  +0.15
```
Net effect ≈ +1.4pp withdrawal among passing first-generation students, in the direction of the
~3–5pp lower continuation seen in UK data.

---

## VLE Engagement Metrics

Four columns added to `fact_weekly_engagement` per student × module × week. Config in `config/engagement_modifiers.yaml` under `vle_modifiers`.

### vle_logins

Trimodal mixture model. Each student is assigned a usage type **once per semester** (persistent), reflecting genuine variation in how students engage with the LMS rather than just engagement level:

| Type | ~% of students | Poisson λ | Typical weekly range |
|------|---------------|-----------|----------------------|
| Low (non-users / home workers) | 50% | 0.8 | 0–2 |
| Mid (regular users) | 43% | 7.0 | 5–10 |
| Power users | 7% | 45.0 | 40+ |

Academic engagement **weakly** tilts the type probabilities (max ±8pp shift) — intentionally not the primary driver, so `vle_logins` retains independent information for any future combined engagement metric.

### vle_resource_views

```
base_views  = vle_logins × views_per_login_base (2.5)
diff_mult   = 1 + (difficulty − 0.5) × difficulty_multiplier (0.5)
time_mult   = 2.0 (weeks 10–12) | 1.4 (weeks 6–8) | 1.0 (otherwise)
eng_mod     = engagement_floor (0.65) + (1 − floor) × academic_engagement
resource_views = round(base_views × diff_mult × time_mult × eng_mod)
```

The `engagement_floor > 0` is deliberate: disengaged students who skip lectures still access recordings and slides online, so resource views don't collapse to zero at low engagement. This is the compensatory online-access effect.

### vle_forum_posts

```
λ_forum = base_lambda (0.2) + social_engagement × 1.2 + extraversion × 0.6
vle_forum_posts ~ Poisson(λ_forum)
```

Average student (both traits 0.5): λ ≈ 1.1, producing mostly 0–2 posts/week. Highly social students reach λ ≈ 1.6–2.0.

### vle_mean_login_hour

Float 0–23 (mod 24 wrap-around — 4am appears as 4.0, not 28.0).

**Per-student base hour** (persistent):
```
base_hour = 14.0 + (0.5 − extraversion) × extraversion_shift (1.5)
```
High extraversion → slightly earlier (daytime social patterns); introversion → slightly later.

**Per-student hour std** (persistent):
```
hour_std = base_std (1.5) + (1 − ses_rank/8) × ses_std_scale (1.2)
         + adhd_std_extra (2.5) if ADHD
         + mental_health_std_extra (1.5) if mental_health_disability
```

**Per-week value**:
```
stress_shift = stress_level × (1 − conscientiousness) × stress_shift_max (10.0)
mean_hour = (base_hour + stress_shift + Normal(0, hour_std)) % 24
```

Typical student (stress 0.5, conscientiousness 0.5): stress_shift ≈ 2.5 hrs → mean ~16:30.  
High-stress, low-conscientiousness, ADHD student: shift up to 8 hrs + std ≈ 4 hrs → mean ~22:00 with tail to 04:00+.

---

## Graduate Outcomes

### Degree Classification (Award Algorithm)

Degree class is calculated from module marks across Years 2 and 3 using a weighted average. Year 1 marks are excluded from classification (common UK practice). The weighting is configured in `config/graduate_outcomes.yaml` under `degree_year_weights`:

```
degree_year_weights:
  1: 0.0    # excluded
  2: 0.333  # one-third weight
  3: 0.667  # two-thirds weight
```

**Formula:**
```
weighted_mark = (mean(Y2_module_marks) × 0.333 + mean(Y3_module_marks) × 0.667)
              / (0.333 + 0.667)
             = mean(Y2_marks) × 0.333 + mean(Y3_marks) × 0.667
```

The denominator simplifies to 1.0 because the active weights sum to 1.

**Boundary adjustments** (`boundary_boost` in config): Students within a configured number of marks below a boundary receive a small upward nudge, reflecting real classification board discretion.

**Classification thresholds** (standard UK):
```
≥ 70 → First
≥ 60 → 2:1
≥ 50 → 2:2
≥ 40 → Third
< 40  → Unclassified (pass degree)
```

**Edge case — Y1-only data**: If a student has no Y2 or Y3 marks (edge case only, unreachable in practice for graduates), the system falls back to the unweighted mean of all available marks. This path exists in the code but is never exercised during normal runs because students must pass Y3 to graduate.

**Implementation:** `core_systems/graduate_outcomes_system.py` lines ~81–121. The `module_year` column in the assessment data maps directly to programme year (1/2/3), not a separate year numbering.

---

## Awarding Gap Design

The species awarding gap (~19pp good degree rate, Elf > Dwarf) emerges from **individual-level factors only**. This is consistent with the UK ethnicity awarding gap (~18–20pp white vs Black students as measured by OfS), making it realistic rather than artificially narrowed:

1. **Clan-specific SES distributions** — disadvantaged clans concentrated at low SES ranks
2. **Clan-specific education distributions** — disadvantaged clans have fewer academic backgrounds
3. **Weighted clan recruitment** — more students from lower-SES Dwarf clans, higher-SES Elf clans
4. **Clan-specific disability prevalence** — per-clan rates in `health_tendencies` section of `clan_personality_specifications.yaml`
5. **Steeper individual modifiers** — SES (0.80-1.20), education (0.85-1.10) create meaningful spread
6. **First-generation status** — SES-sampled, so concentrated in disadvantaged clans (40.7% of Dwarves vs 24.4% of Elves); carries both a mark penalty and a continuation penalty

Channels 5 and 6 deliberately overlap: `first_gen` is drawn from SES rank, so low-SES students take
both modifiers. This is a modelling choice, not an oversight — in real data, first-in-family status
carries explanatory power over and above SES alone, and the compounding is what produces a gap in
the target range without any direct species term.

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
- Species gap (good degree rate, First + 2:1): ~19pp (Elf > Dwarf) — calibrated to UK ethnicity awarding gap
- Mean module mark gap: ~5pp (Elf > Dwarf)

### Attendance
- Mean attendance rate: ~68–75% (population mean; higher for Elves, lower for Dwarves and low-SES students)
- Disadvantaged students (low SES + high disability): ~50–60%
- Mid-semester dip (weeks 6–8): ~8–10pp below weeks 1–2 peak

### Progression
- Year 1 -> Year 2: ~80-90%
- Withdrawal rate: ~5-15% per year
- Repeat rate: ~5-10% per year

---

---

## First-Generation Student Flag

`first_gen` (boolean) is generated at student intake. It approximates whether neither parent attended higher education.

**Formula**: linear taper by SES rank, with a small boost for `no_qualifications` prior education:

```
base_prob = 0.65 − (ses_rank − 1) × (0.64 / 7)
          ≈ 0.65 at SES 1 → 0.01 at SES 8

if education == 'no_qualifications': base_prob = min(base_prob + 0.08, 0.95)
first_gen = Bernoulli(base_prob)
```

Expected prevalence: ~35–40% of the full cohort (concentrated in lower SES ranks).

**Uses in this simulation:**
- `academic_self_efficacy` in the Enrolment Survey (−0.30 penalty on 1–5 scale)
- **Assessment marks** — year-tapered multiplicative modifier (see *Performance Modifiers*)
- **Progression** — lower continuation and higher withdrawal log-odds (see *Progression Decision*)

Because `first_gen` is sampled from SES rank, it is correlated with — not independent of — the SES
mark gradient. Both apply. Measured prevalence is 34.2% overall, but 40.7% of Dwarves against
24.4% of Elves, so the flag is a live contributor to the species awarding gap.

---

## Enrolment Survey

Annual survey of all enrolled students. One row per student per academic year; ~82% response rate.

### Response Probability

```
p_response = clip(0.82 + (academic_engagement − 0.5) × 2 × 0.10, 0.10, 0.98)
```

Low-engagement students are slightly less likely to respond (±10pp max shift from base).

### Career Thinking (career_clarity, career_confidence)

Both items drawn independently from the same model:

```
score = 3.0
      + year_arc[programme_year]          # −0.50 Y1 / 0.00 Y2 / +0.50 Y3
      + career_prospects × 0.30           # from programme_characteristics.csv, normalised 0–1
      + conscientiousness × 0.25
      + motivation_career_development × 0.25
      + (ses_rank − 4.5) / 7.0 × 0.20    # higher SES → more career clarity
      + N(0, 0.35)
```

Clipped to [1, 5].

### Belonging (belonging_peers, belonging_programme)

Both items drawn independently. Disability penalties are additive:

```
score = 3.0
      + year_arc[programme_year]          # 0.00 Y1 / −0.30 Y2 / −0.10 Y3  (U-shape dip)
      + social_engagement × 0.35
      + extraversion × 0.20
      − (ses_rank − 1) / 7.0 × 0.20      # lower SES → lower belonging
      + Σ disability_penalties            # MH: −0.40, social_anxiety: −0.35, autism: −0.25
      + N(0, 0.40)
```

### Academic Self-Efficacy

```
score = 3.0
      + prior_education_score             # academic: +0.20 / vocational: +0.05 / no_quals: −0.15
      + conscientiousness × 0.30
      + resilience × 0.25
      + prior_mark_norm × 0.20           # Y2+ only; (mean_mark − 30) / 70, clipped 0–1
      + (−0.30 if first_gen else 0)
      + N(0, 0.35)
```

### Support Satisfaction

```
score = 3.0
      + prior_education_score             # academic: +0.15 / vocational: +0.05 / no_quals: −0.10
      + extraversion × 0.15
      + academic_engagement × 0.25
      − (ses_rank − 1) / 7.0 × 0.15
      + prior_mark_norm × 0.15
      + N(0, 0.45)
```

No disability modifier — satisfaction reflects perceived access to support, not the quality of the support experience.

---

**See Also**: `docs/SCHEMA.md` for column definitions, `project_tracker/DESIGN_DECISIONS.md` for design rationale.
