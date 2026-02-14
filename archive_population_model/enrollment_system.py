import pandas as pd
import numpy as np
import yaml
import os
from typing import Dict, List, Tuple

class StonegroveEnrollmentSystem:
    """
    Enrollment system for Stonegrove University that assigns students to programs
    based on species, gender, and educational background preferences.
    """
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self.curriculum_df = None
        self.program_preferences = {}
        self._load_curriculum()
        self._setup_program_preferences()
    
    def _load_curriculum(self):
        """Load the curriculum structure from Excel file."""
        try:
            self.curriculum_df = pd.read_excel('Stonegrove_University_Curriculum.xlsx')
            print(f"✅ Loaded curriculum with {len(self.curriculum_df)} programs")
        except Exception as e:
            print(f"❌ Error loading curriculum: {e}")
            raise
    
    def _setup_program_preferences(self):
        """Setup program enrollment preferences based on specifications."""
        
        # Get all programs
        all_programs = self.curriculum_df['Programme'].tolist()
        
        # Base popularity weights (higher = more popular)
        base_popularity = {}
        
        # Most popular: Brewcraft and Fermentation Systems
        base_popularity['Brewcraft and Fermentation Systems'] = 100
        
        # Very popular: Language and Symbol department programs
        language_symbol_programs = [
            'Ancient Tongues and Translation',
            'Comparative Runes and Scripts', 
            'Multispecies Semantics'
        ]
        for program in language_symbol_programs:
            base_popularity[program] = 85
        
        # Least popular: Transdisciplinary Design and Praxis programs
        transdisciplinary_programs = [
            'Knowledge System Prototyping',
            'Embodied Research Methods'
        ]
        for program in transdisciplinary_programs:
            base_popularity[program] = 5
        
        # Critical Power is female-dominated
        base_popularity['Critical Power'] = 60  # Moderate popularity but female preference
        
        # Set default popularity for other programs
        for program in all_programs:
            if program not in base_popularity:
                base_popularity[program] = 30  # Default moderate popularity
        
        # Faculty preferences by species
        faculty_preferences = {
            'Dwarf': {
                'Faculty of Applied Forging': 1.8,      # Dwarves prefer Applied Forging
                'Faculty of Living Lore': 1.6,          # Dwarves also prefer Living Lore
                'Faculty of Hearth and Transformation': 0.8,
                'Faculty of Integrative Inquiry': 0.6
            },
            'Elf': {
                'Faculty of Integrative Inquiry': 1.4,  # Elves prefer Integrative Inquiry
                'Faculty of Hearth and Transformation': 1.2,
                'Faculty of Living Lore': 1.0,
                'Faculty of Applied Forging': 0.3       # Elves rarely in Applied Forging
            }
        }
        
        # Gender preferences
        gender_preferences = {
            'Female': {
                'Critical Power': 2.5,  # Female students strongly prefer Critical Power
                'Faculty of Integrative Inquiry': 1.3,  # Female Elves prefer Integrative Inquiry
                'Faculty of Hearth and Transformation': 0.8
            },
            'Male': {
                'Faculty of Applied Forging': 1.2,
                'Critical Power': 0.4   # Male students less likely in Critical Power
            },
            'Other': {
                'Faculty of Integrative Inquiry': 1.1,
                'Faculty of Hearth and Transformation': 1.0
            }
        }
        
        # Educational background preferences
        education_preferences = {
            'Academic': {
                'Faculty of Integrative Inquiry': 1.4,
                'Faculty of Living Lore': 1.2,
                'Critical Power': 1.3
            },
            'Vocational': {
                'Faculty of Applied Forging': 1.3,
                'Faculty of Hearth and Transformation': 1.2
            }
        }
        
        self.program_preferences = {
            'base_popularity': base_popularity,
            'faculty_preferences': faculty_preferences,
            'gender_preferences': gender_preferences,
            'education_preferences': education_preferences
        }
    
    def calculate_program_weights(self, student_data: pd.Series) -> Dict[str, float]:
        """Calculate enrollment weights for each program for a given student."""
        weights = {}
        
        species = student_data['species']
        gender = student_data['gender']
        education = student_data['prior_educational_experience']
        
        for _, program_row in self.curriculum_df.iterrows():
            program = program_row['Programme']
            faculty = program_row['Faculty']
            
            # Start with base popularity
            weight = self.program_preferences['base_popularity'].get(program, 30)
            
            # Apply faculty preference by species
            faculty_multiplier = self.program_preferences['faculty_preferences'][species].get(faculty, 1.0)
            weight *= faculty_multiplier
            
            # Apply gender preferences
            gender_multiplier = 1.0
            if gender in self.program_preferences['gender_preferences']:
                # Check for specific program preference
                if program in self.program_preferences['gender_preferences'][gender]:
                    gender_multiplier = self.program_preferences['gender_preferences'][gender][program]
                # Check for faculty preference
                elif faculty in self.program_preferences['gender_preferences'][gender]:
                    gender_multiplier = self.program_preferences['gender_preferences'][gender][faculty]
            
            weight *= gender_multiplier
            
            # Apply education background preferences
            education_multiplier = 1.0
            if education in self.program_preferences['education_preferences']:
                if faculty in self.program_preferences['education_preferences'][education]:
                    education_multiplier = self.program_preferences['education_preferences'][education][faculty]
            
            weight *= education_multiplier
            
            # Special case: Female Elves with academic background prefer Integrative Inquiry
            if (species == 'Elf' and gender == 'Female' and education == 'Academic' and 
                faculty == 'Faculty of Integrative Inquiry'):
                weight *= 1.5
            
            weights[program] = weight
        
        return weights
    
    def enroll_students(self, population_df: pd.DataFrame) -> pd.DataFrame:
        """Enroll students in programs based on preferences."""
        print("🎓 Enrolling students in programs...")
        
        # Add academic year column (all students are year 1)
        population_df['academic_year'] = 1
        
        # Initialize program assignment
        program_assignments = []
        
        for idx, student in population_df.iterrows():
            if idx % 1000 == 0:
                print(f"  Processing student {idx + 1}/{len(population_df)}")
            
            # Calculate weights for this student
            weights = self.calculate_program_weights(student)
            
            # Convert weights to probabilities
            total_weight = sum(weights.values())
            probabilities = [weights[program] / total_weight for program in weights.keys()]
            
            # Select program based on weights
            selected_program = np.random.choice(list(weights.keys()), p=probabilities)
            
            # Get program details
            program_info = self.curriculum_df[self.curriculum_df['Programme'] == selected_program].iloc[0]
            
            program_assignments.append({
                'student_id': student['student_id'],
                'faculty_code': program_info['Faculty code'],
                'faculty': program_info['Faculty'],
                'department_code': program_info['Department code'],
                'department': program_info['Department'],
                'programme_code': program_info['Programme code'],
                'programme': selected_program
            })
        
        # Create enrollment dataframe
        enrollment_df = pd.DataFrame(program_assignments)
        
        # Merge with original population
        result_df = population_df.merge(enrollment_df, on='student_id', how='left')
        
        print("✅ Enrollment completed!")
        return result_df
    
    def analyze_enrollment(self, enrolled_df: pd.DataFrame):
        """Analyze enrollment patterns and statistics."""
        print("\n📊 ENROLLMENT ANALYSIS")
        print("=" * 60)
        
        # Faculty distribution
        print(f"\n🏛️  FACULTY DISTRIBUTION:")
        faculty_counts = enrolled_df['faculty'].value_counts()
        for faculty, count in faculty_counts.items():
            percentage = (count / len(enrolled_df)) * 100
            print(f"  {faculty}: {count:,} students ({percentage:.1f}%)")
        
        # Program popularity
        print(f"\n📚 MOST POPULAR PROGRAMS:")
        program_counts = enrolled_df['programme'].value_counts().head(10)
        for program, count in program_counts.items():
            percentage = (count / len(enrolled_df)) * 100
            print(f"  {program}: {count:,} students ({percentage:.1f}%)")
        
        # Species distribution by faculty
        print(f"\n👥 SPECIES DISTRIBUTION BY FACULTY:")
        for faculty in enrolled_df['faculty'].unique():
            faculty_subset = enrolled_df[enrolled_df['faculty'] == faculty]
            print(f"\n  {faculty}:")
            species_counts = faculty_subset['species'].value_counts()
            for species, count in species_counts.items():
                percentage = (count / len(faculty_subset)) * 100
                print(f"    {species}: {count:,} students ({percentage:.1f}%)")
        
        # Gender distribution by faculty
        print(f"\n⚧ GENDER DISTRIBUTION BY FACULTY:")
        for faculty in enrolled_df['faculty'].unique():
            faculty_subset = enrolled_df[enrolled_df['faculty'] == faculty]
            print(f"\n  {faculty}:")
            gender_counts = faculty_subset['gender'].value_counts()
            for gender, count in gender_counts.items():
                percentage = (count / len(faculty_subset)) * 100
                print(f"    {gender}: {count:,} students ({percentage:.1f}%)")
        
        # Critical Power analysis
        critical_power_students = enrolled_df[enrolled_df['programme'] == 'Critical Power']
        if len(critical_power_students) > 0:
            print(f"\n⚡ CRITICAL POWER PROGRAM ANALYSIS:")
            print(f"  Total students: {len(critical_power_students)}")
            gender_dist = critical_power_students['gender'].value_counts()
            for gender, count in gender_dist.items():
                percentage = (count / len(critical_power_students)) * 100
                print(f"    {gender}: {count:,} students ({percentage:.1f}%)")
        
        # Transdisciplinary Design analysis
        transdisciplinary_students = enrolled_df[
            enrolled_df['programme'].isin(['Knowledge System Prototyping', 'Embodied Research Methods'])
        ]
        if len(transdisciplinary_students) > 0:
            print(f"\n🔬 TRANSDISCIPLINARY DESIGN PROGRAMS:")
            print(f"  Total students: {len(transdisciplinary_students)}")
            program_dist = transdisciplinary_students['programme'].value_counts()
            for program, count in program_dist.items():
                percentage = (count / len(enrolled_df)) * 100
                print(f"    {program}: {count:,} students ({percentage:.1f}%)")
        
        # Language and Symbol analysis
        language_students = enrolled_df[
            enrolled_df['programme'].isin(['Ancient Tongues and Translation', 'Comparative Runes and Scripts', 'Multispecies Semantics'])
        ]
        if len(language_students) > 0:
            print(f"\n📖 LANGUAGE AND SYMBOL PROGRAMS:")
            print(f"  Total students: {len(language_students)}")
            program_dist = language_students['programme'].value_counts()
            for program, count in program_dist.items():
                percentage = (count / len(enrolled_df)) * 100
                print(f"    {program}: {count:,} students ({percentage:.1f}%)")
        
        # Brewcraft analysis
        brewcraft_students = enrolled_df[enrolled_df['programme'] == 'Brewcraft and Fermentation Systems']
        if len(brewcraft_students) > 0:
            print(f"\n🍺 BREWCRAFT AND FERMENTATION SYSTEMS:")
            print(f"  Total students: {len(brewcraft_students)}")
            species_dist = brewcraft_students['species'].value_counts()
            for species, count in species_dist.items():
                percentage = (count / len(brewcraft_students)) * 100
                print(f"    {species}: {count:,} students ({percentage:.1f}%)")

