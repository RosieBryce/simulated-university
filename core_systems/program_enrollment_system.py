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
        self._load_programme_characteristics()
        self._load_trait_mapping()
        
    def _load_curriculum_data(self):
        """Load program and module data from curriculum Excel file"""
        # Load programs
        self.programs_df = pd.read_excel(self.curriculum_file, sheet_name='Programmes')
        
        # Load modules
        self.modules_df = pd.read_excel(self.curriculum_file, sheet_name='Modules')
        
        self.year1_modules_df = self.modules_df[self.modules_df['Year'] == 1].copy()
        self.year2_modules_df = self.modules_df[self.modules_df['Year'] == 2].copy()
        self.year3_modules_df = self.modules_df[self.modules_df['Year'] == 3].copy()

        print(f"Loaded {len(self.programs_df)} programs across {self.programs_df['Faculty'].nunique()} faculties")
        print(f"Loaded {len(self.year1_modules_df)} Year 1, {len(self.year2_modules_df)} Year 2, {len(self.year3_modules_df)} Year 3 modules")
        
    def _load_clan_affinities(self):
        """Load clan program affinities and selection settings from YAML"""
        with open('config/clan_program_affinities.yaml', 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            self.clan_affinities = data['clans']
            self.affinity_settings = data['settings']
        selection_rules = self.affinity_settings.get('selection_rules', {})
        self.base_selection_probability = selection_rules.get('base_selection_probability', 0.3)
        self.affinity_multipliers = selection_rules.get('affinity_multipliers', {})
        self.min_affinity_threshold = selection_rules.get('minimum_affinity_threshold', 0.05)
        self.affinity_levels = self.affinity_settings.get('affinity_levels', {})

    def _load_programme_characteristics(self):
        """Load programme characteristics from CSV"""
        self.programme_chars_df = pd.read_csv('config/programme_characteristics.csv')
        self._programme_chars_lookup = {}
        for _, row in self.programme_chars_df.iterrows():
            self._programme_chars_lookup[row['programme_name']] = row.to_dict()

    def _load_trait_mapping(self):
        """Load trait-to-programme-characteristic mapping from CSV"""
        self.trait_mapping_df = pd.read_csv('config/trait_programme_mapping.csv')

    def _classify_affinity(self, score: float) -> str:
        """Classify an affinity score into a level using config ranges."""
        for level, (min_score, max_score) in self.affinity_levels.items():
            if min_score <= score <= max_score:
                return level
        return "minimal"

    def _get_programme_characteristics(self, program_name: str) -> Optional[Dict]:
        """Look up programme characteristics by name."""
        return self._programme_chars_lookup.get(program_name)

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
        Calculate enrollment probability based on:
        - Clan affinity (primary) — scored using affinity_levels and multipliers from config
        - Trait-programme fit (secondary) — driven by trait_programme_mapping.csv and
          programme_characteristics.csv, no hardcoded programme names or keywords
        """
        # --- Clan component (config-driven) ---
        raw_affinity = self.get_program_affinity(clan, program_name)
        if raw_affinity < self.min_affinity_threshold:
            return 0.0
        affinity_level = self._classify_affinity(raw_affinity)
        multiplier = self.affinity_multipliers.get(affinity_level, 1.0)
        clan_score = 0.05 + self.base_selection_probability * multiplier * raw_affinity

        # --- Trait fit component (data-driven) ---
        programme_chars = self._get_programme_characteristics(program_name)
        if programme_chars is None:
            return clan_score

        student_traits = {**personality, **motivation}
        fit_score = 0.0
        for _, mapping_row in self.trait_mapping_df.iterrows():
            char_name = mapping_row['programme_characteristic']
            trait_name = mapping_row['student_trait']
            weight = mapping_row['weight']
            char_value = programme_chars.get(char_name, 0.5)
            trait_value = student_traits.get(trait_name, 0.5)
            fit_score += weight * char_value * (trait_value - 0.5)

        # Combine: clan affinity is primary, trait fit is meaningful secondary
        combined = clan_score * (1.0 + fit_score)
        return max(combined, 0.001)
        
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
        
    def get_modules_for_programme_year(self, program_code: str, programme_year: int) -> List[str]:
        """Get modules for a given program and programme year (1, 2, or 3)."""
        year_df = {
            1: self.year1_modules_df,
            2: self.year2_modules_df,
            3: self.year3_modules_df,
        }.get(programme_year, self.year1_modules_df)
        modules = year_df[year_df['Programme code'] == program_code]
        return modules['Module Title'].tolist()

    def get_year1_modules_for_program(self, program_code: str) -> List[str]:
        """Get list of Year 1 modules for a given program"""
        return self.get_modules_for_programme_year(program_code, 1)
        
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
        
    def enroll_students_batch(
        self,
        students_df: pd.DataFrame,
        academic_year: str = "",
        status_change_at: str = "",
    ) -> pd.DataFrame:
        """
        Enroll a batch of students in programs.
        Returns DataFrame with enrollment information added.
        """
        enrollments = []
        
        for idx, student in students_df.iterrows():
            # Use student_id from input (pipeline assigns before calling)
            sid_raw = student.get("student_id", idx)
            sid = str(sid_raw.iloc[0]) if isinstance(sid_raw, pd.Series) else str(sid_raw)
            # Extract personality and motivation data
            personality_cols = [col for col in students_df.columns if col.startswith('refined_')]
            motivation_cols = [col for col in students_df.columns if col.startswith('motivation_')]
            
            personality = {col: student[col] for col in personality_cols}
            motivation = {col: student[col] for col in motivation_cols}
            
            # Enroll student
            enrollment = self.enroll_student(
                student_id=sid,
                clan=student['clan'],
                personality=personality,
                motivation=motivation
            )
            
            y1 = enrollment.year_modules
            y2 = self.get_modules_for_programme_year(enrollment.program_code, 2)
            y3 = self.get_modules_for_programme_year(enrollment.program_code, 3)
            enrollments.append({
                'student_id': enrollment.student_id,
                'program_code': enrollment.program_code,
                'program_name': enrollment.program_name,
                'faculty': enrollment.faculty,
                'department': enrollment.department,
                'programme_year': 1,
                'status': 'enrolled',
                'year1_modules': _format_module_list_csv(y1),
                'year2_modules': _format_module_list_csv(y2),
                'year3_modules': _format_module_list_csv(y3),
                'num_year1_modules': len(y1),
                'num_year2_modules': len(y2),
                'num_year3_modules': len(y3),
                'clan_affinity': enrollment.enrollment_factors['clan_affinity'],
                'selection_probability': enrollment.enrollment_factors['selection_probability']
            })
            
        # Create enrollment DataFrame
        enrollment_df = pd.DataFrame(enrollments)
        # Align dtypes for merge (students_df may have int, enrollment_df has str)
        students_df = students_df.copy()
        students_df["student_id"] = students_df["student_id"].astype(str)
        enrollment_df["student_id"] = enrollment_df["student_id"].astype(str)
        result_df = students_df.merge(enrollment_df, on="student_id", how="left")
        if academic_year:
            result_df["academic_year"] = academic_year
        if status_change_at:
            result_df["status_change_at"] = status_change_at

        return result_df

    def enroll_continuing_students(
        self,
        students_df: pd.DataFrame,
        programme_year: Optional[int] = None,
        status: Optional[str] = None,
        academic_year: str = "",
        status_change_at: str = "",
    ) -> pd.DataFrame:
        """
        Add enrollment records for continuing students (progressing/repeating).
        Students must already have program_code, program_name, faculty, department.
        If programme_year/status columns exist, use per-row; else use scalar args.
        """
        records = []
        for idx, row in students_df.iterrows():
            sid_raw = row.get("student_id", idx)
            sid = str(sid_raw.iloc[0]) if isinstance(sid_raw, pd.Series) else str(sid_raw)
            pc = row["program_code"]
            pn = row["program_name"]
            faculty = row["faculty"]
            dept = row["department"]
            py = int(row.get("programme_year", programme_year or 1))
            st = str(row.get("status", status or "enrolled"))
            y1 = self.get_modules_for_programme_year(pc, 1)
            y2 = self.get_modules_for_programme_year(pc, 2)
            y3 = self.get_modules_for_programme_year(pc, 3)
            records.append({
                "student_id": sid,
                "program_code": pc,
                "program_name": pn,
                "faculty": faculty,
                "department": dept,
                "programme_year": py,
                "status": st,
                "year1_modules": _format_module_list_csv(y1),
                "year2_modules": _format_module_list_csv(y2),
                "year3_modules": _format_module_list_csv(y3),
                "num_year1_modules": len(y1),
                "num_year2_modules": len(y2),
                "num_year3_modules": len(y3),
                "clan_affinity": row.get("clan_affinity", 0.5),
                "selection_probability": row.get("selection_probability", 0.5),
            })
        enroll_df = pd.DataFrame(records)
        result = students_df.copy()
        # Drop enrollment cols if present, then merge
        drop_cols = [c for c in result.columns if c in enroll_df.columns and c != "student_id"]
        result = result.drop(columns=drop_cols, errors="ignore")
        result = result.merge(enroll_df, on="student_id", how="left")
        if academic_year:
            result["academic_year"] = academic_year
        if status_change_at:
            result["status_change_at"] = status_change_at
        return result

def main():
    """Test the program enrollment system"""
    print("Stonegrove University Program Enrollment System")
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
    print(f"\nSaved enrolled students to data/stonegrove_enrolled_students.csv")
    
    # Show sample enrollment
    print(f"\n=== Sample Enrollment ===")
    sample_cols = ['full_name', 'clan', 'program_name', 'faculty', 'num_year1_modules', 'clan_affinity']
    print(enrolled_df[sample_cols].head(10))

if __name__ == "__main__":
    main() 