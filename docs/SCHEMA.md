# Stonegrove University Data Schema

**Last Updated**: 25 February 2026
**Version**: 2.2 (Semester Structure + Two Assessment Components + Graduate Outcomes + NSS)

This document describes all CSV output files and their column definitions.

---

## Core Tables

### `stonegrove_individual_students.csv`

**Purpose**: Student characteristics and demographics. One row per student per cohort (generated at intake).

| Column | Type | Description |
|--------|------|-------------|
| `student_id` | string | Persistent unique identifier (e.g., "0101") |
| `academic_year` | string | Calendar academic year (e.g. "1046-47", "1047-48") |
| `species` | string | Species category (e.g., "Dwarf", "Elf") |
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
| **`semester`** | integer | **Teaching semester the module belongs to (1 = Autumn, 2 = Spring)** |

**Notes**:
- Generated for all enrolled students each week
- Only includes modules student is enrolled in for that year
- `semester` reflects the module's assigned teaching semester from `config/module_characteristics.csv`

---

### `stonegrove_assessment_events.csv`

**Purpose**: Assessment marks. Two rows per student per module: MIDTERM and FINAL components.

| Column | Type | Description |
|--------|------|-------------|
| `student_id` | string | Persistent unique identifier |
| `academic_year` | string | Calendar academic year (e.g. "1046-47") |
| `programme_code` | string | Programme code |
| `module_code` | string | Module code (joins to `config/module_characteristics.csv`) |
| **`component_code`** | string | **`MIDTERM` or `FINAL`** (was `MAIN` before v2.1) |
| `module_title` | string | Module name |
| `assessment_type` | string | Assessment type (e.g., "essay", "practical", "project", "mixed") |
| `assessment_mark` | float | Component mark (0.0–100.0): raw MIDTERM or raw FINAL mark |
| **`combined_mark`** | float | **Weighted combined mark on FINAL rows only: 0.4 × MIDTERM + 0.6 × FINAL. Null on MIDTERM rows.** |
| `grade` | string | MIDTERM: formative grade from component mark. FINAL: grade from `combined_mark`. |
| `assessment_date` | string | Assessment date (ISO format: YYYY-MM-DD). 4 distinct dates per academic year (2 per semester). |
| `module_year` | integer | Year of module in programme (1, 2, or 3) |

**component_code values**:
| Value | Description | Engagement window | Date (Semester 1) | Date (Semester 2) |
|-------|-------------|-------------------|-------------------|-------------------|
| `MIDTERM` | Formative mid-term assessment | Weeks 1–8 avg | `{year}-11-01` | `{year+1}-03-15` |
| `FINAL` | Summative end-of-module assessment | All 12 weeks avg | `{year}-12-15` | `{year+1}-05-15` |

**Notes**:
- `combined_mark` on FINAL rows is the definitive mark for analysis and progression decisions
- MIDTERM grade is formative only; progression uses `combined_mark` from FINAL rows
- `grade` thresholds (applied to `combined_mark` for FINAL): First (≥70), 2:1 (≥60), 2:2 (≥50), Third (≥40), Fail (<40)
- Engagement windows align with the temporal arc: weeks 1–8 capture early enthusiasm + midterm crunch; all 12 weeks capture the full arc including exam stress

---

### `stonegrove_progression_outcomes.csv`

**Purpose**: Year-end progression decisions. One row per student per academic year.

| Column | Type | Description |
|--------|------|-------------|
| `student_id` | string | Persistent unique identifier |
| `academic_year` | string | Calendar academic year |
| `year_outcome` | string | "pass" or "fail" (all modules >= 40 to pass) |
| `status` | string | Next-year status: "enrolled", "repeating", "withdrawn", "graduated" |
| `status_change_at` | string | Date when new status takes effect (ISO date) |
| `programme_year_next` | integer/null | Programme year for next academic year (null if withdrawn/graduated) |
| `avg_mark` | float | Average assessment mark across all modules |
| `modules_passed` | integer | Count of distinct modules passed (mark >= 40) |
| `modules_total` | integer | Count of distinct modules taken |

