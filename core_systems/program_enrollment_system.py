import csv
import io
import pandas as pd
import numpy as np
import yaml
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


def _format_module_list_csv(modules: List[str]) -> str:
    """Format module list for CSV storage using proper quoting (handles commas in names)."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(modules)
    return buffer.getvalue().strip()

@dataclass
class ProgramEnrollment:
    """Container for program enrollment data"""
    student_id: str
    program_code: str
    program_name: str
    faculty: str
    department: str
    year_modules: List[str]
    enrollment_factors: Dict[str, float]

class ProgramEnrollmentSystem:
    """
    System to enroll students in programs and assign Year 1 modules
    based on clan affinities, personality, and other characteristics.
    """
    
    def __init__(self, curriculum_file: str = "Instructions and guides/Stonegrove_University_Curriculum.xlsx"):
        """Initialize the enrollment system with curriculum data"""
        self.curriculum_file = curriculum_file
        self.programs_df = None
        self.modules_df = None
        self.clan_affinities = None
        self._load_curriculum_data()
        self._load_clan_affinities()
        
    def _load_curriculum_data(self):
        """Load program and module data from curriculum Excel file"""
        # Load programs
        self.programs_df = pd.read_excel(self.curriculum_file, sheet_name='Programmes')
        
        # Load modules
        self.modules_df = pd.read_excel(self.curriculum_file, sheet_name='Modules')
        
        # Filter for Year 1 modules only
        self.year1_modules_df = self.modules_df[self.modules_df['Year'] == 1].copy()
        
        print(f"Loaded {len(self.programs_df)} programs across {self.programs_df['Faculty'].nunique()} faculties")
        print(f"Loaded {len(self.year1_modules_df)} Year 1 modules")
        
    def _load_clan_affinities(self):
        """Load clan program affinities from YAML"""
        with open('config/clan_program_affinities.yaml', 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            self.clan_affinities = data['clans']
            self.affinity_settings = data['settings']
            
    def get_program_affinity(self, clan: str, program_name: str) -> float:
        """Get affinity score for a clan-program combination"""
        if clan not in self.clan_affinities:
            return 0.05  # Default minimal affinity
            
        affinities = self.clan_affinities[clan]['program_affinities']
        return affinities.get(program_name, 0.05)  # Default minimal affinity
        
    def calculate_enrollment_probability(self, clan: str, program_name: str, 
                                       personality: Dict[str, float], 
                                       motivation: Dict[str, float]) -> float:
        """
        Calculate enrollment probability based on multiple factors:
        - Clan affinity (primary factor)
        - Personality traits (secondary modifiers)
        - Motivation dimensions (secondary modifiers)
        - Program characteristics (if available)
        """
        # Base affinity from clan
        base_affinity = self.get_program_affinity(clan, program_name)
        
        # Personality modifiers (small adjustments)
        personality_modifier = 0.0
        
        # Extraversion might influence social programs
        if 'social' in program_name.lower() or 'community' in program_name.lower():
            personality_modifier += (personality.get('refined_extraversion', 0.5) - 0.5) * 0.1
            
        # Conscientiousness might influence structured programs
        if 'governance' in program_name.lower() or 'strategic' in program_name.lower():
            personality_modifier += (personality.get('refined_conscientiousness', 0.5) - 0.5) * 0.1
            
        # Openness might influence creative/innovative programs
        if 'design' in program_name.lower() or 'innovation' in program_name.lower():
            personality_modifier += (personality.get('refined_openness', 0.5) - 0.5) * 0.1
            
        # Motivation modifiers (small adjustments)
        motivation_modifier = 0.0
        
        # Academic drive influences all programs slightly
        motivation_modifier += (motivation.get('motivation_academic_drive', 0.5) - 0.5) * 0.05
        
        # Career focus might influence practical programs
        if 'craft' in program_name.lower() or 'practice' in program_name.lower():
            motivation_modifier += (motivation.get('motivation_career_focus', 0.5) - 0.5) * 0.1
            
        # Values-based motivation might influence community programs
        if 'community' in program_name.lower() or 'mutual' in program_name.lower():
            motivation_modifier += (motivation.get('motivation_values_based_motivation', 0.5) - 0.5) * 0.1
            
        # Combine all factors
        final_probability = base_affinity + personality_modifier + motivation_modifier
        
        # Clamp to reasonable range
        return np.clip(final_probability, 0.01, 0.99)
        
    def select_program_for_student(self, clan: str, personality: Dict[str, float], 
                                 motivation: Dict[str, float]) -> Tuple[str, str, float]:
        """
        Select a program for a student based on their characteristics.
        Returns: (program_code, program_name, selection_probability)
        """
        # Get all available programs
        available_programs = self.programs_df[['Programme code', 'Programme']].drop_duplicates()
        
        # Calculate probabilities for each program
        program_probabilities = []
        for _, row in available_programs.iterrows():
            program_code = row['Programme code']
            program_name = row['Programme']
            
            prob = self.calculate_enrollment_probability(clan, program_name, personality, motivation)
            program_probabilities.append((program_code, program_name, prob))
            
        # Convert to numpy array for weighted choice
        programs = [(code, name) for code, name, _ in program_probabilities]
        probabilities = [prob for _, _, prob in program_probabilities]
        
        # Normalize probabilities
        probabilities = np.array(probabilities)
        probabilities = probabilities / probabilities.sum()
        
        # Select program
        selected_idx = np.random.choice(len(programs), p=probabilities)
        selected_code, selected_name = programs[selected_idx]
        selected_prob = program_probabilities[selected_idx][2]
        
        return selected_code, selected_name, selected_prob
        
    def get_year1_modules_for_program(self, program_code: str) -> List[str]:
        """Get list of Year 1 modules for a given program"""
        modules = self.year1_modules_df[self.year1_modules_df['Programme code'] == program_code]
        return modules['Module Title'].tolist()
        
    def enroll_student(self, student_id: str, clan: str, personality: Dict[str, float], 
                      motivation: Dict[str, float]) -> ProgramEnrollment:
        """
        Enroll a student in a program and assign Year 1 modules.
        """
        # Select program
        program_code, program_name, selection_prob = self.select_program_for_student(
            clan, personality, motivation
        )
        
        # Get program details
        program_info = self.programs_df[self.programs_df['Programme code'] == program_code].iloc[0]
        faculty = program_info['Faculty']
        department = program_info['Department']
        
        # Get Year 1 modules
        year1_modules = self.get_year1_modules_for_program(program_code)
        
        # Create enrollment factors for analysis
        enrollment_factors = {
            'clan_affinity': self.get_program_affinity(clan, program_name),
            'selection_probability': selection_prob,
            'personality_modifier': selection_prob - self.get_program_affinity(clan, program_name),
            'motivation_modifier': 0.0  # Could be calculated more precisely
        }
        
        return ProgramEnrollment(
            student_id=student_id,
            program_code=program_code,
            program_name=program_name,
            faculty=faculty,
            department=department,
            year_modules=year1_modules,
            enrollment_factors=enrollment_factors
        )
        
    def enroll_students_batch(self, students_df: pd.DataFrame) -> pd.DataFrame:
        """
        Enroll a batch of students in programs.
        Returns DataFrame with enrollment information added.
        """
        enrollments = []
        
        for idx, student in students_df.iterrows():
            # Extract personality and motivation data
            personality_cols = [col for col in students_df.columns if col.startswith('refined_')]
            motivation_cols = [col for col in students_df.columns if col.startswith('motivation_')]
            
            personality = {col: student[col] for col in personality_cols}
            motivation = {col: student[col] for col in motivation_cols}
            
            # Enroll student
            enrollment = self.enroll_student(
                student_id=str(idx),
                clan=student['clan'],
                personality=personality,
                motivation=motivation
            )
            
            enrollments.append({
                'student_id': enrollment.student_id,
                'program_code': enrollment.program_code,
                'program_name': enrollment.program_name,
                'faculty': enrollment.faculty,
                'department': enrollment.department,
                'year1_modules': _format_module_list_csv(enrollment.year_modules),
                'num_year1_modules': len(enrollment.year_modules),
                'clan_affinity': enrollment.enrollment_factors['clan_affinity'],
                'selection_probability': enrollment.enrollment_factors['selection_probability']
            })
            
        # Create enrollment DataFrame
        enrollment_df = pd.DataFrame(enrollments)
        
        # Merge with original student data
        result_df = students_df.reset_index(drop=True).copy()
        result_df = pd.concat([result_df, enrollment_df], axis=1)
        
        return result_df

def main():
    """Test the program enrollment system"""
    print("🎓 Stonegrove University Program Enrollment System")
    print("=" * 60)
    
    # Initialize system
    enrollment_system = ProgramEnrollmentSystem()
    
    # Load sample students
    students_df = pd.read_csv('data/stonegrove_individual_students.csv')
    print(f"\nLoaded {len(students_df)} students for enrollment")
    
    # Enroll students
    enrolled_df = enrollment_system.enroll_students_batch(students_df)
    
    # Analysis
    print(f"\n=== Enrollment Analysis ===")
    print(f"Total students enrolled: {len(enrolled_df)}")
    
    print(f"\n=== Program Distribution ===")
    program_counts = enrolled_df['program_name'].value_counts()
    print(program_counts.head(10))
    
    print(f"\n=== Faculty Distribution ===")
    faculty_counts = enrolled_df['faculty'].value_counts()
    print(faculty_counts)
    
    print(f"\n=== Clan-Program Affinity Analysis ===")
    affinity_stats = enrolled_df.groupby('clan')['clan_affinity'].agg(['mean', 'min', 'max']).round(3)
    print(affinity_stats)
    
    print(f"\n=== Selection Probability Analysis ===")
    prob_stats = enrolled_df['selection_probability'].describe()
    print(prob_stats)
    
    # Save enrolled students
    enrolled_df.to_csv('data/stonegrove_enrolled_students.csv', index=False)
    print(f"\n✅ Saved enrolled students to data/stonegrove_enrolled_students.csv")
    
    # Show sample enrollment
    print(f"\n=== Sample Enrollment ===")
    sample_cols = ['full_name', 'clan', 'program_name', 'faculty', 'num_year1_modules', 'clan_affinity']
    print(enrolled_df[sample_cols].head(10))

if __name__ == "__main__":
    main() 