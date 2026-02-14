# Stonegrove University Data Schema

**Last Updated**: February 2026  
**Version**: 2.0 (Longitudinal Individual-Level)

This document describes all CSV output files and their column definitions.

---

## Core Tables

### `stonegrove_individual_students.csv`

**Purpose**: Student characteristics and demographics. One row per student per academic year (if enrolled).

| Column | Type | Description |
|--------|------|-------------|
| `student_id` | string | Persistent unique identifier (e.g., "0101") |
| `academic_year` | string | Calendar academic year (e.g. "1046-47", "1047-48") |
| `race` | string | Race category (e.g., "Dwarf", "Elf") |
| `clan` | string | Clan name (e.g., "malachite", "baobab") |
| `gender` | string | Gender (e.g., "male", "female", "neuter") |
| `forename` | string | First name |
| `surname` | string | Last name |
| `full_name` | string | Full name |
| `age` | integer | Age at enrollment |
| `education` | string | Prior education (e.g., "academic", "vocational", "no_qualifications") |
| `socio_economic_rank` | integer | Socio-economic rank (1-8, 1 = lowest) |
| `disabilities` | string | Comma-separated disability list (CSV-formatted) |
| `base_openness` | float | Base personality trait (0.0-1.0) |
| `base_conscientiousness` | float | Base personality trait (0.0-1.0) |
| `base_extraversion` | float | Base personality trait (0.0-1.0) |
| `base_agreeableness` | float | Base personality trait (0.0-1.0) |
| `base_neuroticism` | float | Base personality trait (0.0-1.0) |
| `refined_openness` | float | Refined personality trait (0.0-1.0) |
| `refined_conscientiousness` | float | Refined personality trait (0.0-1.0) |
| `refined_extraversion` | float | Refined personality trait (0.0-1.0) |
| `refined_agreeableness` | float | Refined personality trait (0.0-1.0) |
| `refined_neuroticism` | float | Refined personality trait (0.0-1.0) |
| `motivation_academic_drive` | float | Motivation dimension (0.0-1.0) |
| `motivation_values_based_motivation` | float | Motivation dimension (0.0-1.0) |
| `motivation_career_focus` | float | Motivation dimension (0.0-1.0) |
| `motivation_cultural_experience` | float | Motivation dimension (0.0-1.0) |
| `motivation_personal_growth` | float | Motivation dimension (0.0-1.0) |
| `motivation_social_connection` | float | Motivation dimension (0.0-1.0) |
| `motivation_intellectual_curiosity` | float | Motivation dimension (0.0-1.0) |
| `motivation_practical_skills` | float | Motivation dimension (0.0-1.0) |

**Notes**:
- `student_id` is persistent across all years
- `academic_year` is **calendar** year (Middle Earth: start 1046-47). Not "student year".
- Personality traits are "refined" based on disabilities, socio-economic rank, education, age

---

### `stonegrove_enrollment.csv`

**Purpose**: Programme enrollment records. One row per student per academic year.

| Column | Type | Description |
|--------|------|-------------|
| `student_id` | string | Persistent unique identifier |
| `academic_year` | string | Calendar academic year (e.g. "1046-47", "1047-48") |
| `programme_code` | string | Programme code (e.g., "1.2.4") |
| `programme_name` | string | Programme name |
| `faculty` | string | Faculty name |
| `department` | string | Department name |
| `programme_year` | integer | Year in programme (1, 2, 3) |
| `status` | string | Status: "enrolled", "repeating", "withdrawn", "graduated" |
| **`status_change_at`** | string | **Start of year** when this status took effect (ISO date, e.g. "1046-09-01"). No in-year withdrawals; timestamp for analysts. |
| `year1_modules` | string | Year 1 modules (CSV-formatted: comma-separated, quoted where needed) |
| `year2_modules` | string | Year 2 modules (CSV-formatted) |
| `year3_modules` | string | Year 3 modules (CSV-formatted) |
| `num_year1_modules` | integer | Count of Year 1 modules |
| `num_year2_modules` | integer | Count of Year 2 modules |
| `num_year3_modules` | integer | Count of Year 3 modules |
| `clan_affinity` | float | Clan-programme affinity score (0.0-1.0) |
| `selection_probability` | float | Probability of selecting this programme (0.0-1.0) |

**Notes**:
- `programme_year` = 1, 2, or 3 (where student is in the programme)
- `academic_year` is calendar; e.g. repeating Year 1 in second year = `academic_year` "1047-48", `programme_year` 1
- `status` = "withdrawn" or "graduated" means no more records for this student

---

### `stonegrove_weekly_engagement.csv`

**Purpose**: Weekly engagement metrics. One row per student per week per module.

