# Stonegrove University - Calculation Reference

**Last Updated**: February 2026  
**Version**: 2.0 (Longitudinal Individual-Level)

This document describes all formulas, modifiers, and assumptions used in the simulation. For transparency and reproducibility.

---

## Student Generation

### Personality Traits

**Base Personality** (from clan specifications):
- Each clan has ranges for Big Five traits (Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism)
- Base value = random within clan range

**Refined Personality** (adjusted by characteristics):
```
refined_trait = base_trait + modifiers
```

**Modifiers**:
- **Disabilities**: 
  - `autistic_spectrum`: +0.1 to conscientiousness, -0.1 to extraversion
  - `adhd`: -0.1 to conscientiousness, +0.1 to extraversion
  - `specific_learning_disability`: -0.1 to conscientiousness
  - (See `config/clan_personality_specifications.yaml` for full list)
- **Socio-economic rank**: Lower rank → slight decrease in conscientiousness
- **Education**: Academic background → slight increase in conscientiousness
- **Age**: Older students → slight increase in conscientiousness

**Clamp**: All refined traits clamped to [0.0, 1.0]

### Motivation Dimensions

8 dimensions, each 0.0-1.0:
- Academic drive
- Values-based motivation
- Career focus
- Cultural experience
- Personal growth
- Social connection
- Intellectual curiosity
- Practical skills

**Nudging**: Personality traits influence motivation (e.g., high conscientiousness → higher academic drive)

---

## Enrollment

### Programme Selection

**Base Affinity** (from `config/clan_programme_affinities.yaml`):
- Each clan has affinity scores (0.0-1.0) for each programme
- Default: 0.05 if not specified

**Personality Modifiers**:
```
personality_modifier = 0.0
if programme has "social" or "community":
    personality_modifier += (extraversion - 0.5) * 0.1
if programme has "governance" or "strategic":
    personality_modifier += (conscientiousness - 0.5) * 0.1
if programme has "design" or "innovation":
    personality_modifier += (openness - 0.5) * 0.1
```

**Motivation Modifiers**:
```
motivation_modifier = (academic_drive - 0.5) * 0.05
if programme has "craft" or "practice":
    motivation_modifier += (career_focus - 0.5) * 0.1
if programme has "community" or "mutual":
    motivation_modifier += (values_based - 0.5) * 0.1
```

**Final Probability**:
```
probability = base_affinity + personality_modifier + motivation_modifier
probability = clamp(probability, 0.01, 0.99)
```

**Selection**: Weighted random choice based on probabilities

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

All values clamped to [0.1, 0.95]

### Module Modifiers

**Difficulty Impact**:
```
difficulty_modifier = (difficulty - 0.5) * 0.2  # ±10% effect

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

### Weekly Variation

```
weekly_value = base_value + random_normal(0, 0.05)
weekly_value = clamp(weekly_value, 0.1, 0.95)
```

### Module Difficulty Estimation

**Feminist-Aware Algorithm** (no penalty for intro/foundation):

```
difficulty = 0.5  # Default: moderate

if "advanced" or "capstone" or "research" in title:
    difficulty += 0.2
elif "epistemolog" or "theoretical" or "complex" in title:
    difficulty += 0.15
elif "embodied" or "somatic" or "fermentation" or "cultivation" or 
     "care" or "healing" or "hospitality" or "ritual" or "ethics" or "indigenous" in title:
    difficulty += 0.05  # Slight elevation: often demanding

