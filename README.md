# Stonegrove University Individual-Level Modeling System

A sophisticated simulation system for modeling individual student behavior, engagement, and academic progression at Stonegrove University.

## 🎯 Project Overview

This system generates unique students with personality traits, motivations, and behavioral patterns that influence their academic journey. It models individual-level characteristics including:

- **Personality profiles** (Big Five + academic dimensions)
- **Motivation dimensions** (8 types with personality nudging)
- **Health/disability status** with realistic distributions
- **Program enrollment** based on clan affinities and personality
- **Weekly engagement** patterns with module-specific modifiers
- **Semester-level summaries** with trends and risk factors

## 📁 Project Structure

```
simulated-university/
├── config/                          # Configuration files
│   ├── clan_personality_specifications.yaml
│   ├── clan_name_pools.yaml
│   ├── clan_program_affinities.yaml
│   ├── disability_distribution.yaml
│   ├── module_characteristics.csv    # (or .yaml) module difficulty, assessment_type, etc.
│   ├── programme_characteristics.csv # (or program_characteristics.yaml) programme attributes
├── core_systems/                     # Main modeling systems
│   ├── student_generation_pipeline.py
│   ├── program_enrollment_system.py
│   ├── engagement_system.py
│   └── assessment_system.py
├── supporting_systems/               # Utility systems
│   ├── name_generator.py
│   ├── personality_refinement_system.py
│   └── motivation_profile_system.py
├── data/                            # Generated data
│   ├── stonegrove_individual_students.csv
│   ├── stonegrove_enrolled_students.csv
│   ├── stonegrove_weekly_engagement.csv
│   ├── stonegrove_semester_engagement.csv
│   └── stonegrove_assessment_events.csv
├── visualizations/                   # Analysis outputs
│   ├── stonegrove_enrollment_analysis.png
│   └── stonegrove_engagement_analysis.png
├── Instructions and guides/          # Source materials
│   ├── Stonegrove_University_Curriculum.xlsx
│   └── World-building/
├── archive_population_model/         # Archived population-level files
├── docs/                            # Documentation (DESIGN, SCHEMA, PROJECT_SUMMARY, etc.)
└── project_tracker/                 # Tickets and progress
```

## 🚀 Quick Start

**Run all commands from the project root.**

### Prerequisites
```bash
pip install pandas numpy matplotlib seaborn scipy openpyxl xlrd PyYAML
```

### Run full pipeline (recommended)
```bash
python run_pipeline.py
```
Runs: student generation → enrollment → engagement → assessment.

### Or run steps individually
```bash
python core_systems/student_generation_pipeline.py
python core_systems/program_enrollment_system.py
python core_systems/engagement_system.py
python core_systems/assessment_system.py
```

### Create Visualizations
```bash
python archive_population_model/enrollment_visualization.py
python metaanalysis/engagement_visualization.py
```

## 📊 Current System Capabilities

### Student Generation
- **500 individual students** with complete characteristics
- **Race distribution**: 60% Dwarf, 40% Elf
- **14 clans** with unique personality ranges and motivations
- **Realistic name generation** from clan-specific pools
- **Personality refinement** based on disabilities, socio-economic rank, education, age

### Program Enrollment
- **44 programs** across 4 faculties
- **Clan-program affinities** driving selection
- **Personality/motivation modifiers** for realistic choices
- **Year 1 modules** automatically assigned

### Engagement Modeling
- **23,916 weekly engagement records** (12 weeks × ~2 modules × 500 students)
- **500 semester engagement summaries** with trends and risk factors
- **Module-specific modifiers** for difficulty, social requirements, creativity
- **Weekly variation** with realistic fluctuations

## 📈 Key Statistics

### Engagement Performance
- **Average attendance rate**: 68.7%
- **Average participation score**: 51.7%
- **Average academic engagement**: 66.8%
- **Average social engagement**: 63.2%
- **Average stress level**: 48.8%

