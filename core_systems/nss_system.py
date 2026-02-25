"""
Stonegrove University NSS (National Student Survey) System

Generates one survey response per final-year student (programme_year == 3) per
academic year, including students repeating their final year.

Eight themes scored 1-5 plus overall satisfaction, mirroring the real NSS structure.
Gaps emerge from: engagement, marks, SES, disability, personality. No direct
species/clan modifier.

Output: stonegrove_nss_responses.csv
"""

import numpy as np
import pandas as pd
import yaml
from pathlib import Path
from typing import Optional


THEMES = [
    'teaching_quality',
    'learning_opportunities',
    'assessment_feedback',
    'academic_support',
    'organisation_management',
    'learning_resources',
    'student_voice',
]


class NSSSystem:
    """
    Generates NSS-style satisfaction scores for all programme_year == 3 students.

    Each student gets:
    - Seven theme scores (1-5 integer)
    - One overall_satisfaction score (1-5 integer)
    - is_repeat_year flag (True if student is repeating Yr3)

    Score model per theme:
        raw = base_score
            + engagement_signal  (weighted engagement metrics, centred at 0.5)
            + mark_signal        (for themes sensitive to marks)
            + ses_adjustment
            + disability_adjustment
            + personality_adjustment
            + student_bias       (correlated noise: systematic over/under-rater)
            + theme_noise        (independent per-theme noise)
        score = clip(round(raw), 1, 5)

    Overall satisfaction is a weighted blend of theme raw scores plus independent noise,
    not a simple average (mirrors real NSS behaviour).
    """

    def __init__(self, seed: int = 42,
                 config_path: str = "config/nss_modifiers.yaml"):
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self.config = self._load_config(config_path)

    def _load_config(self, path: str) -> dict:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"NSS config not found: {path}")
        with open(p, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    # ------------------------------------------------------------------
    # Engagement aggregation
    # ------------------------------------------------------------------

    def _aggregate_engagement(self, weekly_df: pd.DataFrame,
                               academic_year: str) -> pd.DataFrame:
        """
        Return per-student mean engagement metrics for the given academic year.
        Columns: student_id, attendance_rate, participation_score,
                 academic_engagement, social_engagement, stress_level
        """
        if weekly_df is None or weekly_df.empty:
            return pd.DataFrame(columns=['student_id'])

        df = weekly_df.copy()
        df['student_id'] = df['student_id'].astype(str)
        if 'academic_year' in df.columns:
            df = df[df['academic_year'] == academic_year]

        eng_cols = [c for c in ['attendance_rate', 'participation_score',
                                 'academic_engagement', 'social_engagement',
                                 'stress_level'] if c in df.columns]
        if not eng_cols:
            return pd.DataFrame(columns=['student_id'])

        return df.groupby('student_id')[eng_cols].mean().reset_index()

    # ------------------------------------------------------------------
    # Mark aggregation
    # ------------------------------------------------------------------

    def _aggregate_marks(self, assessment_df: pd.DataFrame,
                         academic_year: str) -> pd.DataFrame:
        """Return per-student mean combined_mark for the given academic year (FINAL rows)."""
        if assessment_df is None or assessment_df.empty:
            return pd.DataFrame(columns=['student_id', 'avg_mark'])

        df = assessment_df.copy()
        df['student_id'] = df['student_id'].astype(str)
        if 'academic_year' in df.columns:
            df = df[df['academic_year'] == academic_year]
        if 'component_code' in df.columns:
            df = df[df['component_code'] == 'FINAL']
        df['mark'] = df['combined_mark'].fillna(df['assessment_mark']) \
            if 'combined_mark' in df.columns else df['assessment_mark']

        agg = df.groupby('student_id')['mark'].mean().reset_index()
        agg.columns = ['student_id', 'avg_mark']
        return agg

    # ------------------------------------------------------------------
    # Modifier helpers
    # ------------------------------------------------------------------

    def _has_significant_disability(self, disabilities: str) -> bool:
        raw = str(disabilities).lower()
        if not raw or 'no_known_disabilities' in raw:
            return False
        significant = ['requires_personal_care', 'wheelchair_user',
                       'blind_or_visually_impaired', 'communication_difficulties']
        if any(d in raw for d in significant):
            return True
        parts = [p.strip() for p in raw.split(',') if p.strip() and 'no_known' not in p]
        return len(parts) >= 2

    def _ses_adjustment(self, ses_rank: int) -> float:
        mods = self.config.get('ses_modifiers', {}).get('all_themes', {})
        return float(mods.get(int(ses_rank), mods.get(str(ses_rank), 0.0)))

    def _disability_adjustment(self, theme: str, disabilities: str,
                               sig_disability: bool) -> float:
        if not disabilities or 'no_known_disabilities' in str(disabilities).lower():
            return 0.0
        adj = float(self.config.get('disability_modifiers', {}).get(theme, 0.0))
        if sig_disability:
            adj += float(self.config.get('significant_disability_extra', {}).get(theme, 0.0))
        return adj

    def _personality_adjustment(self, theme: str, student: pd.Series) -> float:
        adj = 0.0
        agr = float(student.get('refined_agreeableness', 0.5))
        neur = float(student.get('refined_neuroticism', 0.5))
        adj += (agr - 0.5) * float(self.config.get('agreeableness_all_themes', 0.30))
        adj += (neur - 0.5) * float(self.config.get('neuroticism_all_themes', -0.35))
        # Theme-specific
        theme_drivers = self.config.get('personality_theme_drivers', {}).get(theme, {})
        for trait, weight in theme_drivers.items():
            adj += (float(student.get(trait, 0.5)) - 0.5) * float(weight)
        return adj

    def _engagement_adjustment(self, theme: str,
                                eng_row: Optional[pd.Series]) -> float:
        if eng_row is None:
            return 0.0
        drivers = self.config.get('engagement_drivers', {}).get(theme, {})
        adj = 0.0
        for metric, weight in drivers.items():
            val = float(eng_row.get(metric, 0.5))
            adj += (val - 0.5) * float(weight)
        return adj

    def _mark_adjustment(self, theme: str, avg_mark: float) -> float:
        mod = float(self.config.get('mark_modifier_per_10pp', {}).get(theme, 0.0))
        return mod * (avg_mark - 60.0) / 10.0

    def _repeat_adjustment(self, theme: str, is_repeat: bool) -> float:
        if not is_repeat:
            return 0.0
        return float(self.config.get('repeat_year_modifier', {}).get(theme, 0.0))

    # ------------------------------------------------------------------
    # Score generation
    # ------------------------------------------------------------------

    def _generate_theme_scores(self, student: pd.Series,
                                eng_row: Optional[pd.Series],
                                avg_mark: float,
                                is_repeat: bool,
                                student_bias: float) -> dict:
        """Generate raw float scores for all 7 themes."""
        bases = self.config.get('base_scores', {})
        theme_noise_std = float(self.config.get('theme_noise_std', 0.38))

        ses = int(student.get('socio_economic_rank', 4))
        disabilities = str(student.get('disabilities', 'no_known_disabilities'))
        sig_dis = self._has_significant_disability(disabilities)
        ses_adj = self._ses_adjustment(ses)

        scores = {}
        for theme in THEMES:
            raw = float(bases.get(theme, 3.5))
            raw += self._engagement_adjustment(theme, eng_row)
            raw += self._mark_adjustment(theme, avg_mark)
            raw += ses_adj
            raw += self._disability_adjustment(theme, disabilities, sig_dis)
            raw += self._personality_adjustment(theme, student)
            raw += self._repeat_adjustment(theme, is_repeat)
            raw += student_bias                                    # correlated noise
            raw += float(self.rng.normal(0, theme_noise_std))     # independent noise
            scores[theme] = raw
        return scores

    def _generate_overall(self, theme_raw_scores: dict,
                           student: pd.Series, is_repeat: bool,
                           student_bias: float) -> float:
        """Overall satisfaction: weighted blend of theme raws + own noise."""
        weights = self.config.get('overall_weights', {})
        total_w = sum(weights.values()) or 1.0
        weighted = sum(theme_raw_scores.get(t, 3.5) * w for t, w in weights.items()) / total_w

        # Own base, SES, disability, personality
        base_overall = float(self.config.get('base_scores', {}).get('overall_satisfaction', 3.6))
        ses = int(student.get('socio_economic_rank', 4))
        disabilities = str(student.get('disabilities', 'no_known_disabilities'))
        sig_dis = self._has_significant_disability(disabilities)

        overall = base_overall + 0.5 * (weighted - base_overall)   # blend base with theme signal
        overall += self._ses_adjustment(ses)
        overall += self._disability_adjustment('overall_satisfaction', disabilities, sig_dis)
        overall += self._personality_adjustment('overall_satisfaction', student)
        overall += self._repeat_adjustment('overall_satisfaction', is_repeat)
        overall += student_bias
        overall += float(self.rng.normal(0, float(self.config.get('theme_noise_std', 0.38))))
        return overall

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def generate_responses(
        self,
        enrolled_df: pd.DataFrame,
        academic_year: str,
        weekly_engagement_df: Optional[pd.DataFrame] = None,
        assessment_df: Optional[pd.DataFrame] = None,
    ) -> pd.DataFrame:
        """
        Generate NSS responses for all programme_year == 3 students in academic_year.
        Includes students who are repeating their final year.

        Args:
            enrolled_df: all enrolled students this year (must include programme_year,
                student traits, SES, disabilities, status)
            academic_year: current academic year
            weekly_engagement_df: weekly engagement data for the year
            assessment_df: assessment events for the year (FINAL rows used for marks)

        Returns:
            DataFrame with one row per Yr3 student.
        """
        # Filter to Yr3 students
        yr3 = enrolled_df[enrolled_df['programme_year'].astype(int) == 3].copy()
        yr3['student_id'] = yr3['student_id'].astype(str)
        if yr3.empty:
            return pd.DataFrame()

        # Aggregate engagement and marks
        eng_agg = self._aggregate_engagement(weekly_engagement_df, academic_year)
        eng_agg['student_id'] = eng_agg['student_id'].astype(str)
        eng_lookup = eng_agg.set_index('student_id') if not eng_agg.empty else pd.DataFrame()

        mark_agg = self._aggregate_marks(assessment_df, academic_year)
        mark_agg['student_id'] = mark_agg['student_id'].astype(str)
        mark_lookup = mark_agg.set_index('student_id')['avg_mark'].to_dict() \
            if not mark_agg.empty else {}

        student_bias_std = float(self.config.get('student_bias_std', 0.28))

        records = []
        for _, student in yr3.iterrows():
            sid = str(student['student_id'])
            is_repeat = str(student.get('status', '')).lower() == 'repeating'
            avg_mark = float(mark_lookup.get(sid, student.get('avg_mark', 55.0) or 55.0))
            eng_row = eng_lookup.loc[sid] if (not eng_lookup.empty and sid in eng_lookup.index) else None

            # One student-level bias (systematic over/under-rater)
            student_bias = float(self.rng.normal(0, student_bias_std))

            theme_raws = self._generate_theme_scores(
                student, eng_row, avg_mark, is_repeat, student_bias
            )
            overall_raw = self._generate_overall(theme_raws, student, is_repeat, student_bias)

            rec = {
                'student_id': sid,
                'academic_year': academic_year,
                'programme_code': student.get('program_code', student.get('programme_code')),
                'programme_year': 3,
                'is_repeat_year': is_repeat,
            }
            for theme in THEMES:
                rec[theme] = int(np.clip(round(theme_raws[theme]), 1, 5))
            rec['overall_satisfaction'] = int(np.clip(round(overall_raw), 1, 5))

            records.append(rec)

        return pd.DataFrame(records)