difficulty = clamp(difficulty, 0.25, 0.9)
```

**Note**: "introduction" and "foundation" do NOT reduce difficulty.

---

## Assessment

### Base Mark Generation

**Distribution Selection** (weighted):
- 70% → base distribution (mean=60, std=8)
- 15% → high performers (mean=75, std=6)
- 15% → struggling (mean=45, std=10)

**Base Mark**:
```
base_mark = random_normal(mean, std)
```

### Performance Modifiers

**Race Modifier**:
- Elf: ×1.1
- Dwarf: ×0.95

**Clan Modifier** (from `config/clan_programme_affinities.yaml`):
- Baobab: ×1.15
- Alabaster: ×0.85
- Default: ×1.0

**Disability Modifiers**:
- `specific_learning_disability`: ×0.8
- `requires_personal_care`: ×0.75
- `blind_or_visually_impaired`: ×0.8
- `communication_difficulties`: ×0.8
- `physical_disability`: ×1.05
- `mental_health_disability`: ×1.05
- `autistic_spectrum`: ×1.1
- `adhd`: ×1.05
- `dyslexia`: ×1.05
- `other_neurodivergence`: ×1.1
- `deaf_or_hearing_impaired`: ×1.05
- `wheelchair_user`: ×1.05
- `no_known_disabilities`: ×1.0

**Education Modifier**:
- Academic: ×1.05
- Vocational: ×0.98

**Socio-Economic Modifier**:
- Rank 1: ×0.9
- Rank 2: ×0.95
- Rank 3: ×1.0 (baseline)
- Rank 4: ×1.05
- Rank 5: ×1.1

**Module Difficulty Modifier**:
- Based on module title keywords (see Module Difficulty Estimation above)
- Applied as multiplier: `module_modifier` (typically 0.85-1.05)

### Final Mark Calculation

```
final_mark = base_mark * race_modifier * clan_modifier * 
              disability_modifier * education_modifier * 
              socio_economic_modifier * module_modifier

# Add individual module performance variation
final_mark += random_normal(0, 5)  # ±5 points

final_mark = clamp(final_mark, 0, 100)
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

## Progression (Planned)

### Pass/Fail Determination

**Per Module**:
```
if assessment_mark >= 40:
    module_passed = True
else:
    module_passed = False
```

**Year Outcome**:
```
if all modules passed:
    year_passed = True
else:
    year_passed = False
```

### Progression Probability

**If Year Passed**:
```
base_progression_probability = 0.85  # 85% progress by default

# Modifiers
if conscientiousness > 0.7:
    progression_probability += 0.1
if academic_drive > 0.7:
    progression_probability += 0.05
if average_mark > 65:
    progression_probability += 0.05

progression_probability = clamp(progression_probability, 0.5, 0.98)

# Withdrawal probability (inverse)
withdrawal_probability = 1 - progression_probability
withdrawal_probability += random_factor  # ±5%
```

**If Year Failed**:
```
base_repeat_probability = 0.6  # 60% repeat by default

# Modifiers
if conscientiousness > 0.6:
    repeat_probability += 0.15
if average_mark > 35:  # Close to passing
    repeat_probability += 0.1

repeat_probability = clamp(repeat_probability, 0.3, 0.9)

# Withdrawal probability (inverse)
withdrawal_probability = 1 - repeat_probability
```

**Decision**:
```
if random() < progression_probability:
    status = "enrolled"  # Progress to next year
elif random() < withdrawal_probability:
    status = "withdrawn"
else:
    status = "repeating"  # Repeat current year
```

---

## Assumptions & Design Choices

### Engagement Does NOT Affect Marks

- **Rationale**: Realistic separation between engagement and assessment
- **Impact**: High engagement ≠ high marks (though both correlate with conscientiousness)

### Module Difficulty: Feminist-Aware

- **Rationale**: Domestic/applied/craft/care work should not be treated as "easy"
- **Impact**: Introduction modules not automatically easy; embodied/domestic modules slightly elevated

### Progression: Student-Level, Not Top-Down

- **Rationale**: Emergent behavior more realistic than fixed percentages
- **Impact**: Overall progression rates emerge from individual decisions

### Protected Characteristics: Included, Not Analyzed

- **Rationale**: Users should compute awarding gaps themselves
- **Impact**: Race, disability, etc. columns present; no "gap" columns provided

---

## Random Seeds

- **Student Generation**: Seed = 42 (or configurable)
- **Enrollment**: Same seed (for reproducibility)
- **Engagement**: Same seed
- **Assessment**: Same seed
- **Progression**: Same seed

**Note**: All systems use same seed for full reproducibility.

---

## Validation Targets

### Engagement
- Average attendance: ~65-75%
- Average participation: ~50-60%
- Strong correlation: Conscientiousness ↔ Attendance (r > 0.8)

### Assessment
- Mark distribution: Skewed toward 56-64 range
- Pass rate: ~80-90% per module
- Grade distribution: Few Firsts, many 2:1s and 2:2s

### Progression
- Year 1 → Year 2: ~80-90%
- Withdrawal rate: ~5-15% per year
- Repeat rate: ~5-10% per year

---

**See Also**: `docs/SCHEMA.md` for column definitions, `docs/DESIGN.md` for overall architecture.
