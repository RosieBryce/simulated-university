"""
Stonegrove University Assessment System

Generates end-of-module marks for enrolled students.
Output: stonegrove_assessment_events.csv with module_code, component_code.
Marks are modified by engagement (attendance, participation, academic_engagement).
Uses module_characteristics (CSV or YAML) for assessment_type and difficulty where available.
"""

import csv
import io
import pandas as pd
import numpy as np
import yaml
from typing import Dict, List, Optional
from pathlib import Path


def _parse_module_list_csv(value: str) -> List[str]:
    """Parse module list from CSV-formatted string (handles commas in module names)."""
    if pd.isna(value) or not str(value).strip():
        return []
    reader = csv.reader(io.StringIO(str(value)))
    return [m.strip() for m in next(reader) if m.strip()]


def _difficulty_to_mark_modifier(difficulty: float) -> float:
    """Convert difficulty (0.25-0.9) to mark modifier (0.85-1.05). Higher difficulty = slightly lower marks."""
    if difficulty <= 0.5:
        return 1.0 + (0.5 - difficulty) * 0.1  # 0.5->1.0, 0.3->1.02
    return 1.0 - (difficulty - 0.5) * 0.25  # 0.7->0.95, 0.9->0.9


def _get_module_difficulty_modifier_fallback(module_title: str) -> float:
    """Fallback: infer from module title when not in config. Feminist-aware."""
    title_lower = module_title.lower()
    if any(w in title_lower for w in ['advanced', 'capstone', 'research']):
        return 0.9
    if any(w in title_lower for w in ['epistemolog', 'theoretical', 'complex']):
        return 0.95
    return 1.0


def _get_assessment_type_fallback(module_title: str) -> str:
    """Fallback: infer assessment type from module title when not in config."""
    title_lower = module_title.lower()
    if any(w in title_lower for w in ['practical', 'hands', 'craft', 'practice']):
        return 'practical'
    if any(w in title_lower for w in ['project', 'design', 'praxis']):
        return 'project'
    if any(w in title_lower for w in ['essay', 'theory', 'critical']):
        return 'essay'
    return 'mixed'


def _grade_from_mark(mark: float) -> str:
    """UK grading: First (>=70), 2:1 (>=60), 2:2 (>=50), Third (>=40), Fail (<40)."""
    if mark >= 70:
        return "First"
    if mark >= 60:
        return "2:1"
    if mark >= 50:
        return "2:2"
    if mark >= 40:
        return "Third"
    return "Fail"


