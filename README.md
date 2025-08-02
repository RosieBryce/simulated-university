# Stonegrove University Population Generator

A comprehensive Python tool for generating fictional student population data for Stonegrove University, a fantasy institution that admits Dwarves and Elves.

## 🏛️ About Stonegrove University

Stonegrove is a hybrid institution that blends the high academic standards and arcane traditions of the Elven university, Eldergrove, with the modern pedagogic and person-centred values of the Dwarven university, Stoneborn.

## 📊 Generated Population

- **Total Students**: 12,000
- **Races**: Dwarves (55%) and Elves (45%)
- **Data Fields**: 26 columns including demographics, disabilities, socio-economic information, and academic enrollment
- **Academic Structure**: 4 Faculties, 16 Departments, 44 Programs

## 🚀 Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Generate Population

```bash
python population_generator.py
```

This will create `stonegrove_university_population.csv` with 12,000 student records.

### Enroll Students

```bash
python enrollment_system.py
```

This will assign students to programs based on race, gender, and educational background preferences, creating `stonegrove_enrolled_population.csv`.

### Analyze Population

```bash
python population_analysis.py
```

This will generate detailed statistics and create `stonegrove_population_analysis.png`.

### Visualize Enrollment

```bash
python enrollment_visualization.py
```

This will create enrollment visualizations and analysis charts.

### Edit Configuration

```bash
python config_editor.py
```

This interactive tool helps you easily modify distribution percentages without editing YAML files directly.

## 🎓 Academic Structure

### Four Faculties

1. **Faculty of Applied Forging** - Practical crafts and engineering
2. **Faculty of Hearth and Transformation** - Healing, hospitality, and community
3. **Faculty of Integrative Inquiry** - Research and interdisciplinary studies
4. **Faculty of Living Lore** - Language, philosophy, and cultural studies

### Enrollment Preferences

- **Dwarves** prefer Applied Forging and Living Lore
- **Elves** prefer Integrative Inquiry and Hearth and Transformation
- **Elves in Applied Forging** are very rare
- **Female Elves** with academic backgrounds prefer Integrative Inquiry
- **Critical Power** program is female-dominated
- **Brewcraft and Fermentation Systems** is the most popular program
- **Language and Symbol** department programs are very popular
- **Transdisciplinary Design and Praxis** programs have very few students

## ⚙️ Configuration System

All distribution percentages are now stored in YAML files in the `config/` directory, making it easy to modify specific values:

### Configuration Files

- **`config/race_distribution.yaml`** - Race distribution (Dwarf/Elf percentages)
- **`config/gender_distribution.yaml`** - Gender distribution (Male/Female/Other)
- **`config/ethnicity_distribution.yaml`** - Ethnicity distribution by race
- **`config/disability_distribution.yaml`** - Disability rates by race
- **`config/education_distribution.yaml`** - Educational background by race
- **`config/socio_economic_distribution.yaml`** - Socio-economic class by race and ethnicity

### Quick Configuration Changes

**Example: Reduce wheelchair user percentage**

1. **Option 1: Use the config editor**
   ```bash
   python config_editor.py
   # Select disability_distribution.yaml
   # Modify wheelchair_user percentages
   ```

2. **Option 2: Edit YAML directly**
   ```yaml
   # In config/disability_distribution.yaml
   Dwarf:
     wheelchair_user: 0.01  # Change from 0.02 to 0.01 (1% instead of 2%)
   Elf:
     wheelchair_user: 0.01  # Change from 0.02 to 0.01 (1% instead of 2%)
   ```

3. **Regenerate population**
   ```bash
   python population_generator.py
   ```

## 📋 Data Specifications

### Demographics
- **Race**: Dwarf (55%), Elf (45%)
- **Gender**: Male (45%), Female (50%), Other (5%)
- **Ethnicity**: 12 different ethnicities distributed by race

### Dwarf Ethnicities
- Malachite (10%), Granite (15%), Gypsum (12.5%)
- Flint (35%), Alabaster (12.5%), Sandstone (15%)

### Elf Ethnicities
- Holly (10%), Yew (15%), Rowan (12.5%)
- Ash (12.5%), Baobab (35%), Palm (15%)