**Notes**:
- `status = "graduated"` when Year 3 student passes all modules
- `modules_passed` counts distinct modules (by module_code) where `combined_mark ≥ 40` (FINAL rows only)
- Progression uses `combined_mark` from FINAL rows; falls back to `assessment_mark` for legacy data
- Progression decision uses trait-based log-odds model (see CALCULATIONS.md)

---

### `stonegrove_graduate_outcomes.csv`

**Purpose**: Post-graduation employment outcomes (~15 months after graduation). One row per graduate.

| Column | Type | Description |
|--------|------|-------------|
| `student_id` | string | Persistent unique identifier |
| `academic_year_graduated` | string | Academic year in which student graduated (e.g. "1048-49") |
| `programme_code` | string | Programme code |
| `faculty` | string | Faculty number (first digit of programme_code) |
| `degree_classification` | string | Weighted degree class: "First", "2:1", "2:2", "Third" (Y2 weight 1/3, Y3 weight 2/3) |
| `degree_weighted_avg` | float | Weighted average mark used for classification |
| `outcome_type` | string | "employed", "further_study", "unemployed", "unknown" |
| `professional_level` | string | "professional" or "non_professional" (null if not employed) |
| `employment_sector` | string | Faculty-mapped sector (null if unemployed/unknown; "further_study" if postgrad) |
| `salary_band` | integer | 1–5 salary proxy (null if not employed) |
| `time_to_outcome_months` | integer | Months from graduation to outcome (0–24) |
| `outcome_recorded_at` | string | ISO date of outcome survey (~15 months post-graduation) |

**Notes**:
- Outcome gaps emerge from degree classification, SES, disability, and programme — no direct species/clan modifier
- `degree_classification` uses UK standard weighting: Year 1 excluded, Year 2 = 1/3, Year 3 = 2/3
- SES gradient on `professional_level` and `salary_band` is intentional (social capital effect)
- `employment_sector` values are mapped from faculty: see `config/graduate_outcomes.yaml`

---

### `stonegrove_nss_responses.csv`

**Purpose**: NSS-style satisfaction survey responses. One row per final-year (programme_year == 3) student per academic year, including students repeating their final year.

| Column | Type | Description |
|--------|------|-------------|
| `student_id` | string | Persistent unique identifier |
| `academic_year` | string | Academic year the survey was taken |
| `programme_code` | string | Programme code |
| `programme_year` | integer | Always 3 (final year only) |
| `is_repeat_year` | boolean | True if student is repeating Year 3 |
| `teaching_quality` | integer | Score 1–5 |
| `learning_opportunities` | integer | Score 1–5 |
| `assessment_feedback` | integer | Score 1–5 (historically lowest theme) |
| `academic_support` | integer | Score 1–5 |
| `organisation_management` | integer | Score 1–5 |
| `learning_resources` | integer | Score 1–5 |
| `student_voice` | integer | Score 1–5 (typically low; students feel less heard) |
| `overall_satisfaction` | integer | Score 1–5 (weighted blend, not simple average) |

**Notes**:
- `% positive` = proportion scoring 4 or 5 (standard NSS reporting convention)
- Scores modelled from: base score + engagement signal + mark signal (A&F) + SES + disability + personality + correlated student bias + independent per-theme noise
- `overall_satisfaction` is a weighted blend of theme raw scores, not their mean (mirrors real NSS Q27 behaviour)
- Repeating Yr3 students included; `repeat_year_modifier` lowers overall_satisfaction and organisation_management slightly
- No direct species/clan modifier — gaps emerge from SES, disability, and personality
- Config: `config/nss_modifiers.yaml`

---

### Semester summaries (not a core output)

Semester summaries are not produced by the longitudinal pipeline. Analysts can aggregate from `stonegrove_weekly_engagement.csv` (e.g. by student, academic_year, semester) if needed.

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
- `stonegrove_assessment_events.csv`: 4 rows (2 modules × 2 components: MIDTERM + FINAL), with `module_code`, `component_code`, `combined_mark` on FINAL rows

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

- `species`
- `clan` (ethnicity)
- `gender`
- `disabilities`
- `socio_economic_rank`
- `education` (prior educational experience)

No special "gap" columns are provided; users analyze patterns themselves.

---

**See Also**: `docs/CALCULATIONS.md` for how these values are computed.