| Column | Type | Description |
|--------|------|-------------|
| `student_id` | string | Persistent unique identifier |
| `academic_year` | string | Calendar academic year (e.g. "1046-47") |
| `week_number` | integer | Week number (1-12 for semester) |
| `programme_code` | string | Programme code |
| `module_title` | string | Module name |
| `attendance_rate` | float | Attendance rate (0.0-1.0) |
| `participation_score` | float | Participation score (0.0-1.0) |
| `academic_engagement` | float | Academic engagement (0.0-1.0) |
| `social_engagement` | float | Social engagement (0.0-1.0) |
| `stress_level` | float | Stress level (0.0-1.0) |
| `module_difficulty` | float | Module difficulty (0.0-1.0) |
| `module_social_requirements` | float | Module social requirements (0.0-1.0) |
| `module_creativity_requirements` | float | Module creativity requirements (0.0-1.0) |
| `personality_conscientiousness` | float | Student conscientiousness (for analysis) |
| `personality_extraversion` | float | Student extraversion (for analysis) |
| `motivation_academic_drive` | float | Student academic drive (for analysis) |
| `motivation_social_connection` | float | Student social connection motivation (for analysis) |

**Notes**:
- Generated for all enrolled students each week
- Only includes modules student is enrolled in for that year

---

### `stonegrove_assessment_events.csv`

**Purpose**: Assessment marks. One row per student per module per assessment.

| Column | Type | Description |
|--------|------|-------------|
| `student_id` | string | Persistent unique identifier |
| `academic_year` | string | Calendar academic year (e.g. "1046-47") |
| `programme_code` | string | Programme code |
| **`module_code`** | string | **Module code** (for joining/later: more assessments per module) |
| **`component_code`** | string | **Assessment component code** (for future: multiple components per module) |
| `module_title` | string | Module name |
| `assessment_type` | string | Assessment type (e.g., "essay", "practical", "project", "mixed") |
| `assessment_mark` | float | Mark (0.0-100.0) |
| `grade` | string | Grade: "First", "2:1", "2:2", "Third", "Fail" |
| `assessment_date` | string | Assessment date (ISO format: YYYY-MM-DD) |
| `module_year` | integer | Year of module (1, 2, or 3) |

**Notes**:
- One assessment per module per year for now (end of module); `module_code` and `component_code` allow more later
- `grade` thresholds: First (≥70), 2:1 (≥60), 2:2 (≥50), Third (≥40), Fail (<40)
- Marks are purely assessment-based (engagement does not affect marks)

---

### Semester summaries (not a core output)

We do **not** produce `stonegrove_semester_engagement.csv` as part of the longitudinal design. Analysts can aggregate from `stonegrove_weekly_engagement.csv` (e.g. by student, academic_year, semester) if needed.

---

## Metadata

### `data/metadata.json`

**Purpose**: Version and reproducibility information.

```json
{
  "model_version": "v2.0-longitudinal",
  "git_commit": "abc123...",
  "random_seed": 42,
  "generation_timestamp": "2026-02-13T10:30:00Z",
  "config_versions": {
    "clan_traits": "v1.0",
    "progression_rules": "v1.0"
  },
  "cohort_size": 500,
  "years_generated": 7,
  "academic_years": ["1046-47", "1047-48", "1048-49", "1049-50", "1050-51", "1051-52", "1052-53"],
  "cohorts": 5
}
```

---

## Relationships

### Student Journey Example

**Year 1** (1046-47):
- `stonegrove_individual_students.csv`: `student_id`="0101", `academic_year`="1046-47"
- `stonegrove_enrollment.csv`: `student_id`="0101", `academic_year`="1046-47", `programme_year`=1, `status`="enrolled", `status_change_at`="1046-09-01"
- `stonegrove_weekly_engagement.csv`: Multiple rows (12 weeks × 2 modules = 24 rows)
- `stonegrove_assessment_events.csv`: 2 rows (one per module), with `module_code`, `component_code`

**Year 2** (1047-48, if progressed):
- `stonegrove_individual_students.csv`: `student_id`="0101", `academic_year`="1047-48"
- `stonegrove_enrollment.csv`: `student_id`="0101", `academic_year`="1047-48", `programme_year`=2, `status`="enrolled", `status_change_at`="1047-09-01"
- `stonegrove_weekly_engagement.csv`: Multiple rows for Year 2 modules
- `stonegrove_assessment_events.csv`: Year 2 module assessments

**Repeating Year 1** (1047-48):
- `stonegrove_enrollment.csv`: `student_id`="0101", `academic_year`="1047-48", `programme_year`=1, `status`="repeating", `status_change_at`="1047-09-01"
- Same modules as Year 1, new engagement/assessment records

---

## CSV Formatting Notes

### Module Lists

Module lists use CSV formatting (comma-separated, quoted where needed) to handle commas in module names:
- Example: `"Module A,\"Module B, Part 2\",Module C"`
- Parse with Python `csv` module for robustness

### Dates

- ISO format: `YYYY-MM-DD` (e.g., "1046-09-15")

### Floats

- Decimal precision: 2-3 decimal places for rates/scores, 1 decimal for marks

---

## Protected Characteristics

The following columns are included for awarding gap analysis (users compute gaps themselves):

- `race`
- `clan` (ethnicity)
- `gender`
- `disabilities`
- `socio_economic_rank`
- `education` (prior educational experience)

No special "gap" columns are provided; users analyze patterns themselves.

---

**See Also**: `docs/CALCULATIONS.md` for how these values are computed.