### Disabilities (13 Boolean Columns)
Different rates for Dwarves and Elves:
- Physical disability, Mental health disability
- Specific learning disability, Autistic spectrum
- ADHD, Dyslexia, Other neurodivergence
- Deaf/hearing impaired, Wheelchair user
- Requires personal care, Blind/visually impaired
- Communication difficulties, No known disabilities

### Educational Experience
- **Dwarves**: Academic (12%), Vocational (88%)
- **Elves**: Academic (78%), Vocational (22%)

### Socio-Economic Class Rank
- Scale: 1 (low) to 5 (high)
- Complex distributions by race and ethnicity

### Academic Enrollment
- **Academic Year**: All students start in Year 1
- **Faculty Assignment**: Based on race and gender preferences
- **Program Assignment**: Weighted by popularity and student characteristics
- **Department Structure**: Hierarchical organization within faculties

## 📁 Files

- `population_generator.py` - Main population generation script
- `enrollment_system.py` - Academic enrollment assignment script
- `population_analysis.py` - Analysis and visualization script
- `enrollment_visualization.py` - Enrollment pattern visualization
- `config_editor.py` - Interactive configuration editor
- `stonegrove_university_population.csv` - Generated population data
- `stonegrove_enrolled_population.csv` - Population with academic enrollment
- `stonegrove_population_analysis.png` - Population analysis charts
- `stonegrove_enrollment_analysis.png` - Enrollment analysis charts
- `stonegrove_program_analysis.png` - Program popularity analysis
- `requirements.txt` - Python dependencies
- `README.md` - This documentation
- `config/` - YAML configuration files
- `Stonegrove_University_Curriculum.xlsx` - Academic structure definition

## 🔧 Technical Details

### Dependencies
- pandas >= 1.5.0
- numpy >= 1.21.0
- matplotlib >= 3.5.0
- seaborn >= 0.11.0
- scipy >= 1.7.0
- openpyxl >= 3.0.0
- xlrd >= 2.0.0
- PyYAML >= 6.0

### Features
- ✅ Exact distribution matching (within 1% tolerance)
- ✅ Comprehensive validation
- ✅ Detailed analysis and visualization
- ✅ Reproducible results (seeded random generation)
- ✅ Clean CSV export
- ✅ **NEW**: YAML-based configuration system
- ✅ **NEW**: Interactive configuration editor
- ✅ **NEW**: Automatic distribution validation
- ✅ **NEW**: Academic enrollment system
- ✅ **NEW**: Program preference modeling
- ✅ **NEW**: Enrollment pattern analysis

## 📈 Sample Statistics

From the generated population:
- **Most common ethnicity**: Flint (Dwarves)
- **Average socio-economic class**: 3.38
- **Students with disabilities**: 5,585 (46.5%)
- **Students without disabilities**: 6,370 (53.1%)
- **Most diverse ethnicity**: Malachite (socio-economically)

From the enrollment data:
- **Most popular program**: Brewcraft and Fermentation Systems (744 students)
- **Least popular programs**: Transdisciplinary Design programs (105 total students)
- **Most popular faculty**: Faculty of Living Lore (4,730 students)
- **Critical Power female students**: 83.4%
- **Elves in Applied Forging**: 16.3% (rare as specified)

## 🎯 Use Cases

This population generator is perfect for:
- Educational data modeling
- Fantasy world-building
- Statistical analysis practice
- Diversity and inclusion research
- Academic simulation studies
- University enrollment modeling
- Program demand forecasting

## 🔄 Workflow

1. **Initial Setup**: Run `python population_generator.py` to create initial population
2. **Enroll Students**: Run `python enrollment_system.py` to assign academic programs
3. **Analyze**: Run `python population_analysis.py` to see demographic statistics
4. **Visualize**: Run `python enrollment_visualization.py` to see enrollment patterns
5. **Modify**: Use `python config_editor.py` to adjust percentages
6. **Regenerate**: Run `python population_generator.py` again to create new population
7. **Repeat**: Iterate until you're happy with the distributions

## 📝 License

This project is created for educational and research purposes. Feel free to modify and extend for your own needs. 