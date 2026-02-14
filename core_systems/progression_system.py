"""
Stonegrove University Progression System

Calculates pass/fail per module and per year; determines progression/repeat/withdrawal
for each student. Student-level decisions (emergent from marks + traits + motivation).
Uses config/year_progression_rules.yaml for base probabilities and modifiers.

Output: progression_outcomes.csv (student_id, academic_year, year_outcome, status, status_change_at)
"""

import pandas as pd
import numpy as np
import yaml
from pathlib import Path
from typing import Dict, Optional, Tuple


def _log_odds(p: float) -> float:
    """Convert probability to log-odds."""
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def _inv_log_odds(x: float) -> float:
    """Convert log-odds back to probability."""
    return 1.0 / (1.0 + np.exp(-x))


class ProgressionSystem:
    """
    Determines year outcomes (pass/fail) and next-year status (progress/repeat/withdraw)
    for each student based on assessment marks and student traits.
    """

    def __init__(self, seed: int = 42, config_path: str = "config/year_progression_rules.yaml"):
        self.seed = seed
        np.random.seed(seed)
        self.config = self._load_config(config_path)
        self.pass_threshold = self.config.get("pass_threshold", 40)

    def _load_config(self, config_path: str) -> dict:
        """Load progression rules from YAML."""
        path = Path(config_path)
        if not path.exists():
            return {
                "pass_threshold": 40,
                "base_progression_probability": 0.90,
                "base_withdrawal_after_pass": 0.10,
                "base_repeat_probability": 0.60,
                "base_withdrawal_after_fail": 0.40,
                "modifiers": {},
            }
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def _get_modifier(self, key: str, default: float = 0.0) -> float:
        mods = self.config.get("modifiers", {})
        return mods.get(key, default)

    def _has_significant_disability(self, student: pd.Series) -> bool:
        """True if student has significant burden: requires_personal_care, wheelchair, blind, communication difficulties, or 2+ disabilities."""
        raw = str(student.get("disabilities", "") or "").lower()
        if not raw or "no_known_disabilities" in raw:
            return False
        significant = [
            "requires_personal_care",
            "wheelchair_user",
            "blind_or_visually_impaired",
            "communication_difficulties",
        ]
        if any(d in raw for d in significant):
            return True
        # 2+ disabilities (comma-separated)
        parts = [p.strip() for p in raw.split(",") if p.strip() and "no_known" not in p]
        return len(parts) >= 2

    def _compute_year_outcome(self, student_marks: pd.Series) -> Tuple[bool, float]:
        """
        Determine pass/fail for the year.
        Pass = all modules >= pass_threshold.
        Returns (passed: bool, avg_mark: float).
        """
        marks = student_marks.dropna()
        if marks.empty:
            return False, 0.0
        all_pass = (marks >= self.pass_threshold).all()
        avg = float(marks.mean())
        return all_pass, avg

    def _apply_modifiers(
        self,
        base_prob: float,
        student: pd.Series,
        passed: bool,
        avg_mark: float,
        outcome_type: str,
    ) -> float:
        """
        Apply trait modifiers to base probability.
        outcome_type: 'progression', 'repeat', or 'withdrawal'
        """
        mods = self.config.get("modifiers", {})
        log_odds = _log_odds(base_prob)

        consc = float(student.get("refined_conscientiousness", 0.5))
        acad = float(student.get("motivation_academic_drive", 0.5))
        neur = float(student.get("refined_neuroticism", 0.5))

        # "Other stuff going on": significant disability, caring responsibilities
        significant_disability = self._has_significant_disability(student)
        caring = bool(student.get("caring_responsibilities", False)) if "caring_responsibilities" in student.index else False

        if outcome_type == "progression":
            log_odds += mods.get("conscientiousness_progression", 0) * (consc - 0.5) * 10
            log_odds += mods.get("academic_drive_progression", 0) * (acad - 0.5) * 10
            log_odds += mods.get("performance_progression", 0) * max(0, avg_mark - 50)
            if significant_disability:
                log_odds += mods.get("significant_disability_progression", 0)
            if caring:
                log_odds += mods.get("caring_responsibilities_progression", 0)
        elif outcome_type == "repeat":
            log_odds += mods.get("conscientiousness_repeat", 0) * (consc - 0.5) * 10
            log_odds += mods.get("academic_drive_repeat", 0) * (acad - 0.5) * 10
        elif outcome_type == "withdrawal":
            log_odds += mods.get("conscientiousness_withdrawal", 0) * (consc - 0.5) * 10
            log_odds += mods.get("academic_drive_withdrawal", 0) * (acad - 0.5) * 10
            log_odds += mods.get("neuroticism_withdrawal", 0) * (neur - 0.5) * 10
            log_odds += mods.get("performance_withdrawal", 0) * max(0, avg_mark - 50)
            if significant_disability:
                log_odds += mods.get("significant_disability_withdrawal", 0)
            if caring:
                log_odds += mods.get("caring_responsibilities_withdrawal", 0)

        return float(np.clip(_inv_log_odds(log_odds), 0.01, 0.99))

    def _decide_outcome(
        self,
        passed: bool,
        student: pd.Series,
        avg_mark: float,
    ) -> str:
        """
        Decide status for next year: 'enrolled' (progressed), 'repeating', or 'withdrawn'.
        """
        base_prog = self.config.get("base_progression_probability", 0.90)
        base_with_pass = self.config.get("base_withdrawal_after_pass", 0.10)
        base_rep = self.config.get("base_repeat_probability", 0.60)
        base_with_fail = self.config.get("base_withdrawal_after_fail", 0.40)

        if passed:
            p_progress = self._apply_modifiers(base_prog, student, True, avg_mark, "progression")
            p_withdraw = self._apply_modifiers(base_with_pass, student, True, avg_mark, "withdrawal")
            p_progress = p_progress * (1.0 - p_withdraw)  # normalize
            p_withdraw = p_withdraw
            p_repeat = 0.0
            total = p_progress + p_withdraw
            p_progress /= total
            p_withdraw /= total
            choices = ["enrolled", "withdrawn"]
            probs = [p_progress, p_withdraw]
        else:
            p_repeat = self._apply_modifiers(base_rep, student, False, avg_mark, "repeat")
            p_withdraw = self._apply_modifiers(base_with_fail, student, False, avg_mark, "withdrawal")
            total = p_repeat + p_withdraw
            p_repeat /= total
            p_withdraw /= total
            choices = ["repeating", "withdrawn"]
            probs = [p_repeat, p_withdraw]

        return str(np.random.choice(choices, p=probs))

    def compute_progression(
        self,
        assessment_df: pd.DataFrame,
        enrolled_df: pd.DataFrame,
        academic_year: str = "1046-47",
        status_change_at: str = "1047-09-01",
    ) -> pd.DataFrame:
        """
        Compute progression outcomes for all students.

        Args:
            assessment_df: stonegrove_assessment_events.csv
            enrolled_df: stonegrove_enrolled_students.csv (for traits)
            academic_year: current academic year
            status_change_at: date when new status takes effect (start of next year)

        Returns:
            DataFrame with: student_id, academic_year, year_outcome, status, status_change_at,
            programme_year (for next year), avg_mark, modules_passed, modules_total
        """
        if assessment_df.empty:
            return pd.DataFrame()

        # Aggregate marks per student
        agg = (
            assessment_df.groupby("student_id")
            .agg(
                avg_mark=("assessment_mark", "mean"),
                modules_total=("module_code", "nunique"),
                min_mark=("assessment_mark", "min"),
            )
            .reset_index()
        )
        agg["year_outcome"] = agg["min_mark"].apply(
            lambda m: "pass" if m >= self.pass_threshold else "fail"
        )
        passed_mask = assessment_df["assessment_mark"] >= self.pass_threshold
        modules_passed = assessment_df.assign(_passed=passed_mask).groupby("student_id")["_passed"].sum()
        agg["modules_passed"] = agg["student_id"].map(modules_passed).fillna(0).astype(int).values

        # Build student lookup for traits (enrolled has student_id as index or column)
        enrolled_df = enrolled_df.copy()
        if "student_id" not in enrolled_df.columns and enrolled_df.index.name != "student_id":
            enrolled_df["student_id"] = enrolled_df.index.astype(str)
        enrolled_df["student_id"] = enrolled_df["student_id"].astype(str)
        agg["student_id"] = agg["student_id"].astype(str)

        student_lookup = enrolled_df.set_index("student_id")

        # Merge programme_year from enrolled (needed for Year 3 graduation)
        if "programme_year" in enrolled_df.columns:
            prog_year_map = enrolled_df.drop_duplicates("student_id").set_index("student_id")["programme_year"].to_dict()
            agg["programme_year"] = agg["student_id"].map(lambda s: prog_year_map.get(s, 1))
        else:
            agg["programme_year"] = 1

        # Deduplicate columns to avoid Series values in row
        agg = agg.loc[:, ~agg.columns.duplicated()]

        records = []
        for row in agg.itertuples(index=False):
            sid = str(row.student_id)  # itertuples returns scalars, avoids Series
            passed = row.year_outcome == "pass"
            avg_mark = row.avg_mark
            programme_year = int(getattr(row, "programme_year", 1))

            student = student_lookup.loc[sid] if sid in student_lookup.index else pd.Series()

            # Year 3 pass → graduated (no roll)
            if programme_year == 3 and passed:
                status = "graduated"
            else:
                status = self._decide_outcome(passed, student, avg_mark)

            # programme_year for next year: 2 if progressed, 1 if repeating, None if withdrawn/graduated
            if status == "graduated":
                next_prog_year = None
            elif status == "enrolled":
                next_prog_year = programme_year + 1  # progressed to next year (1→2 or 2→3)
            elif status == "repeating":
                next_prog_year = programme_year  # same year, repeating
            else:
                next_prog_year = None  # withdrawn

            records.append({
                "student_id": sid,
                "academic_year": academic_year,
                "year_outcome": row.year_outcome,
                "status": status,
                "status_change_at": status_change_at,
                "programme_year_next": next_prog_year,
                "avg_mark": round(avg_mark, 2),
                "modules_passed": int(row.modules_passed),
                "modules_total": int(row.modules_total),
            })

        return pd.DataFrame(records)

    def run(
        self,
        assessment_path: str = "data/stonegrove_assessment_events.csv",
        enrolled_path: str = "data/stonegrove_enrolled_students.csv",
        output_path: str = "data/stonegrove_progression_outcomes.csv",
        academic_year: str = "1046-47",
        status_change_at: str = "1047-09-01",
    ) -> pd.DataFrame:
        """
        Load data, compute progression, save and return outcomes.
        """
        assessment_df = pd.read_csv(assessment_path)
        enrolled_df = pd.read_csv(enrolled_path)

        outcomes = self.compute_progression(
            assessment_df, enrolled_df, academic_year, status_change_at
        )

        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        outcomes.to_csv(out, index=False)
        return outcomes


def main():
    print("Stonegrove University Progression System")
    print("=" * 50)

    system = ProgressionSystem()
    outcomes = system.run()

    print(f"\nGenerated {len(outcomes)} progression outcomes")
    print(f"\nYear outcome distribution:")
    print(outcomes["year_outcome"].value_counts())
    print(f"\nStatus for next year:")
    print(outcomes["status"].value_counts())
    print(f"\nSample:")
    print(outcomes.head(10).to_string())


if __name__ == "__main__":
    main()
