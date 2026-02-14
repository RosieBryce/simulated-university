import pandas as pd
import numpy as np
import random
from typing import Dict, List, Tuple

class CurriculumAssessmentSystem:
    """
    Assessment system for Stonegrove University that generates marks for students
    based on the actual curriculum module structure.
    """
    
    def __init__(self, seed: int = 42):
        self.seed = seed
        np.random.seed(seed)
        random.seed(seed)
        self.curriculum_df = None
        self.modules_df = None
        self._load_curriculum()
        self._setup_assessment_rules()
    
    def _load_curriculum(self):
        """Load the curriculum structure and modules from Excel file."""
        try:
            self.curriculum_df = pd.read_excel('Stonegrove_University_Curriculum.xlsx', sheet_name='Programmes')
            self.modules_df = pd.read_excel('Stonegrove_University_Curriculum.xlsx', sheet_name='Modules')
            print(f"✅ Loaded curriculum with {len(self.curriculum_df)} programs")
            print(f"✅ Loaded modules with {len(self.modules_df)} total modules")
            
            # Filter for Year 1 modules only
            self.year1_modules = self.modules_df[self.modules_df['Year'] == 1].copy()
            print(f"✅ Found {len(self.year1_modules)} Year 1 modules")
            
        except Exception as e:
            print(f"❌ Error loading curriculum: {e}")
            raise
    
    def _setup_assessment_rules(self):
        """Setup assessment rules and mark distributions."""
        
        # Base mark distribution (skewed towards 56-64 range)
        # Using a mixture of normal distributions to create the desired curve
        self.mark_distributions = {
            'base': {
                'mean': 60,  # Center around 60
                'std': 8,    # Standard deviation
                'weight': 0.7  # 70% of students follow this distribution
            },
            'high_performers': {
                'mean': 75,  # High performers
                'std': 6,
                'weight': 0.15  # 15% of students
            },
            'struggling': {
                'mean': 45,  # Struggling students
                'std': 10,
                'weight': 0.15  # 15% of students
            }
        }
        
        # Performance modifiers based on characteristics
        self.performance_modifiers = {
            # Species modifiers
            'species': {
                'Elf': 1.1,      # Elves tend to outperform dwarves
                'Dwarf': 0.95    # Dwarves slightly underperform
            },
            
            # Ethnicity modifiers
            'ethnicity': {
                'Baobab': 1.15,   # Baobab elves consistently perform highest
                'Alabaster': 0.85, # Alabaster dwarves get lowest marks
                'default': 1.0
            },
            
            # Disability modifiers
            'disabilities': {
                'specific_learning_disability': 0.8,      # Perform less well
                'requires_personal_care': 0.75,           # Perform less well
                'blind_or_visually_impaired': 0.8,        # Perform less well
                'communication_difficulties': 0.8,        # Perform less well
                'physical_disability': 1.05,              # Tend to perform better
                'mental_health_disability': 1.05,         # Tend to perform better
                'autistic_spectrum': 1.1,                 # Tend to perform better
                'adhd': 1.05,                              # Tend to perform better
                'dyslexia': 1.05,                         # Tend to perform better
                'other_neurodivergence': 1.1,             # Tend to perform better
                'deaf_or_hearing_impaired': 1.05,         # Tend to perform better
                'wheelchair_user': 1.05,                  # Tend to perform better
                'no_known_disabilities': 1.0              # Baseline
            },
            
            # Educational background modifiers
            'education': {
                'Academic': 1.05,    # Academic background helps slightly
                'Vocational': 0.98   # Vocational background slightly lower
            },
            
            # Socio-economic class modifiers
            'socio_economic': {
                1: 0.9,   # Lower class - slight disadvantage
                2: 0.95,
                3: 1.0,   # Middle class - baseline
                4: 1.05,
                5: 1.1    # Upper class - slight advantage
            }
        }
        
        # Module difficulty modifiers based on module titles
        self.module_difficulty = {
            # Foundation/Introduction modules are easier
            'introduction': 1.05,
            'foundations': 1.05,
            'basic': 1.05,
            'elementary': 1.05,
            
            # Advanced/Complex modules are harder
            'advanced': 0.9,
            'complex': 0.9,
            'advanced': 0.9,
            'capstone': 0.85,
            'research': 0.92,
            'theoretical': 0.95,
            
            # Practical modules are moderate
            'practical': 1.0,
            'practice': 1.0,
            'applied': 1.0,
            'hands-on': 1.02,
            
            # Default difficulty
            'default': 1.0
        }
    
    def get_module_difficulty(self, module_title: str) -> float:
        """Determine module difficulty based on title keywords."""
        title_lower = module_title.lower()
        
        for keyword, modifier in self.module_difficulty.items():
            if keyword in title_lower:
                return modifier
        
        return self.module_difficulty['default']
    
    def generate_student_base_mark(self, student_data: pd.Series) -> float:
        """Generate a base mark for a student based on their characteristics."""
        
        # Choose distribution based on student characteristics
        if random.random() < self.mark_distributions['base']['weight']:
            dist = self.mark_distributions['base']
        elif random.random() < self.mark_distributions['high_performers']['weight'] / (1 - self.mark_distributions['base']['weight']):
            dist = self.mark_distributions['high_performers']
        else:
            dist = self.mark_distributions['struggling']
        
        # Generate base mark
        base_mark = np.random.normal(dist['mean'], dist['std'])
        
        # Apply performance modifiers
        modifier = 1.0
        
        # Race modifier
        species_modifier = self.performance_modifiers['species'].get(student_data['species'], 1.0)
        modifier *= species_modifier
        
        # Ethnicity modifier
        ethnicity_modifier = self.performance_modifiers['ethnicity'].get(
            student_data['ethnicity'], 
            self.performance_modifiers['ethnicity']['default']
        )
        modifier *= ethnicity_modifier
        
        # Disability modifiers
        disability_modifier = 1.0
        for disability in self.performance_modifiers['disabilities'].keys():
            if disability in student_data and student_data[disability] == True:
                disability_modifier *= self.performance_modifiers['disabilities'][disability]
        
        modifier *= disability_modifier
        
        # Education background modifier
        education_modifier = self.performance_modifiers['education'].get(
            student_data['prior_educational_experience'], 1.0
        )
        modifier *= education_modifier
        
        # Socio-economic class modifier
        socio_modifier = self.performance_modifiers['socio_economic'].get(
            student_data['socio_economic_class_rank'], 1.0
        )
        modifier *= socio_modifier
        
        # Apply modifier to base mark
        adjusted_mark = base_mark * modifier
        
        # Ensure mark is within bounds (0-100)
        adjusted_mark = max(0, min(100, adjusted_mark))
        
        return adjusted_mark
    
    def generate_module_mark(self, student_data: pd.Series, module_title: str) -> float:
        """Generate a mark for a specific module."""
        
        # Get base mark for student
        base_mark = self.generate_student_base_mark(student_data)
        
        # Apply module difficulty modifier
        module_modifier = self.get_module_difficulty(module_title)
        module_mark = base_mark * module_modifier
        
        # Add some randomness for individual module performance
        # Students don't perform identically across all modules
        performance_variation = np.random.normal(0, 5)  # ±5 points variation
        final_mark = module_mark + performance_variation
        
        # Ensure mark is within bounds (0-100)
        final_mark = max(0, min(100, final_mark))
        
        return round(final_mark, 1)
    
    def generate_assessment_data(self, enrolled_df: pd.DataFrame) -> pd.DataFrame:
        """Generate assessment marks for all students across their actual Year 1 modules."""
        
        print("📝 Generating assessment marks for actual curriculum modules...")
        
        assessment_records = []
        
        for idx, student in enrolled_df.iterrows():
            if idx % 1000 == 0:
                print(f"  Processing student {idx + 1}/{len(enrolled_df)}")
            
            # Get student's program code
            programme_code = student['programme_code']
            
            # Get all Year 1 modules for this program
            program_modules = self.year1_modules[
                self.year1_modules['Programme code'] == programme_code
            ]
            
            if len(program_modules) == 0:
                print(f"⚠️  No Year 1 modules found for program {programme_code}")
                continue
            
            # Generate marks for each module in the program
            for _, module in program_modules.iterrows():
                mark = self.generate_module_mark(student, module['Module Title'])
                
                # Create record with all student information
                record = {
                    'student_id': student['student_id'],
                    'academic_year': student['academic_year'],
                    'faculty': student['faculty'],
                    'department': student['department'],
                    'programme': student['programme'],
                    'programme_code': programme_code,
                    'module_title': module['Module Title'],
                    'module_year': module['Year'],
                    'assessment_mark': mark,
                    'grade': self._calculate_grade(mark),
                    'species': student['species'],
                    'ethnicity': student['ethnicity'],
                    'gender': student['gender'],
                    'prior_educational_experience': student['prior_educational_experience'],
                    'socio_economic_class_rank': student['socio_economic_class_rank']
                }
                
                # Add disability information
                disability_columns = [col for col in enrolled_df.columns if any(disability in col for disability in 
                               ['physical_disability', 'mental_health_disability', 'specific_learning_disability', 
                                'autistic_spectrum', 'adhd', 'dyslexia', 'other_neurodivergence', 
                                'deaf_or_hearing_impaired', 'wheelchair_user', 'requires_personal_care', 
                                'blind_or_visually_impaired', 'communication_difficulties', 'no_known_disabilities'])]
                
                for disability in disability_columns:
                    if disability in student:
                        record[disability] = student[disability]
                
                assessment_records.append(record)
        
        assessment_df = pd.DataFrame(assessment_records)
        print("✅ Assessment marks generated!")
        return assessment_df
    
    def _calculate_grade(self, mark: float) -> str:
        """Calculate grade based on mark."""
        if mark >= 70:
            return "First"
        elif mark >= 60:
            return "2:1"
        elif mark >= 50:
            return "2:2"
        elif mark >= 40:
            return "Third"
        else:
            return "Fail"
    
    def analyze_assessment_data(self, assessment_df: pd.DataFrame):
        """Analyze assessment data and verify specifications."""
        
        print("\n📊 ASSESSMENT ANALYSIS")
        print("=" * 60)
        
        # Overall mark distribution
        print(f"\n📈 MARK DISTRIBUTION:")
        mark_ranges = [
            (0, 39, "Fail"),
            (40, 49, "Third"),
            (50, 59, "2:2"),
            (60, 69, "2:1"),
            (70, 100, "First")
        ]
        
        for min_mark, max_mark, grade_name in mark_ranges:
            count = len(assessment_df[(assessment_df['assessment_mark'] >= min_mark) & 
                                    (assessment_df['assessment_mark'] <= max_mark)])
            percentage = (count / len(assessment_df)) * 100
            print(f"  {grade_name} ({min_mark}-{max_mark}): {count:,} marks ({percentage:.1f}%)")
        
        # Check 56-64 range (should be large proportion)
        range_56_64 = len(assessment_df[(assessment_df['assessment_mark'] >= 56) & 
                                       (assessment_df['assessment_mark'] <= 64)])
        range_percentage = (range_56_64 / len(assessment_df)) * 100
        print(f"\n  📊 Marks 56-64: {range_56_64:,} marks ({range_percentage:.1f}%)")
        
        # Performance by species
        print(f"\n👥 PERFORMANCE BY SPECIES:")
        for species in assessment_df['species'].unique():
            species_marks = assessment_df[assessment_df['species'] == species]['assessment_mark']
            avg_mark = species_marks.mean()
            print(f"  {species}: {avg_mark:.1f} average mark")
        
        # Performance by ethnicity
        print(f"\n🏛️  PERFORMANCE BY ETHNICITY:")
        ethnicity_performance = assessment_df.groupby('ethnicity')['assessment_mark'].mean().sort_values(ascending=False)
        for ethnicity, avg_mark in ethnicity_performance.head(10).items():
            print(f"  {ethnicity}: {avg_mark:.1f} average mark")
        
        # Performance by disability
        print(f"\n♿ PERFORMANCE BY DISABILITY STATUS:")
        disability_columns = [col for col in assessment_df.columns if any(disability in col for disability in 
                           ['physical_disability', 'mental_health_disability', 'specific_learning_disability', 
                            'autistic_spectrum', 'adhd', 'dyslexia', 'other_neurodivergence', 
                            'deaf_or_hearing_impaired', 'wheelchair_user', 'requires_personal_care', 
                            'blind_or_visually_impaired', 'communication_difficulties'])]
        
        if disability_columns:
            for disability in disability_columns:
                if disability in assessment_df.columns:
                    disabled_marks = assessment_df[assessment_df[disability] == True]['assessment_mark']
                    non_disabled_marks = assessment_df[assessment_df[disability] == False]['assessment_mark']
                    if len(disabled_marks) > 0 and len(non_disabled_marks) > 0:
                        disabled_avg = disabled_marks.mean()
                        non_disabled_avg = non_disabled_marks.mean()
                        print(f"  {disability}: {disabled_avg:.1f} vs {non_disabled_avg:.1f} (disabled vs non-disabled)")
        
        # Program performance
        print(f"\n📚 PERFORMANCE BY PROGRAM:")
        program_performance = assessment_df.groupby('programme')['assessment_mark'].mean().sort_values(ascending=False)
        for program, avg_mark in program_performance.head(10).items():
            print(f"  {program}: {avg_mark:.1f} average mark")
        
        # Faculty performance
        print(f"\n🏛️  PERFORMANCE BY FACULTY:")
        faculty_performance = assessment_df.groupby('faculty')['assessment_mark'].mean().sort_values(ascending=False)
        for faculty, avg_mark in faculty_performance.items():
            print(f"  {faculty}: {avg_mark:.1f} average mark")
        
        # Module analysis
        print(f"\n📖 MODULE ANALYSIS:")
        print(f"  Total unique modules: {assessment_df['module_title'].nunique()}")
        print(f"  Average modules per student: {len(assessment_df) / assessment_df['student_id'].nunique():.1f}")
        
        # Top performing modules
        print(f"\n🏆 TOP PERFORMING MODULES:")
        module_performance = assessment_df.groupby('module_title')['assessment_mark'].mean().sort_values(ascending=False)
        for module, avg_mark in module_performance.head(5).items():
            print(f"  {module}: {avg_mark:.1f} average mark")
        
        # Lowest performing modules
        print(f"\n📉 LOWEST PERFORMING MODULES:")
        for module, avg_mark in module_performance.tail(5).items():
            print(f"  {module}: {avg_mark:.1f} average mark")

