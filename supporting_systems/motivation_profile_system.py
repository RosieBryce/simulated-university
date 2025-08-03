import yaml
import numpy as np
from typing import Dict, Any

class MotivationProfileSystem:
    """
    System to generate and nudge motivation profiles for students
    based on clan motivation ranges and individual personality traits.
    """
    def __init__(self, clan_spec_file: str = "config/clan_personality_specifications.yaml"):
        with open(clan_spec_file, 'r', encoding='utf-8') as f:
            self.clan_data = yaml.safe_load(f)["clans"]

    def sample_motivation_profile(self, clan_key: str) -> Dict[str, float]:
        """
        Sample a motivation profile for a student from their clan's motivation_dimensions ranges.
        """
        expected_dims = [
            'academic_drive', 'values_based_motivation', 'career_focus', 'cultural_experience',
            'personal_growth', 'social_connection', 'intellectual_curiosity', 'practical_skills'
        ]
        clan = self.clan_data[clan_key]
        motivation_ranges = clan.get("motivation_dimensions", {})
        profile = {}
        for dim in expected_dims:
            rng = motivation_ranges.get(dim, None)
            if rng is not None:
                profile[dim] = float(np.random.uniform(rng[0], rng[1]))
            else:
                print(f"WARNING: Clan '{clan_key}' missing motivation dimension '{dim}'. Using default 0.5.")
                profile[dim] = 0.5
        return profile

    def nudge_motivation_profile(self, profile: Dict[str, float], personality: Dict[str, float]) -> Dict[str, float]:
        """
        Nudge the motivation profile based on individual personality traits.
        """
        nudged = profile.copy()
        # Define nudging logic
        # Each nudge is a small adjustment (e.g., up to ±0.1)
        # Clamp to [0, 1]
        def clamp(x):
            return float(np.clip(x, 0.0, 1.0))

        # Academic drive
        nudged['academic_drive'] = clamp(
            nudged['academic_drive'] +
            0.10 * (personality.get('conscientiousness', 0.5) - 0.5) +
            0.10 * (personality.get('academic_curiosity', 0.5) - 0.5) +
            0.05 * (personality.get('perfectionism', 0.5) - 0.5)
        )
        # Values-based
        nudged['values_based_motivation'] = clamp(
            nudged['values_based_motivation'] +
            0.10 * (personality.get('agreeableness', 0.5) - 0.5) +
            0.10 * (personality.get('community_engagement', 0.5) - 0.5)
        )
        # Career focus
        nudged['career_focus'] = clamp(
            nudged['career_focus'] +
            0.10 * (personality.get('career_ambition', 0.5) - 0.5) +
            0.05 * (personality.get('conscientiousness', 0.5) - 0.5)
        )
        # Cultural experience
        nudged['cultural_experience'] = clamp(
            nudged['cultural_experience'] +
            0.10 * (personality.get('openness', 0.5) - 0.5) +
            0.05 * (personality.get('extraversion', 0.5) - 0.5)
        )
        # Personal growth
        nudged['personal_growth'] = clamp(
            nudged['personal_growth'] +
            0.10 * (personality.get('openness', 0.5) - 0.5) +
            0.05 * (personality.get('resilience', 0.5) - 0.5)
        )
        # Social connection
        nudged['social_connection'] = clamp(
            nudged['social_connection'] +
            0.10 * (personality.get('extraversion', 0.5) - 0.5) -
            0.10 * (personality.get('social_anxiety', 0.5) - 0.5)
        )
        # Intellectual curiosity
        nudged['intellectual_curiosity'] = clamp(
            nudged['intellectual_curiosity'] +
            0.10 * (personality.get('openness', 0.5) - 0.5) +
            0.10 * (personality.get('academic_curiosity', 0.5) - 0.5)
        )
        # Practical skills
        nudged['practical_skills'] = clamp(
            nudged['practical_skills'] +
            0.10 * (personality.get('conscientiousness', 0.5) - 0.5) +
            0.05 * (personality.get('perfectionism', 0.5) - 0.5)
        )
        return nudged

    def generate_student_motivation(self, clan_key: str, personality: Dict[str, float]) -> Dict[str, Any]:
        """
        Generate a motivation profile for a student, including both sampled and nudged values.
        """
        sampled = self.sample_motivation_profile(clan_key)
        nudged = self.nudge_motivation_profile(sampled, personality)
        return {
            'sampled': sampled,
            'nudged': nudged
        }

if __name__ == "__main__":
    # Demo/test
    system = MotivationProfileSystem()
    clan_key = 'malachite'
    # Example personality (mid-high conscientiousness, high academic curiosity, low extraversion)
    personality = {
        'openness': 0.7,
        'conscientiousness': 0.8,
        'extraversion': 0.3,
        'agreeableness': 0.6,
        'neuroticism': 0.3,
        'academic_curiosity': 0.9,
        'perfectionism': 0.7,
        'resilience': 0.6,
        'leadership_tendency': 0.5,
        'social_anxiety': 0.4,
        'extra_curricular_propensity': 0.6,
        'career_ambition': 0.7,
        'community_engagement': 0.8
    }
    result = system.generate_student_motivation(clan_key, personality)
    print(f"Sampled motivation profile for clan '{clan_key}':")
    for k, v in result['sampled'].items():
        print(f"  {k}: {v:.3f}")
    print("\nNudged motivation profile:")
    for k, v in result['nudged'].items():
        print(f"  {k}: {v:.3f}")