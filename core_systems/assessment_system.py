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
    """Convert difficulty (0.25-0.9) to mark modifier. Higher difficulty = lower marks.
    Slope tuned to create a clear negative difficulty–mark correlation (~-0.10 to -0.20).
    Range: ~1.03 (diff=0.29) down to ~0.86 (diff=0.88)."""
    if difficulty <= 0.5:
        return 1.0 + (0.5 - difficulty) * 0.15  # 0.5->1.0, 0.3->1.03
    return 1.0 - (difficulty - 0.5) * 0.37       # 0.7->0.926, 0.9->0.852


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
        self.rng = np.random.default_rng(seed)
        self.curriculum_file = curriculum_file
        self.modules_df = None
        self.module_chars = {}  # module_title -> {assessment_type, difficulty_level}
        self._load_curriculum()
        self._load_module_characteristics()
        self._load_disability_modifiers()
        self._load_assessment_modifiers()

    def _load_curriculum(self):
        """Load Modules sheet and build (programme_code, module_title) -> module_code lookup."""
        self.modules_df = pd.read_excel(self.curriculum_file, sheet_name='Modules')
        self.module_code_lookup = {
            (str(row['Programme code']).strip(), str(row['Module Title']).strip()): str(row['Module Code']).strip()
            for _, row in self.modules_df.iterrows()
        }

    def _load_module_characteristics(self):
        """Load module characteristics from CSV (preferred) or YAML. Used for assessment_type and difficulty."""
        csv_path = Path('config/module_characteristics.csv')
        yaml_path = Path('config/module_characteristics.yaml')
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            for _, row in df.iterrows():
                title = str(row.get('module_title', '')).strip()
                if title:
                    raw_mod = row.get('mark_modifier')
                    self.module_chars[title] = {
                        'assessment_type': str(row.get('assessment_type', 'mixed')).strip() or 'mixed',
                        'difficulty_level': float(row.get('difficulty_level', 0.5)),
                        'mark_modifier':    float(raw_mod) if pd.notna(raw_mod) else None,
                        'semester':         int(row.get('semester', 1)),
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

    def _load_disability_modifiers(self):
        """Load disability assessment modifiers from CSV."""
        self.disability_modifiers = {}
        csv_path = Path('config/disability_assessment_modifiers.csv')
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            for _, row in df.iterrows():
                self.disability_modifiers[str(row['disability']).strip().lower()] = float(row['mark_modifier'])

    def _load_assessment_modifiers(self):
        """Load education and SES modifiers from config/assessment_modifiers.yaml."""
        path = Path('config/assessment_modifiers.yaml')
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            self._education_modifiers = data.get('education_modifiers', {})
            raw_ses = data.get('socio_economic_modifiers', {})
            self._ses_modifiers = {int(k): float(v) for k, v in raw_ses.items()}
        else:
            print("Warning: assessment_modifiers.yaml not found. Using hardcoded defaults.")
            self._education_modifiers = {'academic': 1.06, 'vocational': 0.96, 'no_qualifications': 0.92}
            self._ses_modifiers = {1: 0.91, 2: 0.93, 3: 0.95, 4: 0.97, 5: 1.03, 6: 1.05, 7: 1.07, 8: 1.09}

    def _get_assessment_type(self, module_title: str) -> str:
        """Get assessment_type from module_characteristics, else infer from title."""
        title = str(module_title).strip()
        if title in self.module_chars:
            return self.module_chars[title]['assessment_type']
        return _get_assessment_type_fallback(module_title)

    def _get_difficulty_modifier(self, module_title: str) -> float:
        """Get mark modifier from module_characteristics CSV (preferred), else compute from difficulty."""
        title = str(module_title).strip()
        if title in self.module_chars:
            mod = self.module_chars[title].get('mark_modifier')
            if mod is not None:
                return mod
            return _difficulty_to_mark_modifier(self.module_chars[title]['difficulty_level'])
        return _get_module_difficulty_modifier_fallback(module_title)

    def _get_disability_modifier(self, disabilities: str) -> float:
        """Product of modifiers for each disability from config/disability_assessment_modifiers.csv.
        Multiple disabilities compound multiplicatively."""
        if pd.isna(disabilities) or not str(disabilities).strip():
            return 1.0
        raw = str(disabilities).lower()
        if 'no_known_disabilities' in raw:
            return 1.0
        prod = 1.0
        for k, v in self.disability_modifiers.items():
            if k in raw:
                prod *= v
        return prod

    def _get_clan_modifier(self, clan: str) -> float:
        """No direct clan modifier — clan differences emerge from SES, education, and engagement."""
        return 1.0

    def _get_education_modifier(self, education: str) -> float:
        """Education modifier loaded from config/assessment_modifiers.yaml."""
        if pd.isna(education):
            return 1.0
        e = str(education).lower()
        for key, val in self._education_modifiers.items():
            if key in e:
                return float(val)
        return 1.0

    def _get_socio_economic_modifier(self, rank: int) -> float:
        """Socio-economic rank modifier (rank 1=lowest, 8=highest) from config/assessment_modifiers.yaml."""
        r = int(rank) if not pd.isna(rank) else 4
        return self._ses_modifiers.get(r, 1.0)

    def _assessment_dates(self, academic_year: str, semester: int) -> Dict[str, str]:
        """Return MIDTERM and FINAL assessment dates for a given academic year and teaching semester.

        Semester 1 (Autumn): MIDTERM Nov 1, FINAL Dec 15 of the starting calendar year.
        Semester 2 (Spring):  MIDTERM Mar 15, FINAL May 15 of the following calendar year.
        """
        start = int(academic_year.split('-')[0])  # e.g. 1046
        end = start + 1                            # e.g. 1047
        if semester == 1:
            return {'MIDTERM': f"{start}-11-01", 'FINAL': f"{start}-12-15"}
        else:
            return {'MIDTERM': f"{end}-03-15", 'FINAL': f"{end}-05-15"}

    def _engagement_to_modifier(self, avg_engagement: float) -> float:
        """Convert engagement score (0-1) to mark modifier. High engagement slightly boosts marks.
        Formula: 0.88 + 0.24 * engagement, clipped to [0.88, 1.12].
        0.0 -> 0.88, 0.5 -> 1.0, 1.0 -> 1.12."""
        if avg_engagement is None or np.isnan(avg_engagement):
            return 1.0
        return float(np.clip(0.88 + 0.24 * avg_engagement, 0.88, 1.12))

    def generate_mark(self, student: pd.Series, module_title: str,
                     engagement_modifier: Optional[float] = None) -> float:
        """
        Generate a single module mark for a student.
        Base distribution 70% (60,8), 15% (75,6), 15% (45,10).
        Modifiers: species, clan, disability, education, socio-economic, module difficulty, engagement.
        """
        # Base distribution
        r = self.rng.random()
        if r < 0.7:
            base = self.rng.normal(60, 8)
        elif r < 0.85:
            base = self.rng.normal(75, 6)
        else:
            base = self.rng.normal(45, 10)

        # Modifiers (species-level variation is captured by clan modifiers)
        mod = 1.0
        mod *= self._get_clan_modifier(str(student.get('clan', '')).lower())
        mod *= self._get_disability_modifier(student.get('disabilities', ''))
        mod *= self._get_education_modifier(student.get('education', ''))
        mod *= self._get_socio_economic_modifier(student.get('socio_economic_rank', 3))
        mod *= self._get_difficulty_modifier(module_title)
        if engagement_modifier is not None:
            mod *= engagement_modifier

        mark = base * mod + self.rng.normal(0, 5)
        return float(np.clip(round(mark, 1), 0.0, 100.0))

    def _load_engagement_by_student_module(
        self,
        engagement_path: str = "data/stonegrove_weekly_engagement.csv",
        academic_year: Optional[str] = None,
        engagement_df: Optional[pd.DataFrame] = None,
    ) -> Dict[tuple, float]:
        """
        Load weekly engagement and return (student_id, module_title) -> avg_engagement (all weeks).
        If engagement_df is provided, use it directly. Otherwise load from path.
        If academic_year given and column exists, filter to that year.
        """
        final_lookup, _ = self._load_engagement_lookups(
            engagement_path, academic_year=academic_year, engagement_df=engagement_df
        )
        return final_lookup

    def _load_engagement_lookups(
        self,
        engagement_path: str = "data/stonegrove_weekly_engagement.csv",
        academic_year: Optional[str] = None,
        engagement_df: Optional[pd.DataFrame] = None,
    ) -> tuple:
        """
        Return (final_lookup, midterm_lookup):
          - final_lookup:   (student_id, module_title) -> avg_engagement across all 12 weeks
          - midterm_lookup: (student_id, module_title) -> avg_engagement across weeks 1-8

        Midterm captures early enthusiasm + midterm crunch; final uses the full arc.
        """
        if engagement_df is not None:
            df = engagement_df.copy()
        else:
            path = Path(engagement_path)
            if not path.exists():
                return {}, {}
            df = pd.read_csv(path)
        if df.empty or 'student_id' not in df.columns or 'module_title' not in df.columns:
            return {}, {}
        if academic_year and 'academic_year' in df.columns:
            df = df[df['academic_year'] == academic_year]
        cols = [c for c in ['attendance_rate', 'participation_score', 'academic_engagement'] if c in df.columns]
        if not cols:
            return {}, {}
        df = df.copy()
        df['engagement'] = df[cols].mean(axis=1)
        df['student_id'] = df['student_id'].astype(str)
        df['module_title'] = df['module_title'].str.strip()

        # Final: all weeks
        final_agg = df.groupby(['student_id', 'module_title'])['engagement'].mean()
        final_lookup = {k: float(v) for k, v in final_agg.items()}

        # Midterm: weeks 1-8 only
        if 'week_number' in df.columns:
            midterm_df = df[df['week_number'] <= 8]
        else:
            midterm_df = df  # fallback: use all weeks if week_number not present
        midterm_agg = midterm_df.groupby(['student_id', 'module_title'])['engagement'].mean()
        midterm_lookup = {k: float(v) for k, v in midterm_agg.items()}

        return final_lookup, midterm_lookup

    def generate_assessment_data(
        self,
        enrolled_df: pd.DataFrame,
        academic_year: str = "1046-47",
        assessment_date: Optional[str] = None,  # deprecated; dates now computed per module/semester
        weekly_engagement_path: str = "data/stonegrove_weekly_engagement.csv",
        weekly_engagement_df: Optional[pd.DataFrame] = None,
    ) -> pd.DataFrame:
        """
        Generate assessment events for all enrolled students.

        Produces two rows per student per module: MIDTERM and FINAL components.
        - MIDTERM: engagement from weeks 1-8 (early enthusiasm + midterm crunch)
        - FINAL: engagement from all 12 weeks; combined_mark = 0.4*MIDTERM + 0.6*FINAL
        - Progression uses combined_mark from FINAL rows only.

        assessment_date parameter is deprecated and ignored; dates are now derived
        from the module's teaching semester via _assessment_dates().
        """
        final_lookup, midterm_lookup = self._load_engagement_lookups(
            weekly_engagement_path, academic_year=academic_year,
            engagement_df=weekly_engagement_df,
        )
        records = []
        for idx, student in enrolled_df.iterrows():
            sid_raw = student.get('student_id', idx)
            student_id = str(sid_raw.iloc[0]) if isinstance(sid_raw, pd.Series) else str(sid_raw)
            program_code = student['program_code']
            prog_year = int(student.get('programme_year', 1))
            mod_col = f'year{prog_year}_modules'
            modules = _parse_module_list_csv(student.get(mod_col, student.get('year1_modules', '')))

            for module_title in modules:
                if not module_title.strip():
                    continue
                module_title = module_title.strip()
                module_code = self.module_code_lookup.get(
                    (program_code, module_title),
                    f"{program_code}.??"  # should not occur if curriculum is complete
                )
                mod_chars = self.module_chars.get(module_title, {})
                module_semester = mod_chars.get('semester', 1)
                dates = self._assessment_dates(academic_year, module_semester)
                assessment_type = self._get_assessment_type(module_title)

                key = (student_id, module_title)

                # MIDTERM: engagement from weeks 1-8 (captures early enthusiasm + midterm crunch)
                midterm_avg = midterm_lookup.get(key)
                midterm_eng_mod = self._engagement_to_modifier(midterm_avg) if midterm_avg is not None else None
                midterm_mark = self.generate_mark(student, module_title, engagement_modifier=midterm_eng_mod)

                # FINAL: engagement from all 12 weeks
                final_avg = final_lookup.get(key)
                final_eng_mod = self._engagement_to_modifier(final_avg) if final_avg is not None else None
                final_mark = self.generate_mark(student, module_title, engagement_modifier=final_eng_mod)

                # Combined mark weights: 40% midterm, 60% final
                combined_mark = round(0.4 * midterm_mark + 0.6 * final_mark, 1)

                records.append({
                    'student_id': student_id,
                    'academic_year': academic_year,
                    'programme_code': program_code,
                    'module_code': module_code,
                    'component_code': 'MIDTERM',
                    'module_title': module_title,
                    'assessment_type': assessment_type,
                    'assessment_mark': midterm_mark,
                    'combined_mark': None,
                    'grade': _grade_from_mark(midterm_mark),  # formative signal
                    'assessment_date': dates['MIDTERM'],
                    'module_year': prog_year,
                })
                records.append({
                    'student_id': student_id,
                    'academic_year': academic_year,
                    'programme_code': program_code,
                    'module_code': module_code,
                    'component_code': 'FINAL',
                    'module_title': module_title,
                    'assessment_type': assessment_type,
                    'assessment_mark': final_mark,
                    'combined_mark': combined_mark,
                    'grade': _grade_from_mark(combined_mark),
                    'assessment_date': dates['FINAL'],
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