### Strong Personality-Engagement Correlations
- **Conscientiousness vs Attendance**: 0.856 (very strong)
- **Extraversion vs Participation**: 0.923 (very strong)
- **Openness vs Academic Engagement**: 0.820 (very strong)

### Risk Factors
- **175 students** with low attendance
- **143 students** with low participation
- **88 students** with no risk factors

## 🎯 Next Development Phase

### Phase 1: Data Quality & Validation
- [ ] IMPORT ALL XLSX FILES INTO A SOLID DATA STRUCTURE! (like curriculum)
- [ ] Fix module name parsing issues
- [ ] Review module difficulty estimation
- [ ] Clarify engagement metrics (social vs participation)
- [ ] Define motivation dimensions (intellectual vs academic)
- [ ] Implement program characteristics

### Phase 2: Assessment System
- [ ] Create assessment modeling system
- [ ] Implement mark generation with realistic distributions
- [ ] Add performance modifiers (disability, clan, personality)

### Phase 3: Longitudinal Progression
- [ ] Year 2-3 progression logic
- [ ] Graduation modeling
- [ ] Career outcomes

### Phase 4: Intervention Framework
- [ ] Extra-curricular activities
- [ ] Support programs
- [ ] Evaluation methods

## 🔧 Configuration

### Clan Personality Specifications
Edit `config/clan_personality_specifications.yaml` to modify:
- Personality ranges for each clan
- Health/disability tendencies
- Motivation dimensions

### Program Affinities
Edit `config/clan_program_affinities.yaml` to adjust:
- Clan preferences for specific programs
- Affinity scores and selection rules

### Disability Distributions
Edit `config/disability_distribution.yaml` to change:
- Disability prevalence by race
- Overall proportions

## 📋 Files Overview

### Core Systems
- **`student_generation_pipeline.py`**: Main student generation system
- **`program_enrollment_system.py`**: Program selection and enrollment
- **`engagement_system.py`**: Weekly and semester engagement modeling
- **`assessment_system.py`**: End-of-module marks (stonegrove_assessment_events.csv)

### Supporting Systems
- **`name_generator.py`**: Clan-specific name generation
- **`personality_refinement_system.py`**: Personality trait modification
- **`motivation_profile_system.py`**: Motivation dimension generation

### Data Files
- **`stonegrove_individual_students.csv`**: Base student population
- **`stonegrove_enrolled_students.csv`**: Students with program enrollment
- **`stonegrove_weekly_engagement.csv`**: Weekly engagement data
- **`stonegrove_semester_engagement.csv`**: Semester summaries
- **`stonegrove_assessment_events.csv`**: Assessment marks (module_code, component_code)

### Visualizations
- **`stonegrove_enrollment_analysis.png`**: Program enrollment patterns
- **`stonegrove_engagement_analysis.png`**: Engagement trends and correlations

## 🎓 Academic Structure

### Faculties
1. **Faculty of Applied Forging** (23% of students)
2. **Faculty of Hearth and Transformation** (28.6% of students)
3. **Faculty of Integrative Inquiry** (13% of students)
4. **Faculty of Living Lore** (35.4% of students)

### Programs
- 44 unique programs across all faculties
- Clan-specific affinities influence program selection
- Personality and motivation provide individual variation

### Modules
- Year 1 modules automatically assigned based on program
- Module characteristics (difficulty, social requirements, creativity) affect engagement
- Average 2.1 modules per student

## 🔄 Git Workflow

1. **Current State**: Individual-level modeling with engagement system
2. **Next Branch**: Create feature branch for assessment system
3. **Development**: Implement fixes and new features
4. **Validation**: Test and validate before merging

## 📚 Documentation

- **`docs/PROJECT_SUMMARY.md`**: Pick-up guide and project status
- **`Instructions and guides/`**: Source materials and world-building documents
- **`archive_population_model/`**: Archived population-level modeling files

---

**Current Version**: Individual-level student modeling with engagement system
**Next Focus**: Data quality fixes and assessment system implementation
**Key Priority**: Fix module parsing and clarify engagement metrics 