class AssessmentSystem:
    """
    Generates assessment marks for enrolled students.
    One row per student per module per assessment.
    Uses module_characteristics (CSV or YAML) for assessment_type and difficulty.
    """

    def __init__(self, seed: int = 42, curriculum_file: str = "Instructions and guides/Stonegrove_University_Curriculum.xlsx"):
        self.seed = seed
        np.random.seed(seed)
        self.curriculum_file = curriculum_file
        self.modules_df = None
        self.module_chars = {}  # module_title -> {assessment_type, difficulty_level}
        self._load_curriculum()
        self._load_module_characteristics()

    def _load_curriculum(self):
        """Load Modules sheet for programme-module mapping."""
        self.modules_df = pd.read_excel(self.curriculum_file, sheet_name='Modules')
        self.year1_modules = self.modules_df[self.modules_df['Year'] == 1].copy()

    def _load_module_characteristics(self):
        """Load module characteristics from CSV (preferred) or YAML. Used for assessment_type and difficulty."""
        csv_path = Path('config/module_characteristics.csv')
        yaml_path = Path('config/module_characteristics.yaml')
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            for _, row in df.iterrows():
                title = str(row.get('module_title', '')).strip()
                if title:
                    self.module_chars[title] = {
                        'assessment_type': str(row.get('assessment_type', 'mixed')).strip() or 'mixed',
                        'difficulty_level': float(row.get('difficulty_level', 0.5)),
                    }
        elif yaml_path.exists():
            with open(yaml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            for title, info in (data.get('modules') or {}).items():
                if isinstance(info, dict):
                    self.module_chars[str(title).strip()] = {
                        'assessment_type': str(info.get('assessment_type', 'mixed')).strip() or 'mixed',
                        'difficulty_level': float(info.get('difficulty_level', 0.5)),
                    }
        # else: module_chars stays empty, fallbacks used

    def _get_assessment_type(self, module_title: str) -> str:
        """Get assessment_type from module_characteristics, else infer from title."""
        title = str(module_title).strip()
        if title in self.module_chars:
            return self.module_chars[title]['assessment_type']
        return _get_assessment_type_fallback(module_title)

    def _get_difficulty_modifier(self, module_title: str) -> float:
        """Get mark modifier from module_characteristics difficulty, else infer from title."""
        title = str(module_title).strip()
        if title in self.module_chars:
            return _difficulty_to_mark_modifier(self.module_chars[title]['difficulty_level'])
        return _get_module_difficulty_modifier_fallback(module_title)

    def _get_disability_modifier(self, disabilities: str) -> float:
        """Product of modifiers for each disability (CALCULATIONS.md)."""
        if pd.isna(disabilities) or not str(disabilities).strip():
            return 1.0
        raw = str(disabilities).lower()
        if 'no_known_disabilities' in raw:
            return 1.0
        modifiers = {
            'specific_learning_disability': 0.8,
            'requires_personal_care': 0.75,
            'blind_or_visually_impaired': 0.8,
            'communication_difficulties': 0.8,
            'physical_disability': 1.05,
            'mental_health_disability': 1.05,
            'autistic_spectrum': 1.1,
            'adhd': 1.05,
            'dyslexia': 1.05,
            'other_neurodivergence': 1.1,
            'deaf_or_hearing_impaired': 1.05,
            'wheelchair_user': 1.05,
        }
        prod = 1.0
        for k, v in modifiers.items():
            if k in raw:
                prod *= v
        return prod

    def _get_clan_modifier(self, clan: str) -> float:
        """Clan modifier (Baobab 1.15, Alabaster 0.85, else 1.0)."""
        if clan == 'baobab':
            return 1.15
        if clan == 'alabaster':
            return 0.85
        return 1.0

    def _get_education_modifier(self, education: str) -> float:
        """Education modifier: academic 1.05, vocational 0.98, else 1.0."""
        if pd.isna(education):
            return 1.0
        e = str(education).lower()
        if 'academic' in e:
            return 1.05
        if 'vocational' in e:
            return 0.98
        return 1.0

    def _get_socio_economic_modifier(self, rank: int) -> float:
        """Socio-economic rank modifier (CALCULATIONS.md)."""
        mapping = {1: 0.9, 2: 0.95, 3: 1.0, 4: 1.05, 5: 1.1}
        r = int(rank) if not pd.isna(rank) else 3
        return mapping.get(r, 1.0)

    def _engagement_to_modifier(self, avg_engagement: float) -> float:
        """Convert engagement score (0-1) to mark modifier. High engagement slightly boosts marks."""
        if avg_engagement is None or np.isnan(avg_engagement):
            return 1.0
        # 0.5 engagement -> 1.0 modifier; 0.2 -> 0.94; 0.8 -> 1.06
        return float(np.clip(0.88 + 0.24 * avg_engagement, 0.88, 1.12))

    def generate_mark(self, student: pd.Series, module_title: str,
                     engagement_modifier: Optional[float] = None) -> float:
        """
        Generate a single module mark for a student.
        Base distribution 70% (60,8), 15% (75,6), 15% (45,10).
        Modifiers: species, clan, disability, education, socio-economic, module difficulty, engagement.
        """
        # Base distribution
        r = np.random.random()
        if r < 0.7:
            base = np.random.normal(60, 8)
        elif r < 0.85:
            base = np.random.normal(75, 6)
        else:
            base = np.random.normal(45, 10)

        # Modifiers
        mod = 1.0
        mod *= 1.1 if str(student.get('species', '')).lower() == 'elf' else 0.95
        mod *= self._get_clan_modifier(str(student.get('clan', '')).lower())
        mod *= self._get_disability_modifier(student.get('disabilities', ''))
        mod *= self._get_education_modifier(student.get('education', ''))
        mod *= self._get_socio_economic_modifier(student.get('socio_economic_rank', 3))
        mod *= self._get_difficulty_modifier(module_title)
        if engagement_modifier is not None:
            mod *= engagement_modifier

        mark = base * mod + np.random.normal(0, 5)
        return float(np.clip(round(mark, 1), 0.0, 100.0))

    def _load_engagement_by_student_module(
        self,
        engagement_path: str = "data/stonegrove_weekly_engagement.csv",
        academic_year: Optional[str] = None,
    ) -> Dict[tuple, float]:
        """
        Load weekly engagement and return (student_id, module_title) -> avg_engagement.
        If academic_year given and column exists, filter to that year.
        """
        path = Path(engagement_path)
        if not path.exists():
            return {}
        df = pd.read_csv(path)
        if df.empty or 'student_id' not in df.columns or 'module_title' not in df.columns:
            return {}
        if academic_year and 'academic_year' in df.columns:
            df = df[df['academic_year'] == academic_year]
        cols = [c for c in ['attendance_rate', 'participation_score', 'academic_engagement'] if c in df.columns]
        if not cols:
            return {}
        df['engagement'] = df[cols].mean(axis=1)
        df['student_id'] = df['student_id'].astype(str)
        df['module_title'] = df['module_title'].str.strip()
        agg = df.groupby(['student_id', 'module_title'])['engagement'].mean()
        return {k: float(v) for k, v in agg.items()}

    def generate_assessment_data(
        self,
        enrolled_df: pd.DataFrame,
        academic_year: str = "1046-47",
        assessment_date: str = "1046-12-15",
        weekly_engagement_path: str = "data/stonegrove_weekly_engagement.csv",
    ) -> pd.DataFrame:
        """
        Generate assessment events for all enrolled students.
        Reads year1_modules from each student, one assessment per module.
        Uses weekly engagement (if available) as a modifier to marks.
        """
        engagement_lookup = self._load_engagement_by_student_module(
            weekly_engagement_path, academic_year=academic_year
        )
        records = []
        for idx, student in enrolled_df.iterrows():
            sid_raw = student.get('student_id', idx)
            student_id = str(sid_raw.iloc[0]) if isinstance(sid_raw, pd.Series) else str(sid_raw)
            program_code = student['program_code']
            prog_year = int(student.get('programme_year', 1))
            mod_col = f'year{prog_year}_modules'
            modules = _parse_module_list_csv(student.get(mod_col, student.get('year1_modules', '')))

            for i, module_title in enumerate(modules):
                if not module_title.strip():
                    continue
                module_code = f"{program_code}.{i+1:02d}"
                component_code = "MAIN"

                key = (student_id, module_title.strip())
                avg_eng = engagement_lookup.get(key)
                eng_mod = self._engagement_to_modifier(avg_eng) if avg_eng is not None else None

                mark = self.generate_mark(student, module_title, engagement_modifier=eng_mod)
                grade = _grade_from_mark(mark)

                records.append({
                    'student_id': student_id,
                    'academic_year': academic_year,
                    'programme_code': program_code,
                    'module_code': module_code,
                    'component_code': component_code,
                    'module_title': module_title.strip(),
                    'assessment_type': self._get_assessment_type(module_title),
                    'assessment_mark': mark,
                    'grade': grade,
                    'assessment_date': assessment_date,
                    'module_year': prog_year,
                })

        return pd.DataFrame(records)


def main():
    print("Stonegrove University Assessment System")
    print("=" * 50)

    system = AssessmentSystem()
    enrolled_df = pd.read_csv('data/stonegrove_enrolled_students.csv')
    print(f"Loaded {len(enrolled_df)} enrolled students")

    df = system.generate_assessment_data(enrolled_df)

    print(f"\nGenerated {len(df)} assessment events")
    print(f"\nGrade distribution:")
    print(df['grade'].value_counts())
    print(f"\nMark statistics:")
    print(df['assessment_mark'].describe().round(2))

    out_path = Path('data/stonegrove_assessment_events.csv')
    df.to_csv(out_path, index=False)
    print(f"\nSaved to {out_path}")

    print(f"\nSample:")
    print(df[['student_id', 'module_title', 'assessment_mark', 'grade']].head(10))


if __name__ == "__main__":
    main()
