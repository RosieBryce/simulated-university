"""
Enrolment Survey System — annual survey for all enrolled students.

One response per student per academic year. ~82% base response rate, nudged by
academic engagement (disengaged students slightly more likely to skip).

Constructs (1–5 integer Likert scale, higher = more of the construct):
  career_clarity, career_confidence          — career thinking
  belonging_peers, belonging_programme       — sense of belonging (U-shape Y1→Y3)
  academic_self_efficacy                     — belief in ability to succeed
  support_satisfaction                       — satisfaction with university support

Non-respondents remain in the table with NULL score columns (survey_responded=False).
is_repeat_year is derived from prior progression history.
"""

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class EnrolmentSurveySystem:
    def __init__(self, seed: int = 42):
        self.rng = np.random.default_rng(seed)
        self._cfg = self._load_config()

    # ------------------------------------------------------------------
    # Config
    # ------------------------------------------------------------------

    def _load_config(self) -> dict:
        cfg_path = PROJECT_ROOT / "config" / "enrolment_survey_config.yaml"
        with open(cfg_path) as f:
            return yaml.safe_load(f)

    # ------------------------------------------------------------------
    # Response probability
    # ------------------------------------------------------------------

    def _response_prob(self, academic_engagement: float) -> float:
        cfg = self._cfg["response"]
        base = cfg["base_rate"]
        mod = cfg["engagement_modifier"]
        # engagement in [0,1]: 0.5 neutral, higher boosts response
        shift = (academic_engagement - 0.5) * 2.0 * mod
        return float(np.clip(base + shift, 0.10, 0.98))

    # ------------------------------------------------------------------
    # Construct helpers
    # ------------------------------------------------------------------

    def _clip(self, v: float) -> float:
        s = self._cfg["scale"]
        return float(np.clip(v, s["min"], s["max"]))

    def _career_score(
        self,
        programme_year: int,
        career_prospects: float,
        conscientiousness: float,
        motivation_career: float,
        ses_rank: int,
    ) -> float:
        cfg = self._cfg["career"]
        mid = self._cfg["scale"]["mid"]
        arc = cfg["year_arc"].get(programme_year, 0.0)
        score = (
            mid
            + arc
            + career_prospects * cfg["career_prospects_weight"]
            + conscientiousness * cfg["conscientiousness_weight"]
            + motivation_career * cfg["motivation_career_development_weight"]
            + (ses_rank - 4.5) / 7.0 * cfg["ses_weight"]
            + self.rng.normal(0, cfg["noise_std"])
        )
        return self._clip(score)

    def _belonging_score(
        self,
        programme_year: int,
        social_engagement: float,
        extraversion: float,
        ses_rank: int,
        disabilities: list,
    ) -> float:
        cfg = self._cfg["belonging"]
        mid = self._cfg["scale"]["mid"]
        arc = cfg["year_arc"].get(programme_year, 0.0)
        disability_penalty = sum(
            cfg["disability_penalties"].get(d, 0.0) for d in disabilities
        )
        score = (
            mid
            + arc
            + social_engagement * cfg["social_engagement_weight"]
            + extraversion * cfg["extraversion_weight"]
            - (ses_rank - 1) / 7.0 * cfg["ses_weight"]   # lower SES → lower belonging
            + disability_penalty
            + self.rng.normal(0, cfg["noise_std"])
        )
        return self._clip(score)

    def _self_efficacy_score(
        self,
        programme_year: int,
        education: str,
        conscientiousness: float,
        resilience: float,
        first_gen: bool,
        prior_mark_norm: float | None,
    ) -> float:
        cfg = self._cfg["academic_self_efficacy"]
        mid = self._cfg["scale"]["mid"]
        edu_bonus = cfg["prior_education_scores"].get(education, 0.0)
        mark_contrib = (
            (prior_mark_norm or 0.0) * cfg["marks_weight"]
            if programme_year >= 2
            else 0.0
        )
        score = (
            mid
            + edu_bonus
            + conscientiousness * cfg["conscientiousness_weight"]
            + resilience * cfg["resilience_weight"]
            + mark_contrib
            + (cfg["first_gen_penalty"] if first_gen else 0.0)
            + self.rng.normal(0, cfg["noise_std"])
        )
        return self._clip(score)

    def _support_satisfaction_score(
        self,
        education: str,
        extraversion: float,
        academic_engagement: float,
        ses_rank: int,
        prior_mark_norm: float | None,
    ) -> float:
        cfg = self._cfg["support_satisfaction"]
        mid = self._cfg["scale"]["mid"]
        edu_bonus = cfg["prior_education_scores"].get(education, 0.0)
        score = (
            mid
            + edu_bonus
            + extraversion * cfg["extraversion_weight"]
            + academic_engagement * cfg["academic_engagement_weight"]
            - (ses_rank - 1) / 7.0 * cfg["ses_weight"]
            + (prior_mark_norm or 0.0) * cfg["marks_weight"]
            + self.rng.normal(0, cfg["noise_std"])
        )
        return self._clip(score)

    # ------------------------------------------------------------------
    # Engagement aggregation
    # ------------------------------------------------------------------

    @staticmethod
    def _aggregate_engagement(weekly_df: pd.DataFrame | None, academic_year: str) -> dict:
        """Return {student_id -> {metric: mean}} over this year's weekly engagement.

        Mirrors the NSS system: the enrolled dataframe carries no engagement columns,
        so the per-student aggregation must come from the weekly engagement frame.
        """
        if weekly_df is None or len(weekly_df) == 0:
            return {}
        df = weekly_df.copy()
        df["student_id"] = df["student_id"].astype(str)
        if "academic_year" in df.columns:
            df = df[df["academic_year"] == academic_year]
        eng_cols = [c for c in ["attendance_rate", "participation_score",
                                 "academic_engagement", "social_engagement", "stress_level"]
                    if c in df.columns]
        if df.empty or not eng_cols:
            return {}
        agg = df.groupby("student_id")[eng_cols].mean()
        return {sid: row.to_dict() for sid, row in agg.iterrows()}

    # ------------------------------------------------------------------
    # Prior-mark helper
    # ------------------------------------------------------------------

    @staticmethod
    def _get_prior_mark_norm(student_id: str, all_assessment_df: pd.DataFrame | None) -> float | None:
        """Mean mark from prior assessments for this student, normalised to [0,1]."""
        if all_assessment_df is None or len(all_assessment_df) == 0:
            return None
        rows = all_assessment_df[
            (all_assessment_df["student_id"].astype(str) == str(student_id))
            & (all_assessment_df.get("component_code", pd.Series(dtype=str)) == "FINAL")
        ]
        if len(rows) == 0:
            rows = all_assessment_df[
                all_assessment_df["student_id"].astype(str) == str(student_id)
            ]
        if len(rows) == 0:
            return None
        mark_col = "combined_mark" if "combined_mark" in rows.columns else "assessment_mark"
        mean_mark = rows[mark_col].dropna().mean()
        if pd.isna(mean_mark):
            return None
        return float(np.clip((mean_mark - 30.0) / 70.0, 0.0, 1.0))   # 30–100 → 0–1

    # ------------------------------------------------------------------
    # Career prospects lookup
    # ------------------------------------------------------------------

    def _load_career_prospects(self) -> dict:
        path = PROJECT_ROOT / "config" / "programme_characteristics.csv"
        if not path.exists():
            return {}
        df = pd.read_csv(path)
        if "programme_code" not in df.columns or "career_prospects" not in df.columns:
            return {}
        mn, mx = df["career_prospects"].min(), df["career_prospects"].max()
        if mx == mn:
            return {row["programme_code"]: 0.5 for _, row in df.iterrows()}
        return {
            row["programme_code"]: float((row["career_prospects"] - mn) / (mx - mn))
            for _, row in df.iterrows()
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_responses(
        self,
        enrolled_df: pd.DataFrame,
        academic_year: str,
        all_assessment_df: pd.DataFrame | None = None,
        weekly_engagement_df: pd.DataFrame | None = None,
    ) -> pd.DataFrame:
        """Generate enrolment survey responses for all enrolled students this year.

        Parameters
        ----------
        enrolled_df : DataFrame
            Combined enrolled students for this academic year (output of enrollment step).
        academic_year : str
            e.g. '1047-48'
        all_assessment_df : DataFrame, optional
            Accumulated assessment events (used for prior-mark normalisation in Y2+).
        weekly_engagement_df : DataFrame, optional
            This year's weekly engagement, aggregated per student to drive the response
            rate and the engagement terms in the belonging/support scores.
        """
        if enrolled_df is None or len(enrolled_df) == 0:
            return pd.DataFrame()

        career_prospects_map = self._load_career_prospects()
        eng_lookup = self._aggregate_engagement(weekly_engagement_df, academic_year)

        records = []
        for _, row in enrolled_df.iterrows():
            sid = str(row.get("student_id", ""))
            programme_year = int(row.get("programme_year", 1))
            # is_repeat_year reflects the student's status THIS year (matches NSS),
            # not whether they ever repeated in the past.
            is_repeat = str(row.get("status", "")).lower() == "repeating"

            # Per-student engagement (mean over the year's weekly records); fallback 0.5.
            eng_row = eng_lookup.get(sid, {})
            eng_cols = ["academic_engagement", "participation_score", "attendance_rate"]
            eng_vals = [eng_row[c] for c in eng_cols if c in eng_row and pd.notna(eng_row[c])]
            avg_eng = float(np.mean(eng_vals)) if eng_vals else 0.5

            # Response decision
            responded = bool(self.rng.random() < self._response_prob(avg_eng))

            rec = {
                "student_id": sid,
                "academic_year": academic_year,
                "programme_year": programme_year,
                "survey_responded": responded,
                "is_repeat_year": is_repeat,
                "career_clarity": None,
                "career_confidence": None,
                "belonging_peers": None,
                "belonging_programme": None,
                "academic_self_efficacy": None,
                "support_satisfaction": None,
            }

            if not responded:
                records.append(rec)
                continue

            # Trait lookups — try refined_ then base_ then 0.5
            def trait(name: str) -> float:
                for prefix in ("refined_", "base_", ""):
                    v = row.get(f"{prefix}{name}")
                    if v is not None and pd.notna(v):
                        return float(v)
                return 0.5

            conscientiousness = trait("conscientiousness")
            extraversion = trait("extraversion")
            resilience = trait("resilience")
            social_eng = float(eng_row.get("social_engagement", 0.5))

            # Motivation (generated dimension is career_focus)
            mot_career = float(row.get("motivation_career_focus") or 0.5)

            ses_rank = int(row.get("socio_economic_rank") or 4)
            education = str(row.get("education") or "academic")
            first_gen = bool(row.get("first_gen") or False)

            disabilities_raw = str(row.get("disabilities") or "no_known_disabilities")
            disabilities = [d.strip() for d in disabilities_raw.split(",")]

            # Enrolled dataframe uses program_code (single 'm'); config keys match.
            programme_code = str(row.get("program_code") or row.get("programme_code") or "")
            career_prospects = career_prospects_map.get(programme_code, 0.5)

            prior_mark_norm = self._get_prior_mark_norm(sid, all_assessment_df)

            # Score each construct (two items per construct, add small independent noise)
            cc1 = self._career_score(programme_year, career_prospects, conscientiousness, mot_career, ses_rank)
            cc2 = self._career_score(programme_year, career_prospects, conscientiousness, mot_career, ses_rank)

            bp1 = self._belonging_score(programme_year, social_eng, extraversion, ses_rank, disabilities)
            bp2 = self._belonging_score(programme_year, social_eng, extraversion, ses_rank, disabilities)

            se1 = self._self_efficacy_score(programme_year, education, conscientiousness, resilience, first_gen, prior_mark_norm)

            ss1 = self._support_satisfaction_score(education, extraversion, avg_eng, ses_rank, prior_mark_norm)

            rec.update({
                "career_clarity":         int(np.clip(round(cc1), 1, 5)),
                "career_confidence":      int(np.clip(round(cc2), 1, 5)),
                "belonging_peers":        int(np.clip(round(bp1), 1, 5)),
                "belonging_programme":    int(np.clip(round(bp2), 1, 5)),
                "academic_self_efficacy": int(np.clip(round(se1), 1, 5)),
                "support_satisfaction":   int(np.clip(round(ss1), 1, 5)),
            })
            records.append(rec)

        return pd.DataFrame(records)
