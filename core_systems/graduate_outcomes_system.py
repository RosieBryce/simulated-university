"""
Stonegrove University Graduate Outcomes System

Generates post-graduation employment outcomes for all graduates (~15 months after graduation).
One row per graduate in stonegrove_graduate_outcomes.csv.

Outcome gaps emerge from: degree classification, SES, disability, programme, personality.
No direct species/clan modifier — same design principle as the assessment system.
"""

import numpy as np
import pandas as pd
import yaml
from pathlib import Path
from typing import Optional


def _log_odds(p: float) -> float:
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return float(np.log(p / (1 - p)))


def _inv_log_odds(x: float) -> float:
    return float(1.0 / (1.0 + np.exp(-x)))


def _degree_classification(avg_mark: float) -> str:
    """UK degree classification from weighted average mark."""
    if avg_mark >= 70:
        return "First"
    if avg_mark >= 60:
        return "2:1"
    if avg_mark >= 50:
        return "2:2"
    return "Third"


class GraduateOutcomesSystem:
    """
    Generates graduate employment outcomes for students with status='graduated'.

    Outcomes modelled:
    - outcome_type: employed / further_study / unemployed / unknown
    - professional_level: professional / non_professional
    - employment_sector: faculty-mapped sector (string)
    - salary_band: 1-5 proxy
    - time_to_outcome_months: months from graduation to outcome
    - degree_classification: First / 2:1 / 2:2 / Third (computed from Y2+Y3 marks)
    - outcome_recorded_at: ISO date (~15 months post-graduation)
    """

    def __init__(self, seed: int = 42,
                 config_path: str = "config/graduate_outcomes.yaml"):
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self.config = self._load_config(config_path)

    def _load_config(self, path: str) -> dict:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Graduate outcomes config not found: {path}")
        with open(p, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    # ------------------------------------------------------------------
    # Degree classification
    # ------------------------------------------------------------------

    def _compute_degree_classifications(
        self,
        student_ids: list,
        assessment_df: Optional[pd.DataFrame],
        fallback_avg_marks: dict,
    ) -> dict:
        """
        Compute degree classification for each student from Y2+Y3 FINAL marks.
        Weights: Y1=0, Y2=1/3, Y3=2/3 (UK standard).
        Falls back to overall avg_mark from progression if no assessment data.
        Returns {student_id -> (degree_classification, weighted_avg)}
        """
        year_weights = self.config.get("degree_year_weights", {1: 0.0, 2: 0.333, 3: 0.667})
        result = {}

        if assessment_df is not None and not assessment_df.empty:
            finals = assessment_df[assessment_df.get('component_code', pd.Series(['FINAL'] * len(assessment_df))) == 'FINAL'].copy() \
                if 'component_code' in assessment_df.columns else assessment_df.copy()
            finals['mark'] = finals['combined_mark'].fillna(finals['assessment_mark']) \
                if 'combined_mark' in finals.columns else finals['assessment_mark']
            finals['student_id'] = finals['student_id'].astype(str)

            for sid in student_ids:
                sid = str(sid)
                rows = finals[finals['student_id'] == sid]
                if rows.empty:
                    avg = fallback_avg_marks.get(sid, 50.0)
                    result[sid] = (_degree_classification(avg), avg)
                    continue

                weighted_sum = 0.0
                weight_total = 0.0
                for yr, w in year_weights.items():
                    if w == 0.0:
                        continue
                    yr_rows = rows[rows.get('module_year', pd.Series(dtype=int)) == yr] \
                        if 'module_year' in rows.columns else pd.DataFrame()
                    if len(yr_rows) > 0:
                        weighted_sum += yr_rows['mark'].mean() * w
                        weight_total += w

                if weight_total > 0:
                    weighted_avg = weighted_sum / weight_total
                else:
                    # Only Y1 data available — fall back to overall mean
                    weighted_avg = rows['mark'].mean()

                result[sid] = (_degree_classification(weighted_avg), round(float(weighted_avg), 1))
        else:
            for sid in student_ids:
                sid = str(sid)
                avg = fallback_avg_marks.get(sid, 50.0)
                result[sid] = (_degree_classification(avg), avg)

        return result

    # ------------------------------------------------------------------
    # Outcome helpers
    # ------------------------------------------------------------------

    def _get_outcome_type(self, student: pd.Series, degree_class: str) -> str:
        """Draw outcome type: employed / further_study / unemployed / unknown."""
        base = self.config.get("base_outcome_probabilities", {
            "employed": 0.65, "further_study": 0.20,
            "unemployed": 0.10, "unknown": 0.05,
        })

        # Adjust employed probability via log-odds
        emp_mod = self.config.get("degree_classification_modifiers", {}) \
            .get("employment_log_odds", {}).get(degree_class, 0.0)
        p_employed = float(np.clip(
            _inv_log_odds(_log_odds(base["employed"]) + emp_mod), 0.05, 0.95
        ))

        # Adjust further_study probability
        fs_mod = self.config.get("degree_classification_modifiers", {}) \
            .get("further_study_log_odds", {}).get(degree_class, 0.0)
        p_further = float(np.clip(
            _inv_log_odds(_log_odds(base["further_study"]) + fs_mod), 0.02, 0.50
        ))

        # Renormalise
        p_unemployed = base["unemployed"]
        p_unknown = base["unknown"]
        total = p_employed + p_further + p_unemployed + p_unknown
        probs = [p / total for p in [p_employed, p_further, p_unemployed, p_unknown]]
        choices = ["employed", "further_study", "unemployed", "unknown"]
        return str(self.rng.choice(choices, p=probs))

    def _get_professional_level(self, student: pd.Series, degree_class: str,
                                faculty: str) -> str:
        """Determine professional / non_professional employment."""
        fac_base = self.config.get("faculty_professional_base", {}).get(faculty, 0.55)
        log_odds = _log_odds(fac_base)

        # Degree classification
        dc_mod = self.config.get("degree_classification_modifiers", {}) \
            .get("professional_log_odds", {}).get(degree_class, 0.0)
        log_odds += dc_mod

        # SES — social capital / network effect
        ses = int(student.get("socio_economic_rank", 4))
        ses_mods = self.config.get("ses_professional_modifiers", {})
        log_odds += float(ses_mods.get(ses, ses_mods.get(str(ses), 0.0)))

        # Disability
        disabilities = str(student.get("disabilities", "")).lower()
        if disabilities and "no_known_disabilities" not in disabilities:
            log_odds += float(self.config.get("disability_professional_modifier", -0.40))

        # Personality
        extrav = float(student.get("refined_extraversion", 0.5))
        consc = float(student.get("refined_conscientiousness", 0.5))
        career = float(student.get("motivation_career_focus", 0.5))
        log_odds += (extrav - 0.5) * float(self.config.get("extraversion_professional_weight", 0.25))
        log_odds += (consc - 0.5) * float(self.config.get("conscientiousness_professional_weight", 0.35))
        log_odds += (career - 0.5) * float(self.config.get("career_focus_weight", 0.30))

        p_professional = float(np.clip(_inv_log_odds(log_odds), 0.05, 0.95))
        return "professional" if self.rng.random() < p_professional else "non_professional"

    def _get_employment_sector(self, faculty: str, outcome_type: str) -> Optional[str]:
        """Pick an employment sector from the faculty's sector list."""
        if outcome_type == "further_study":
            return "further_study"
        if outcome_type in ("unemployed", "unknown"):
            return None
        sectors = self.config.get("faculty_sectors", {}).get(faculty, ["general_employment"])
        return str(self.rng.choice(sectors))

    def _get_salary_band(self, student: pd.Series, degree_class: str,
                         professional_level: str, outcome_type: str) -> Optional[int]:
        """Salary band 1-5. Only for employed students."""
        if outcome_type != "employed":
            return None
        base = float(self.config.get("salary_band_base", {}).get(degree_class, 2))

        # SES effect on salary
        ses = int(student.get("socio_economic_rank", 4))
        ses_mods = self.config.get("ses_salary_modifiers", {})
        base += float(ses_mods.get(ses, ses_mods.get(str(ses), 0.0)))

        # Professional role boosts salary
        if professional_level == "professional":
            base += 0.75

        # Small random noise
        base += float(self.rng.normal(0, 0.4))
        return int(np.clip(round(base), 1, 5))

    def _get_time_to_outcome(self, outcome_type: str) -> int:
        """Months from graduation to outcome, triangular distribution."""
        params = self.config.get("time_to_outcome_months", {}).get(
            outcome_type, {"min": 0, "mode": 6, "max": 18}
        )
        val = self.rng.triangular(params["min"], params["mode"], params["max"])
        return int(round(float(np.clip(val, 0, 24))))

    def _outcome_recorded_at(self, academic_year: str) -> str:
        """ISO date ~15 months after end of graduation year."""
        survey_months = int(self.config.get("outcome_survey_months_after_graduation", 15))
        # Graduation year ends ~May of year+1; add survey_months
        start = int(academic_year.split("-")[0])
        end_month = 5  # May of the second calendar year
        total_months = (start + 1) * 12 + end_month + survey_months
        yr = total_months // 12
        mo = total_months % 12
        if mo == 0:
            mo = 12
            yr -= 1
        return f"{yr}-{mo:02d}-01"

    # ------------------------------------------------------------------
    # Main generation
    # ------------------------------------------------------------------

    def generate_outcomes(
        self,
        graduates_enrolled_df: pd.DataFrame,
        academic_year: str,
        all_assessment_df: Optional[pd.DataFrame] = None,
    ) -> pd.DataFrame:
        """
        Generate graduate outcomes for all students who graduated in academic_year.

        Args:
            graduates_enrolled_df: enrolled students with status='graduated' this year.
                Must include student traits (personality, motivation, SES, disabilities).
            academic_year: the year these students graduated.
            all_assessment_df: full assessment history (all years) for degree classification.
                Uses Y2+Y3 FINAL combined_mark weighted 1/3 : 2/3. If None, falls back
                to avg_mark from enrolled_df.

        Returns:
            DataFrame with one row per graduate.
        """
        if graduates_enrolled_df.empty:
            return pd.DataFrame()

        grads = graduates_enrolled_df.copy()
        grads['student_id'] = grads['student_id'].astype(str)

        # Build fallback avg_mark from enrolled_df (avg_mark column if present)
        fallback_marks = {}
        if 'avg_mark' in grads.columns:
            fallback_marks = grads.set_index('student_id')['avg_mark'].to_dict()

        # Compute degree classifications
        student_ids = grads['student_id'].tolist()
        classifications = self._compute_degree_classifications(
            student_ids, all_assessment_df, fallback_marks
        )

        recorded_at = self._outcome_recorded_at(academic_year)

        records = []
        for _, student in grads.iterrows():
            sid = str(student['student_id'])
            degree_class, weighted_avg = classifications.get(sid, ("2:2", 50.0))
            faculty = str(student.get('program_code', student.get('programme_code', '1.1.1'))).split('.')[0]

            outcome_type = self._get_outcome_type(student, degree_class)

            if outcome_type == "employed":
                professional_level = self._get_professional_level(student, degree_class, faculty)
                employment_sector = self._get_employment_sector(faculty, outcome_type)
                salary_band = self._get_salary_band(student, degree_class, professional_level, outcome_type)
            elif outcome_type == "further_study":
                professional_level = None
                employment_sector = "further_study"
                salary_band = None
            else:
                professional_level = None
                employment_sector = None
                salary_band = None

            time_to_outcome = self._get_time_to_outcome(outcome_type)

            records.append({
                "student_id": sid,
                "academic_year_graduated": academic_year,
                "programme_code": student.get('program_code', student.get('programme_code')),
                "faculty": faculty,
                "degree_classification": degree_class,
                "degree_weighted_avg": weighted_avg,
                "outcome_type": outcome_type,
                "professional_level": professional_level,
                "employment_sector": employment_sector,
                "salary_band": salary_band,
                "time_to_outcome_months": time_to_outcome,
                "outcome_recorded_at": recorded_at,
            })

        return pd.DataFrame(records)
