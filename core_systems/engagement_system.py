import csv
import io
import pandas as pd
import numpy as np
import yaml
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path


def _parse_module_list_csv(value: str) -> List[str]:
    """Parse module list from CSV-formatted string (handles commas in module names)."""
    if pd.isna(value) or not str(value).strip():
        return []
    reader = csv.reader(io.StringIO(str(value)))
    return [m.strip() for m in next(reader) if m.strip()]

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
    programme_year: int   # year in programme (1/2/3); was 'semester' before Feb 2026 refactor
    semester: int         # teaching semester (1 = Autumn, 2 = Spring); 0 if mixed/unknown
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

    Weekly engagement uses an AR(1) autocorrelated noise model so that
    good/bad weeks cluster realistically. Disability and SES modifiers shift
    the baseline and widen variability. A semester temporal arc adds an
    early-enthusiasm boost, midterm crunch, and exam-period stress spike.
    """

    # Maps base_engagement keys → short metric name → output column name
    _METRIC_MAP = [
        ('base_attendance',         'attendance',         'attendance_rate'),
        ('base_participation',      'participation',      'participation_score'),
        ('base_academic_engagement','academic_engagement','academic_engagement'),
        ('base_social_engagement',  'social_engagement',  'social_engagement'),
        ('base_stress',             'stress',             'stress_level'),
    ]

    def __init__(self):
        """Initialize the engagement system"""
        self._load_characteristics()
        self._load_engagement_modifiers()

    def _load_characteristics(self):
        """Load module and program characteristics from CSV (preferred) or YAML."""
        mc_csv = Path('config/module_characteristics.csv')
        pc_csv = Path('config/programme_characteristics.csv')
        mc_yaml = Path('config/module_characteristics.yaml')
        pc_yaml = Path('config/program_characteristics.yaml')

        # Module characteristics
        self._module_chars = {}
        if mc_csv.exists():
            df = pd.read_csv(mc_csv)
            for _, row in df.iterrows():
                title = str(row.get('module_title', '')).strip()
                if title:
                    self._module_chars[title] = {
                        'difficulty': float(row.get('difficulty_level', 0.5)),
                        'social_requirements': float(row.get('social_requirements', 0.5)),
                        'creativity_requirements': float(row.get('creativity_requirements', 0.5)),
                        'semester': int(row.get('semester', 1)),
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

    def _load_engagement_modifiers(self):
        """Load disability, SES, and temporal arc engagement modifiers from YAML."""
        path = Path('config/engagement_modifiers.yaml')
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            self._disability_eng_mods = data.get('disability_modifiers', {})
            raw_ses = data.get('ses_modifiers', {})
            self._ses_eng_mods = {int(k): v for k, v in raw_ses.items()}
            self._temporal_arc = data.get('temporal_arc', {})
        else:
            print("Warning: engagement_modifiers.yaml not found. Disability/SES/temporal modifiers disabled.")
            self._disability_eng_mods = {}
            self._ses_eng_mods = {}
            self._temporal_arc = {}

    # ------------------------------------------------------------------
    # Module / programme characteristics
    # ------------------------------------------------------------------

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
        difficulty = 0.5
        social_requirements = 0.5
        creativity_requirements = 0.5

        if any(word in title_lower for word in ['advanced', 'capstone', 'research']):
            difficulty += 0.2
        elif any(word in title_lower for word in ['epistemolog', 'theoretical', 'complex']):
            difficulty += 0.15
        elif any(word in title_lower for word in [
            'embodied', 'somatic', 'fermentation', 'cultivation', 'harvest',
            'care', 'healing', 'hospitality', 'ritual', 'ethics', 'indigenous'
        ]):
            difficulty += 0.05

        if any(word in title_lower for word in ['group', 'team', 'collaboration', 'discussion', 'circle', 'listening']):
            social_requirements += 0.25
        elif any(word in title_lower for word in ['individual', 'independent', 'research']):
            social_requirements -= 0.15

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

    # ------------------------------------------------------------------
    # Base engagement
    # ------------------------------------------------------------------

    def calculate_base_engagement(self, personality: Dict[str, float],
                                  motivation: Dict[str, float]) -> Dict[str, float]:
        """Calculate base engagement levels from personality and motivation."""
        base_attendance = (
            personality.get('refined_conscientiousness', 0.5) * 0.4 +
            motivation.get('motivation_academic_drive', 0.5) * 0.3 +
            personality.get('refined_resilience', 0.5) * 0.2 +
            motivation.get('motivation_practical_skills', 0.5) * 0.1
        )
        base_participation = (
            personality.get('refined_extraversion', 0.5) * 0.4 +
            motivation.get('motivation_social_connection', 0.5) * 0.3 +
            personality.get('refined_leadership_tendency', 0.5) * 0.2 +
            personality.get('refined_social_anxiety', 0.5) * -0.1
        )
        base_academic_engagement = (
            personality.get('refined_academic_curiosity', 0.5) * 0.4 +
            motivation.get('motivation_intellectual_curiosity', 0.5) * 0.3 +
            personality.get('refined_openness', 0.5) * 0.2 +
            motivation.get('motivation_academic_drive', 0.5) * 0.1
        )
        base_social_engagement = (
            personality.get('refined_extraversion', 0.5) * 0.5 +
            motivation.get('motivation_social_connection', 0.5) * 0.3 +
            personality.get('refined_leadership_tendency', 0.5) * 0.2
        )
        base_stress = (
            personality.get('refined_neuroticism', 0.5) * 0.4 +
            personality.get('refined_social_anxiety', 0.5) * 0.3 +
            (1 - personality.get('refined_resilience', 0.5)) * 0.2 +
            (1 - motivation.get('motivation_personal_growth', 0.5)) * 0.1
        )
        return {
            'base_attendance':          float(np.clip(base_attendance, 0.1, 0.95)),
            'base_participation':       float(np.clip(base_participation, 0.1, 0.95)),
            'base_academic_engagement': float(np.clip(base_academic_engagement, 0.1, 0.95)),
            'base_social_engagement':   float(np.clip(base_social_engagement, 0.1, 0.95)),
            'base_stress':              float(np.clip(base_stress, 0.05, 0.9)),
        }

    def apply_module_modifiers(self, base_engagement: Dict[str, float],
                               module_characteristics: Dict[str, float],
                               personality: Dict[str, float]) -> Dict[str, float]:
        """Apply module-specific modifiers to base engagement."""
        modified = base_engagement.copy()
        difficulty = module_characteristics['difficulty']
        difficulty_modifier = (difficulty - 0.5) * 0.2

        if personality.get('refined_conscientiousness', 0.5) > 0.7:
            modified['base_attendance']          += difficulty_modifier * 0.5
            modified['base_academic_engagement'] += difficulty_modifier
        else:
            modified['base_attendance']          -= difficulty_modifier * 0.3
            modified['base_academic_engagement'] -= difficulty_modifier * 0.5

        social_req = module_characteristics['social_requirements']
        social_modifier = (social_req - 0.5) * 0.3

        if personality.get('refined_extraversion', 0.5) > 0.6:
            modified['base_participation']    += social_modifier
            modified['base_social_engagement'] += social_modifier
        else:
            modified['base_participation']    -= social_modifier * 0.5
            modified['base_social_engagement'] -= social_modifier * 0.3
            modified['base_stress']           += social_modifier * 0.2

        creativity_req = module_characteristics['creativity_requirements']
        creativity_modifier = (creativity_req - 0.5) * 0.2

        if personality.get('refined_openness', 0.5) > 0.6:
            modified['base_academic_engagement'] += creativity_modifier
        else:
            modified['base_academic_engagement'] -= creativity_modifier * 0.5

        for key in modified:
            clip_max = 0.9 if key == 'base_stress' else 0.95
            modified[key] = float(np.clip(modified[key], 0.05, clip_max))

        return modified

    # ------------------------------------------------------------------
    # Modifier helpers
    # ------------------------------------------------------------------

    def _get_disability_base_mods(self, disabilities_str: str) -> Dict[str, float]:
        """Return combined base engagement adjustments for a student's disabilities."""
        if not disabilities_str or 'no_known_disabilities' in disabilities_str:
            return {}
        result: Dict[str, float] = {}
        for dis_key, dis_data in self._disability_eng_mods.items():
            if dis_key == 'no_known_disabilities':
                continue
            if dis_key in disabilities_str:
                for metric, adj in (dis_data.get('base') or {}).items():
                    result[metric] = result.get(metric, 0.0) + float(adj)
        return result

    def _get_disability_std_extra(self, disabilities_str: str) -> float:
        """Return additional noise std from disabilities (additive for comorbidities, capped at 0.15)."""
        if not disabilities_str or 'no_known_disabilities' in disabilities_str:
            return 0.0
        total = 0.0
        for dis_key, dis_data in self._disability_eng_mods.items():
            if dis_key == 'no_known_disabilities':
                continue
            if dis_key in disabilities_str:
                total += float(dis_data.get('std_extra', 0.0))
        return min(total, 0.15)

    def _get_ses_mods(self, ses_rank: int) -> Dict[str, float]:
        """Return base engagement adjustments for SES rank."""
        return dict(self._ses_eng_mods.get(int(ses_rank), {}))

    def _get_temporal_modifiers(self, week: int, personality: Dict[str, float]) -> Dict[str, float]:
        """Return engagement adjustments for this point in the semester arc."""
        arc = self._temporal_arc
        conscientiousness = personality.get('refined_conscientiousness', 0.5)

        if week <= 2:
            return dict(arc.get('early', {}))
        elif 6 <= week <= 8:
            return dict(arc.get('midterm', {}))
        elif week >= 10:
            mods = dict(arc.get('exam_base', {}))
            if conscientiousness > 0.6:
                for k, v in arc.get('exam_high_conscientiousness', {}).items():
                    mods[k] = mods.get(k, 0.0) + float(v)
            else:
                for k, v in arc.get('exam_low_conscientiousness', {}).items():
                    mods[k] = mods.get(k, 0.0) + float(v)
            return mods
        return {}

    def _generate_week_deviations(self, n_weeks: int, noise_std: float,
                                   alpha: float = 0.4) -> np.ndarray:
        """
        AR(1) autocorrelated week-level deviations.
        Positive deviation = good week (more engagement, less stress).
        Stationary variance = noise_std^2 regardless of alpha.
        """
        scale = float(np.sqrt(max(0.0, 1.0 - alpha ** 2))) * noise_std
        devs = np.zeros(n_weeks)
        prev = 0.0
        for i in range(n_weeks):
            devs[i] = alpha * prev + np.random.normal(0, scale)
            prev = devs[i]
        return devs

    # ------------------------------------------------------------------
    # Semester summary
    # ------------------------------------------------------------------

    def generate_semester_engagement(self, student_id: str, programme_year: int,
                                     weekly_engagements: List[WeeklyEngagement]
                                     ) -> Optional[SemesterEngagement]:
        """Generate semester-level engagement summary from weekly data."""
        if not weekly_engagements:
            return None

        avg_attendance    = np.mean([w.attendance_rate for w in weekly_engagements])
        avg_participation = np.mean([w.participation_score for w in weekly_engagements])
        avg_academic      = np.mean([w.academic_engagement for w in weekly_engagements])
        avg_social        = np.mean([w.social_engagement for w in weekly_engagements])
        avg_stress        = np.mean([w.stress_level for w in weekly_engagements])

        mid = len(weekly_engagements) // 2
        first_half  = np.mean([w.attendance_rate for w in weekly_engagements[:mid]])
        second_half = np.mean([w.attendance_rate for w in weekly_engagements[mid:]])

        if second_half > first_half + 0.05:
            trend = 'improving'
        elif second_half < first_half - 0.05:
            trend = 'declining'
        else:
            trend = 'stable'

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
            programme_year=programme_year,
            semester=0,  # summary mixes both teaching semesters
            program_code=weekly_engagements[0].program_code,
            average_attendance=float(avg_attendance),
            average_participation=float(avg_participation),
            average_academic_engagement=float(avg_academic),
            average_social_engagement=float(avg_social),
            average_stress_level=float(avg_stress),
            engagement_trend=trend,
            risk_factors=risk_factors,
        )

    # ------------------------------------------------------------------
    # Simplified single-record generation (kept for compatibility)
    # ------------------------------------------------------------------

    def generate_weekly_variation(self, base_engagement: Dict[str, float]) -> Dict[str, float]:
        """
        Simplified weekly variation with fixed noise std.
        Used by generate_weekly_engagement for single-record calls.
        For full autocorrelated generation use generate_engagement_data.
        """
        weekly_engagement = {}
        for key, base_value in base_engagement.items():
            variation = np.random.normal(0, 0.15)  # fixed std, not proportional
            weekly_engagement[key.replace('base_', '')] = float(np.clip(base_value + variation, 0.05, 0.95))
        return weekly_engagement

    def generate_weekly_engagement(self, student_id: str, week_number: int,
                                   program_code: str, programme_name: str,
                                   module_title: str,
                                   personality: Dict[str, float],
                                   motivation: Dict[str, float]) -> WeeklyEngagement:
        """
        Generate a single weekly engagement record (simplified, no autocorrelation).
        For full longitudinal generation use generate_engagement_data.
        """
        module_chars = self.get_module_characteristics(module_title)
        base_engagement = self.calculate_base_engagement(personality, motivation)
        modified_engagement = self.apply_module_modifiers(base_engagement, module_chars, personality)
        weekly_engagement = self.generate_weekly_variation(modified_engagement)

        engagement_factors = {
            'module_difficulty':              module_chars['difficulty'],
            'module_social_requirements':     module_chars['social_requirements'],
            'module_creativity_requirements': module_chars['creativity_requirements'],
            'personality_conscientiousness':  personality.get('refined_conscientiousness', 0.5),
            'personality_extraversion':       personality.get('refined_extraversion', 0.5),
            'motivation_academic_drive':      motivation.get('motivation_academic_drive', 0.5),
            'motivation_social_connection':   motivation.get('motivation_social_connection', 0.5),
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
            engagement_factors=engagement_factors,
        )

    # ------------------------------------------------------------------
    # Main batch generation
    # ------------------------------------------------------------------

    def generate_engagement_data(
        self,
        enrolled_students_df: pd.DataFrame,
        weeks_per_semester: int = 12,
        academic_year: str = "",
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Generate engagement data for all enrolled students.

        Architecture:
        - Per student: base engagement from personality/motivation, shifted by disability
          and SES modifiers.
        - Per module: base modified by module difficulty/social/creativity requirements.
        - Per week: AR(1) autocorrelated week-level deviation (shared across modules that
          week) plus a temporal arc (early enthusiasm, midterm crunch, exam stress) plus
          small independent module-level noise.
        - Stress is inverted relative to the week deviation (good week → less stress).

        Returns: (weekly_engagement_df, semester_engagement_df)
        """
        weekly_data = []
        semester_data = []

        personality_cols = [c for c in enrolled_students_df.columns if c.startswith('refined_')]
        motivation_cols  = [c for c in enrolled_students_df.columns if c.startswith('motivation_')]

        for idx, student in enrolled_students_df.iterrows():
            # --- Student identity ---
            sid_raw = student.get("student_id", idx)
            student_id = str(sid_raw.iloc[0]) if isinstance(sid_raw, pd.Series) else str(sid_raw)
            ay = academic_year or str(student.get('academic_year', ''))

            personality = {c: student[c] for c in personality_cols}
            motivation  = {c: student[c] for c in motivation_cols}

            disabilities = str(student.get('disabilities', 'no_known_disabilities'))
            ses_rank     = int(student.get('socio_economic_rank', 4))
            prog_year    = int(student.get('programme_year', 1))

            mod_col  = f'year{prog_year}_modules'
            modules  = _parse_module_list_csv(student.get(mod_col, student.get('year1_modules', '')))
            program_code    = student['program_code']
            programme_name  = student.get('program_name', '')

            # --- Base engagement + disability + SES adjustments ---
            base_engagement = self.calculate_base_engagement(personality, motivation)

            for metric, adj in self._get_disability_base_mods(disabilities).items():
                bk = f'base_{metric}'
                if bk in base_engagement:
                    base_engagement[bk] = float(np.clip(base_engagement[bk] + adj, 0.05, 0.95))

            for metric, adj in self._get_ses_mods(ses_rank).items():
                bk = f'base_{metric}'
                if bk in base_engagement:
                    base_engagement[bk] = float(np.clip(base_engagement[bk] + adj, 0.05, 0.95))

            # --- Per-module base (module difficulty/social/creativity) ---
            module_bases: Dict[str, Dict] = {}
            for module in modules:
                m = module.strip()
                if m:
                    module_chars = self.get_module_characteristics(m)
                    module_bases[m] = self.apply_module_modifiers(dict(base_engagement), module_chars, personality)

            # --- Autocorrelated week deviations ---
            # Arc alignment: weeks 1-2 = early enthusiasm, 6-8 = midterm crunch, 10-12 = exam stress.
            # The MIDTERM assessment component uses the weeks 1-8 engagement average (captures the crunch);
            # the FINAL component uses all 12 weeks. This alignment is emergent from the temporal arc.
            noise_std = 0.12 + self._get_disability_std_extra(disabilities)
            week_devs = self._generate_week_deviations(weeks_per_semester, noise_std)

            # --- Generate weekly records ---
            all_weekly: List[WeeklyEngagement] = []

            for w_idx, week in enumerate(range(1, weeks_per_semester + 1)):
                t_mods   = self._get_temporal_modifiers(week, personality)
                week_dev = week_devs[w_idx]

                for module in modules:
                    m = module.strip()
                    if not m:
                        continue

                    mod_base = module_bases.get(m, base_engagement)
                    mod_semester = self._module_chars.get(m, {}).get('semester', 1)
                    rec: Dict = {
                        'student_id':   student_id,
                        'week_number':  week,
                        'program_code': program_code,
                        'module_title': m,
                        'semester':     mod_semester,
                    }
                    if ay:
                        rec['academic_year'] = ay

                    for bk, sk, ok in self._METRIC_MAP:
                        base_val = mod_base.get(bk, 0.5)
                        # Stress inverted: positive week_dev = good week = less stress
                        if sk == 'stress':
                            val = base_val - week_dev + t_mods.get('stress', 0.0)
                        else:
                            val = base_val + week_dev + t_mods.get(sk, 0.0)
                        val += np.random.normal(0, 0.05)  # small module-specific noise
                        rec[ok] = float(np.clip(val, 0.05, 0.95))

                    # Analysis columns
                    module_chars = self.get_module_characteristics(m)
                    rec['module_difficulty']              = module_chars['difficulty']
                    rec['module_social_requirements']     = module_chars['social_requirements']
                    rec['module_creativity_requirements'] = module_chars['creativity_requirements']
                    rec['personality_conscientiousness']  = personality.get('refined_conscientiousness', 0.5)
                    rec['personality_extraversion']       = personality.get('refined_extraversion', 0.5)
                    rec['motivation_academic_drive']      = motivation.get('motivation_academic_drive', 0.5)
                    rec['motivation_social_connection']   = motivation.get('motivation_social_connection', 0.5)

                    all_weekly.append(WeeklyEngagement(
                        student_id=student_id,
                        week_number=week,
                        program_code=program_code,
                        module_title=m,
                        attendance_rate=rec['attendance_rate'],
                        participation_score=rec['participation_score'],
                        academic_engagement=rec['academic_engagement'],
                        social_engagement=rec['social_engagement'],
                        stress_level=rec['stress_level'],
                        engagement_factors={},
                    ))
                    weekly_data.append(rec)

            # --- Semester summary ---
            if all_weekly:
                sem = self.generate_semester_engagement(student_id, prog_year, all_weekly)
                if sem:
                    d = {
                        'student_id':                    sem.student_id,
                        'programme_year':                sem.programme_year,
                        'program_code':                  sem.program_code,
                        'average_attendance':            sem.average_attendance,
                        'average_participation':         sem.average_participation,
                        'average_academic_engagement':   sem.average_academic_engagement,
                        'average_social_engagement':     sem.average_social_engagement,
                        'average_stress_level':          sem.average_stress_level,
                        'engagement_trend':              sem.engagement_trend,
                        'risk_factors': ','.join(sem.risk_factors) if sem.risk_factors else 'none',
                    }
                    if ay:
                        d['academic_year'] = ay
                    semester_data.append(d)

        return pd.DataFrame(weekly_data), pd.DataFrame(semester_data)


def main():
    """Test the engagement system"""
    print("Stonegrove University Engagement System")
    print("=" * 60)

    engagement_system = EngagementSystem()

    enrolled_df = pd.read_csv('data/stonegrove_enrolled_students.csv')
    print(f"Loaded {len(enrolled_df)} enrolled students")

    weekly_df, semester_df = engagement_system.generate_engagement_data(enrolled_df, weeks_per_semester=12)

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
    print(semester_df['engagement_trend'].value_counts())

    print(f"\n=== Risk Factors ===")
    print(semester_df['risk_factors'].value_counts().head(10))

    weekly_df.to_csv('data/stonegrove_weekly_engagement.csv', index=False)
    semester_df.to_csv('data/stonegrove_semester_engagement.csv', index=False)
    print(f"\nSaved engagement data:")
    print(f"   - Weekly: data/stonegrove_weekly_engagement.csv")
    print(f"   - Semester: data/stonegrove_semester_engagement.csv")

    print(f"\n=== Sample Weekly Engagement ===")
    sample_cols = ['student_id', 'week_number', 'module_title', 'attendance_rate',
                   'participation_score', 'academic_engagement', 'stress_level']
    print(weekly_df[sample_cols].head(10))


if __name__ == "__main__":
    main()
