import csv
import io
import pandas as pd
import numpy as np
import yaml
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


def _parse_module_list_csv(value: str) -> List[str]:
    """Parse module list from CSV-formatted string (handles commas in module names)."""
    if pd.isna(value) or not str(value).strip():
        return []
    reader = csv.reader(io.StringIO(str(value)))
    return [m.strip() for m in next(reader) if m.strip()]
from datetime import datetime, timedelta

@dataclass
class WeeklyEngagement:
    """Container for weekly engagement data"""
    student_id: str
    week_number: int
    program_code: str
    module_title: str
    attendance_rate: float  # 0.0 to 1.0
    participation_score: float  # 0.0 to 1.0
    academic_engagement: float  # 0.0 to 1.0
    social_engagement: float  # 0.0 to 1.0
    stress_level: float  # 0.0 to 1.0
    engagement_factors: Dict[str, float]

@dataclass
class SemesterEngagement:
    """Container for semester-level engagement summary"""
    student_id: str
    semester: int
    program_code: str
    average_attendance: float
    average_participation: float
    average_academic_engagement: float
    average_social_engagement: float
    average_stress_level: float
    engagement_trend: str  # 'improving', 'declining', 'stable'
    risk_factors: List[str]

class EngagementSystem:
    """
    System to model student engagement, attendance, and participation
    based on individual characteristics, program/module requirements, and weekly events.
    """
    
    def __init__(self):
        """Initialize the engagement system"""
        self._load_characteristics()
        
    def _load_characteristics(self):
        """Load module and program characteristics from CSV (preferred) or YAML."""
        from pathlib import Path
        mc_csv = Path('config/module_characteristics.csv')
        pc_csv = Path('config/programme_characteristics.csv')
        mc_yaml = Path('config/module_characteristics.yaml')
        pc_yaml = Path('config/program_characteristics.yaml')

        # Module characteristics
        self._module_chars = {}  # module_title -> {difficulty, social_requirements, creativity_requirements}
        if mc_csv.exists():
            df = pd.read_csv(mc_csv)
            for _, row in df.iterrows():
                title = str(row.get('module_title', '')).strip()
                if title:
                    self._module_chars[title] = {
                        'difficulty': float(row.get('difficulty_level', 0.5)),
                        'social_requirements': float(row.get('social_requirements', 0.5)),
                        'creativity_requirements': float(row.get('creativity_requirements', 0.5)),
                    }
        elif mc_yaml.exists():
            with open(mc_yaml, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            for title, info in (data.get('modules') or {}).items():
                if isinstance(info, dict):
                    self._module_chars[str(title).strip()] = {
                        'difficulty': float(info.get('difficulty_level', 0.5)),
                        'social_requirements': float(info.get('social_requirements', 0.5)),
                        'creativity_requirements': float(info.get('creativity_requirements', 0.5)),
                    }
        else:
            print("Warning: module_characteristics not found. Using estimation.")

        # Programme characteristics (keyed by programme_name)
        self._programme_chars = {}
        if pc_csv.exists():
            df = pd.read_csv(pc_csv)
            for _, row in df.iterrows():
                name = str(row.get('programme_name', '')).strip()
                if name:
                    self._programme_chars[name] = {
                        'social_intensity': float(row.get('social_intensity', 0.5)),
                        'practical_theoretical_balance': float(row.get('practical_theoretical_balance', 0.5)),
                        'stress_level': float(row.get('stress_level', 0.5)),
                        'career_prospects': float(row.get('career_prospects', 0.5)),
                    }
        elif pc_yaml.exists():
            with open(pc_yaml, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            for name, info in (data.get('programs') or {}).items():
                if isinstance(info, dict):
                    chars = info.get('characteristics', {})
                    self._programme_chars[str(name).strip()] = {
                        'social_intensity': float(chars.get('social_intensity', 0.5)),
                        'practical_theoretical_balance': float(chars.get('practical_theoretical_balance', 0.5)),
                        'stress_level': float(chars.get('stress_level', 0.5)),
                        'career_prospects': float(chars.get('career_prospects', 0.5)),
                    }
        else:
            print("Warning: programme_characteristics not found. Using defaults.")

    def get_module_characteristics(self, module_title: str) -> Dict[str, float]:
        """Get characteristics for a specific module (from config or estimated)."""
        title = str(module_title).strip()
        if title in self._module_chars:
            return self._module_chars[title].copy()
        return self._estimate_module_characteristics(module_title)
    
    def _estimate_module_characteristics(self, module_title: str) -> Dict[str, float]:
        """
        Estimate module characteristics based on title keywords.
        Feminist-aware: domestic, applied, craft, and care work are NOT treated as easy.
        """
        title_lower = module_title.lower()
        
        # Default: moderate difficulty (no automatic penalty for intro/foundation)
        difficulty = 0.5
        social_requirements = 0.5
        creativity_requirements = 0.5
        
        # Difficulty: only elevate for genuinely demanding markers; no penalty for intro/foundation
        if any(word in title_lower for word in ['advanced', 'capstone', 'research']):
            difficulty += 0.2
        elif any(word in title_lower for word in ['epistemolog', 'theoretical', 'complex']):
            difficulty += 0.15
        # Domestic/applied/craft/care: do NOT reduce - these require technical and embodied skill
        elif any(word in title_lower for word in [
            'embodied', 'somatic', 'fermentation', 'cultivation', 'harvest',
            'care', 'healing', 'hospitality', 'ritual', 'ethics', 'indigenous'
        ]):
            difficulty += 0.05  # Slight elevation: often demanding
        # Simple "introduction" without substantive content marker: neutral (stay 0.5)
        # No: difficulty -= 0.2 for introduction/basic/foundation
            
        # Social requirements
        if any(word in title_lower for word in ['group', 'team', 'collaboration', 'discussion', 'circle', 'listening']):
            social_requirements += 0.25
        elif any(word in title_lower for word in ['individual', 'independent', 'research']):
            social_requirements -= 0.15
            
        # Creativity requirements
        if any(word in title_lower for word in ['design', 'creative', 'innovation', 'art', 'craft', 'weaving']):
            creativity_requirements += 0.25
        elif any(word in title_lower for word in ['analysis', 'method', 'systematic', 'logic']):
            creativity_requirements -= 0.1
            
        return {
            'difficulty': np.clip(difficulty, 0.25, 0.9),
            'social_requirements': np.clip(social_requirements, 0.2, 0.9),
            'creativity_requirements': np.clip(creativity_requirements, 0.2, 0.9)
        }
    
    def get_programme_characteristics(self, programme_name: str) -> Dict[str, float]:
        """Get characteristics for a specific programme (by programme name)."""
        name = str(programme_name).strip()
        if name in self._programme_chars:
            return self._programme_chars[name].copy()
        return {
            'social_intensity': 0.5,
            'practical_theoretical_balance': 0.5,
            'stress_level': 0.5,
            'career_prospects': 0.5
        }
    
    def calculate_base_engagement(self, personality: Dict[str, float], 
                                motivation: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate base engagement levels based on personality and motivation.
        """
        # Base attendance (conscientiousness + academic drive)
        base_attendance = (
            personality.get('refined_conscientiousness', 0.5) * 0.4 +
            motivation.get('motivation_academic_drive', 0.5) * 0.3 +
            personality.get('refined_resilience', 0.5) * 0.2 +
            motivation.get('motivation_practical_skills', 0.5) * 0.1
        )
        
        # Base participation (extraversion + social connection motivation)
        base_participation = (
            personality.get('refined_extraversion', 0.5) * 0.4 +
            motivation.get('motivation_social_connection', 0.5) * 0.3 +
            personality.get('refined_leadership_tendency', 0.5) * 0.2 +
            personality.get('refined_social_anxiety', 0.5) * -0.1  # Negative impact
        )
        
        # Base academic engagement (academic curiosity + intellectual curiosity)
        base_academic_engagement = (
            personality.get('refined_academic_curiosity', 0.5) * 0.4 +
            motivation.get('motivation_intellectual_curiosity', 0.5) * 0.3 +
            personality.get('refined_openness', 0.5) * 0.2 +
            motivation.get('motivation_academic_drive', 0.5) * 0.1
        )
        
        # Base social engagement (extraversion + social connection)
        base_social_engagement = (
            personality.get('refined_extraversion', 0.5) * 0.5 +
            motivation.get('motivation_social_connection', 0.5) * 0.3 +
            personality.get('refined_leadership_tendency', 0.5) * 0.2
        )
        
        # Base stress level (neuroticism + various factors)
        base_stress = (
            personality.get('refined_neuroticism', 0.5) * 0.4 +
            personality.get('refined_social_anxiety', 0.5) * 0.3 +
            (1 - personality.get('refined_resilience', 0.5)) * 0.2 +
            (1 - motivation.get('motivation_personal_growth', 0.5)) * 0.1
        )
        
        return {
            'base_attendance': np.clip(base_attendance, 0.1, 0.95),
            'base_participation': np.clip(base_participation, 0.1, 0.95),
            'base_academic_engagement': np.clip(base_academic_engagement, 0.1, 0.95),
            'base_social_engagement': np.clip(base_social_engagement, 0.1, 0.95),
            'base_stress': np.clip(base_stress, 0.05, 0.9)
        }
    
    def apply_module_modifiers(self, base_engagement: Dict[str, float], 
                             module_characteristics: Dict[str, float],
                             personality: Dict[str, float]) -> Dict[str, float]:
        """
        Apply module-specific modifiers to base engagement.
        """
        modified = base_engagement.copy()
        
        # Module difficulty affects attendance and academic engagement
        difficulty = module_characteristics['difficulty']
        difficulty_modifier = (difficulty - 0.5) * 0.2  # ±10% effect
        
        # High difficulty can reduce attendance for some students, increase for others
        if personality.get('refined_conscientiousness', 0.5) > 0.7:
            # Conscientious students work harder with difficult modules
            modified['base_attendance'] += difficulty_modifier * 0.5
            modified['base_academic_engagement'] += difficulty_modifier
        else:
            # Less conscientious students may struggle
            modified['base_attendance'] -= difficulty_modifier * 0.3
            modified['base_academic_engagement'] -= difficulty_modifier * 0.5
        
        # Social requirements affect participation and social engagement
        social_req = module_characteristics['social_requirements']
        social_modifier = (social_req - 0.5) * 0.3  # ±15% effect
        
        if personality.get('refined_extraversion', 0.5) > 0.6:
            # Extraverted students thrive in social modules
            modified['base_participation'] += social_modifier
            modified['base_social_engagement'] += social_modifier
        else:
            # Introverted students may struggle
            modified['base_participation'] -= social_modifier * 0.5
            modified['base_social_engagement'] -= social_modifier * 0.3
            modified['base_stress'] += social_modifier * 0.2
        
        # Creativity requirements affect academic engagement
        creativity_req = module_characteristics['creativity_requirements']
        creativity_modifier = (creativity_req - 0.5) * 0.2  # ±10% effect
        
        if personality.get('refined_openness', 0.5) > 0.6:
            # Open students enjoy creative modules
            modified['base_academic_engagement'] += creativity_modifier
        else:
            # Less open students may struggle
            modified['base_academic_engagement'] -= creativity_modifier * 0.5
        
        # Clamp all values
        for key in modified:
            if key != 'base_stress':
                modified[key] = np.clip(modified[key], 0.05, 0.95)
            else:
                modified[key] = np.clip(modified[key], 0.05, 0.9)
        
        return modified
    
    def generate_weekly_variation(self, base_engagement: Dict[str, float]) -> Dict[str, float]:
        """
        Generate weekly variation in engagement levels.
        """
        weekly_engagement = {}
        
        for key, base_value in base_engagement.items():
            # Add random variation (±15% of base value)
            variation = np.random.normal(0, 0.15 * base_value)
            weekly_engagement[key.replace('base_', '')] = np.clip(base_value + variation, 0.05, 0.95)
        
        return weekly_engagement
    
    def generate_weekly_engagement(self, student_id: str, week_number: int,
                                 program_code: str, programme_name: str, module_title: str,
                                 personality: Dict[str, float], 
                                 motivation: Dict[str, float]) -> WeeklyEngagement:
        """
        Generate weekly engagement data for a student.
        """
        # Get module and programme characteristics
        module_chars = self.get_module_characteristics(module_title)
        program_chars = self.get_programme_characteristics(programme_name)
        
        # Calculate base engagement
        base_engagement = self.calculate_base_engagement(personality, motivation)
        
        # Apply module modifiers
        modified_engagement = self.apply_module_modifiers(base_engagement, module_chars, personality)
        
        # Generate weekly variation
        weekly_engagement = self.generate_weekly_variation(modified_engagement)
        
        # Create engagement factors for analysis
        engagement_factors = {
            'module_difficulty': module_chars['difficulty'],
            'module_social_requirements': module_chars['social_requirements'],
            'module_creativity_requirements': module_chars['creativity_requirements'],
            'personality_conscientiousness': personality.get('refined_conscientiousness', 0.5),
            'personality_extraversion': personality.get('refined_extraversion', 0.5),
            'motivation_academic_drive': motivation.get('motivation_academic_drive', 0.5),
            'motivation_social_connection': motivation.get('motivation_social_connection', 0.5)
        }
        
        return WeeklyEngagement(
            student_id=student_id,
            week_number=week_number,
            program_code=program_code,
            module_title=module_title,
            attendance_rate=weekly_engagement['attendance'],
            participation_score=weekly_engagement['participation'],
            academic_engagement=weekly_engagement['academic_engagement'],
            social_engagement=weekly_engagement['social_engagement'],
            stress_level=weekly_engagement['stress'],
            engagement_factors=engagement_factors
        )
    
    def generate_semester_engagement(self, student_id: str, semester: int,
                                   weekly_engagements: List[WeeklyEngagement]) -> SemesterEngagement:
        """
        Generate semester-level engagement summary from weekly data.
        """
        if not weekly_engagements:
            return None
            
        # Calculate averages
        avg_attendance = np.mean([w.attendance_rate for w in weekly_engagements])
        avg_participation = np.mean([w.participation_score for w in weekly_engagements])
        avg_academic = np.mean([w.academic_engagement for w in weekly_engagements])
        avg_social = np.mean([w.social_engagement for w in weekly_engagements])
        avg_stress = np.mean([w.stress_level for w in weekly_engagements])
        
        # Determine trend (comparing first half vs second half)
        mid_point = len(weekly_engagements) // 2
        first_half_attendance = np.mean([w.attendance_rate for w in weekly_engagements[:mid_point]])
        second_half_attendance = np.mean([w.attendance_rate for w in weekly_engagements[mid_point:]])
        
        if second_half_attendance > first_half_attendance + 0.05:
            trend = 'improving'
        elif second_half_attendance < first_half_attendance - 0.05:
            trend = 'declining'
        else:
            trend = 'stable'
        
        # Identify risk factors
        risk_factors = []
        if avg_attendance < 0.7:
            risk_factors.append('low_attendance')
        if avg_participation < 0.5:
            risk_factors.append('low_participation')
        if avg_stress > 0.7:
            risk_factors.append('high_stress')
        if avg_academic < 0.5:
            risk_factors.append('low_academic_engagement')
        
        return SemesterEngagement(
            student_id=student_id,
            semester=semester,
            program_code=weekly_engagements[0].program_code,
            average_attendance=avg_attendance,
            average_participation=avg_participation,
            average_academic_engagement=avg_academic,
            average_social_engagement=avg_social,
            average_stress_level=avg_stress,
            engagement_trend=trend,
            risk_factors=risk_factors
        )
    
    def generate_engagement_data(
        self,
        enrolled_students_df: pd.DataFrame,
        weeks_per_semester: int = 12,
        academic_year: str = "",
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Generate engagement data for all enrolled students.
        Returns: (weekly_engagement_df, semester_engagement_df)
        """
        weekly_data = []
        semester_data = []
        
        for idx, student in enrolled_students_df.iterrows():
            sid_raw = student.get("student_id", idx)
            student_id = str(sid_raw.iloc[0]) if isinstance(sid_raw, pd.Series) else str(sid_raw)
            
            # Extract personality and motivation data
            personality_cols = [col for col in enrolled_students_df.columns if col.startswith('refined_')]
            motivation_cols = [col for col in enrolled_students_df.columns if col.startswith('motivation_')]
            
            personality = {col: student[col] for col in personality_cols}
            motivation = {col: student[col] for col in motivation_cols}
            
            # Get student's modules for their programme_year (1, 2, or 3)
            prog_year = int(student.get('programme_year', 1))
            mod_col = f'year{prog_year}_modules'
            modules = _parse_module_list_csv(student.get(mod_col, student.get('year1_modules', '')))
            program_code = student['program_code']
            programme_name = student.get('program_name', '')
            
            # Generate weekly engagement for each module
            weekly_engagements = []
            for week in range(1, weeks_per_semester + 1):
                for module in modules:
                    module = module.strip()
                    if module:  # Skip empty modules
                        weekly_engagement = self.generate_weekly_engagement(
                            student_id, week, program_code, programme_name, module, personality, motivation
                        )
                        weekly_engagements.append(weekly_engagement)
                        
                        # Add to weekly data
                        rec = {
                            'student_id': weekly_engagement.student_id,
                            'week_number': weekly_engagement.week_number,
                            'program_code': weekly_engagement.program_code,
                            'module_title': weekly_engagement.module_title,
                            'attendance_rate': weekly_engagement.attendance_rate,
                            'participation_score': weekly_engagement.participation_score,
                            'academic_engagement': weekly_engagement.academic_engagement,
                            'social_engagement': weekly_engagement.social_engagement,
                            'stress_level': weekly_engagement.stress_level,
                            **weekly_engagement.engagement_factors
                        }
                        ay = academic_year or student.get('academic_year', '')
                        if ay:
                            rec['academic_year'] = ay
                        weekly_data.append(rec)
            
            # Generate semester summary
            if weekly_engagements:
                semester_engagement = self.generate_semester_engagement(
                    student_id, 1, weekly_engagements
                )
                if semester_engagement:
                    semester_data.append({
                        'student_id': semester_engagement.student_id,
                        'semester': semester_engagement.semester,
                        'program_code': semester_engagement.program_code,
                        'average_attendance': semester_engagement.average_attendance,
                        'average_participation': semester_engagement.average_participation,
                        'average_academic_engagement': semester_engagement.average_academic_engagement,
                        'average_social_engagement': semester_engagement.average_social_engagement,
                        'average_stress_level': semester_engagement.average_stress_level,
                        'engagement_trend': semester_engagement.engagement_trend,
                        'risk_factors': ','.join(semester_engagement.risk_factors) if semester_engagement.risk_factors else 'none'
                    })
        
        return pd.DataFrame(weekly_data), pd.DataFrame(semester_data)

def main():
    """Test the engagement system"""
    print("Stonegrove University Engagement System")
    print("=" * 60)
    
    # Initialize system
    engagement_system = EngagementSystem()
    
    # Load enrolled students
    enrolled_df = pd.read_csv('data/stonegrove_enrolled_students.csv')
    print(f"Loaded {len(enrolled_df)} enrolled students")
    
    # Generate engagement data
    weekly_df, semester_df = engagement_system.generate_engagement_data(enrolled_df, weeks_per_semester=12)
    
    # Analysis
    print(f"\n=== Engagement Data Generated ===")
    print(f"Weekly engagement records: {len(weekly_df)}")
    print(f"Semester engagement records: {len(semester_df)}")
    
    print(f"\n=== Weekly Engagement Statistics ===")
    weekly_stats = weekly_df[['attendance_rate', 'participation_score', 'academic_engagement', 
                             'social_engagement', 'stress_level']].describe()
    print(weekly_stats.round(3))
    
    print(f"\n=== Semester Engagement Statistics ===")
    semester_stats = semester_df[['average_attendance', 'average_participation', 
                                 'average_academic_engagement', 'average_social_engagement', 
                                 'average_stress_level']].describe()
    print(semester_stats.round(3))
    
    print(f"\n=== Engagement Trends ===")
    trend_counts = semester_df['engagement_trend'].value_counts()
    print(trend_counts)
    
    print(f"\n=== Risk Factors ===")
    risk_counts = semester_df['risk_factors'].value_counts()
    print(risk_counts.head(10))
    
    # Save data
    weekly_df.to_csv('data/stonegrove_weekly_engagement.csv', index=False)
    semester_df.to_csv('data/stonegrove_semester_engagement.csv', index=False)
    print(f"\nSaved engagement data:")
    print(f"   - Weekly: data/stonegrove_weekly_engagement.csv")
    print(f"   - Semester: data/stonegrove_semester_engagement.csv")
    
    # Show sample data
    print(f"\n=== Sample Weekly Engagement ===")
    sample_cols = ['student_id', 'week_number', 'module_title', 'attendance_rate', 
                   'participation_score', 'academic_engagement', 'stress_level']
    print(weekly_df[sample_cols].head(10))

if __name__ == "__main__":
    main() 