def main():
    """Main function to generate assessment data."""
    print("🏛️  Stonegrove University Curriculum-Based Assessment System")
    print("=" * 60)
    
    # Load enrolled population
    try:
        enrolled_df = pd.read_csv('stonegrove_enrolled_population.csv')
        print(f"✅ Loaded enrolled population: {len(enrolled_df)} students")
    except FileNotFoundError:
        print("❌ Enrolled population file not found. Please run enrollment_system.py first.")
        return
    
    # Initialize assessment system
    assessment_system = CurriculumAssessmentSystem()
    
    # Generate assessment data
    assessment_df = assessment_system.generate_assessment_data(enrolled_df)
    
    # Analyze assessment data
    assessment_system.analyze_assessment_data(assessment_df)
    
    # Save assessment data
    output_filename = "stonegrove_curriculum_assessment_marks.csv"
    assessment_df.to_csv(output_filename, index=False)
    print(f"\n✅ Curriculum-based assessment marks saved to: {output_filename}")
    
    # Print summary
    print(f"\n📋 ASSESSMENT SUMMARY:")
    print(f"  Total assessment records: {len(assessment_df)}")
    print(f"  Unique students: {assessment_df['student_id'].nunique()}")
    print(f"  Unique modules: {assessment_df['module_title'].nunique()}")
    print(f"  Average modules per student: {len(assessment_df) / assessment_df['student_id'].nunique():.1f}")
    print(f"  Overall average mark: {assessment_df['assessment_mark'].mean():.1f}")
    print(f"  Pass rate: {(len(assessment_df[assessment_df['assessment_mark'] >= 40]) / len(assessment_df)) * 100:.1f}%")
    print(f"  Fail rate: {(len(assessment_df[assessment_df['assessment_mark'] < 40]) / len(assessment_df)) * 100:.1f}%")
    
    # Show sample of the data
    print(f"\n📋 SAMPLE ASSESSMENT RECORDS:")
    print(assessment_df[['student_id', 'programme', 'module_title', 'assessment_mark', 'grade']].head(10).to_string(index=False))

if __name__ == "__main__":
    main() 