def main():
    """Main function to enroll students."""
    print("🏛️  Stonegrove University Enrollment System")
    print("=" * 50)
    
    # Load current population
    try:
        population_df = pd.read_csv('stonegrove_university_population.csv')
        print(f"✅ Loaded population: {len(population_df)} students")
    except FileNotFoundError:
        print("❌ Population file not found. Please run population_generator.py first.")
        return
    
    # Initialize enrollment system
    enrollment_system = StonegroveEnrollmentSystem()
    
    # Enroll students
    enrolled_df = enrollment_system.enroll_students(population_df)
    
    # Analyze enrollment
    enrollment_system.analyze_enrollment(enrolled_df)
    
    # Save enrolled population
    output_filename = "stonegrove_enrolled_population.csv"
    enrolled_df.to_csv(output_filename, index=False)
    print(f"\n✅ Enrolled population saved to: {output_filename}")
    
    # Print summary
    print(f"\n📋 ENROLLMENT SUMMARY:")
    print(f"  Total students enrolled: {len(enrolled_df)}")
    print(f"  Academic year: {enrolled_df['academic_year'].iloc[0]}")
    print(f"  Total programs: {enrolled_df['programme'].nunique()}")
    print(f"  Total faculties: {enrolled_df['faculty'].nunique()}")
    print(f"  Total departments: {enrolled_df['department'].nunique()}")
    
    # Show new columns
    new_columns = ['academic_year', 'faculty_code', 'faculty', 'department_code', 'department', 'programme_code', 'programme']
    print(f"\n📋 NEW COLUMNS ADDED:")
    for i, col in enumerate(new_columns, 1):
        print(f"  {i:2d}. {col}")

if __name__ == "__main__":
    main() 