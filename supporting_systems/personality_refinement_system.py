import yaml
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

CONFIG_PATH = Path("config/personality_refinement_modifiers.yaml")


@dataclass
class PersonalityRefinement:
    """Container for personality refinement data"""
    base_personality: Dict[str, float]
    refined_personality: Dict[str, float]
    applied_modifiers: Dict[str, Dict[str, float]]
    characteristics: Dict[str, any]


class PersonalityRefinementSystem:
    """
    Personality refinement system for Stonegrove University.
    Takes base personality and applies characteristic-based modifiers.
    All modifier values are loaded from config/personality_refinement_modifiers.yaml.
    Disability modifiers are per-clan: defaults apply unless the clan has an override
    for that disability (in which case only the overridden traits are replaced).
    """

    def __init__(self, config_path: str = None):
        path = Path(config_path) if config_path else CONFIG_PATH
        with open(path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)

        self._disability_defaults = cfg["disability_modifiers"]["defaults"]
        self._disability_clan_overrides = cfg["disability_modifiers"].get("clan_overrides", {})
        self._socio_economic_modifiers = cfg["socio_economic_modifiers"]
        self._education_modifiers = cfg["education_modifiers"]
        self._age_modifiers = cfg["age_modifiers"]

    def _get_disability_modifier(self, disability: str, clan: str = "") -> Dict[str, float]:
        """
        Return trait adjustments for a disability, merged with any clan-specific overrides.
        Clan overrides only replace the traits they specify; everything else stays default.
        """
        defaults = dict(self._disability_defaults.get(disability, {}))
        if clan and clan in self._disability_clan_overrides:
            clan_dis = self._disability_clan_overrides[clan].get(disability, {})
            defaults.update(clan_dis)  # clan values replace defaults where present
        return defaults

    def refine_personality(
        self,
        base_personality: Dict[str, float],
        characteristics: Dict,
    ) -> PersonalityRefinement:
        """
        Refine base personality based on student characteristics.

        Args:
            base_personality: Base personality traits (0–1 scale)
            characteristics: Dict with keys: disabilities, socio_economic_rank,
                             education, age, clan (optional)

        Returns:
            PersonalityRefinement with refined personality and applied modifiers
        """
        refined = base_personality.copy()
        applied = {}
        clan = str(characteristics.get("clan", "")).lower()

        def _apply(modifier: Dict[str, float], label: str):
            applied[label] = modifier
            for trait, adj in modifier.items():
                if trait in refined:
                    refined[trait] = float(np.clip(refined[trait] + adj, 0.0, 1.0))

        # Disability modifiers (per-clan aware)
        for disability in characteristics.get("disabilities", []):
            mod = self._get_disability_modifier(disability, clan)
            if mod:
                _apply(mod, f"disability_{disability}")

        # Socio-economic modifiers
        rank = characteristics.get("socio_economic_rank")
        if rank is not None:
            if rank <= 2:
                _apply(self._socio_economic_modifiers["high_class"], "socio_economic_high")
            elif rank >= 7:
                _apply(self._socio_economic_modifiers["low_class"], "socio_economic_low")
            else:
                _apply(self._socio_economic_modifiers["middle_class"], "socio_economic_middle")

        # Education modifiers
        education = characteristics.get("education")
        if education and education in self._education_modifiers:
            _apply(self._education_modifiers[education], f"education_{education}")

        # Age modifiers
        age = characteristics.get("age")
        if age is not None:
            if age <= 19:
                _apply(self._age_modifiers["young"], "age_young")
            elif age >= 23:
                _apply(self._age_modifiers["older"], "age_older")
            else:
                _apply(self._age_modifiers["mature"], "age_mature")

        return PersonalityRefinement(
            base_personality=base_personality,
            refined_personality=refined,
            applied_modifiers=applied,
            characteristics=characteristics,
        )
