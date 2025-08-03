import yaml
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass

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
    """
    
    def __init__(self):
        """Initialize the personality refinement system"""
        self.disability_modifiers = self._load_disability_modifiers()
        self.socio_economic_modifiers = self._load_socio_economic_modifiers()
        self.education_modifiers = self._load_education_modifiers()
        self.age_modifiers = self._load_age_modifiers()
        
    def _load_disability_modifiers(self) -> Dict:
        """Load disability-based personality modifiers"""
        return {
            'autistic_spectrum': {
                'openness': 0.0,           # No change
                'conscientiousness': 0.1,  # +10% - attention to detail
                'extraversion': -0.2,      # -20% - more introverted
                'agreeableness': 0.0,      # No change
                'neuroticism': 0.0,        # No change
                'academic_curiosity': 0.15, # +15% - deep interests
                'perfectionism': 0.2,      # +20% - attention to detail
                'resilience': 0.0,         # No change
                'leadership_tendency': -0.1, # -10% - less leadership
                'social_anxiety': 0.2,     # +20% - social challenges
                'extra_curricular_propensity': -0.1, # -10% - less social activities
                'career_ambition': 0.0,    # No change
                'community_engagement': -0.1 # -10% - less community involvement
            },
            'adhd': {
                'openness': 0.1,           # +10% - creative thinking
                'conscientiousness': -0.15, # -15% - organization challenges
                'extraversion': 0.1,       # +10% - more outgoing
                'agreeableness': 0.0,      # No change
                'neuroticism': 0.1,        # +10% - frustration
                'academic_curiosity': 0.1,  # +10% - interest in many things
                'perfectionism': -0.15,    # -15% - less perfectionist
                'resilience': 0.0,         # No change
                'leadership_tendency': 0.0, # No change
                'social_anxiety': -0.1,    # -10% - less social anxiety
                'extra_curricular_propensity': 0.1, # +10% - high energy
                'career_ambition': 0.0,    # No change
                'community_engagement': 0.0 # No change
            },
            'mental_health_disability': {
                'openness': -0.1,          # -10% - less open to new experiences
                'conscientiousness': -0.1, # -10% - organization challenges
                'extraversion': -0.2,      # -20% - more withdrawn
                'agreeableness': 0.0,      # No change
                'neuroticism': 0.3,        # +30% - higher anxiety/depression
                'academic_curiosity': -0.1, # -10% - reduced motivation
                'perfectionism': 0.1,      # +10% - perfectionism as coping
                'resilience': -0.2,        # -20% - reduced resilience
                'leadership_tendency': -0.2, # -20% - less leadership
                'social_anxiety': 0.3,     # +30% - higher social anxiety
                'extra_curricular_propensity': -0.2, # -20% - less participation
                'career_ambition': -0.1,   # -10% - reduced ambition
                'community_engagement': -0.2 # -20% - less engagement
            },
            'physical_disability': {
                'openness': 0.0,           # No change
                'conscientiousness': 0.0,  # No change
                'extraversion': 0.0,       # No change
                'agreeableness': 0.0,      # No change
                'neuroticism': 0.1,        # +10% - some stress
                'academic_curiosity': 0.0,  # No change
                'perfectionism': 0.0,      # No change
                'resilience': 0.2,         # +20% - adaptation builds resilience
                'leadership_tendency': 0.0, # No change
                'social_anxiety': -0.1,    # -10% - adaptation reduces anxiety
                'extra_curricular_propensity': -0.1, # -10% - accessibility challenges
                'career_ambition': 0.0,    # No change
                'community_engagement': 0.0 # No change
            },
            'specific_learning_disability': {
                'openness': 0.0,           # No change
                'conscientiousness': -0.1, # -10% - organization challenges
                'extraversion': 0.0,       # No change
                'agreeableness': 0.0,      # No change
                'neuroticism': 0.1,        # +10% - frustration
                'academic_curiosity': -0.1, # -10% - reduced confidence
                'perfectionism': 0.1,      # +10% - overcompensation
                'resilience': 0.1,         # +10% - builds resilience
                'leadership_tendency': -0.1, # -10% - reduced confidence
                'social_anxiety': 0.1,     # +10% - academic anxiety
                'extra_curricular_propensity': 0.0, # No change
                'career_ambition': -0.1,   # -10% - reduced confidence
                'community_engagement': 0.0 # No change
            },
            'dyslexia': {
                'openness': 0.0,           # No change
                'conscientiousness': -0.05, # -5% - mild organization challenges
                'extraversion': 0.0,       # No change
                'agreeableness': 0.0,      # No change
                'neuroticism': 0.05,       # +5% - mild frustration
                'academic_curiosity': -0.05, # -5% - mild confidence issues
                'perfectionism': 0.1,      # +10% - overcompensation
                'resilience': 0.1,         # +10% - builds resilience
                'leadership_tendency': 0.0, # No change
                'social_anxiety': 0.05,    # +5% - mild academic anxiety
                'extra_curricular_propensity': 0.0, # No change
                'career_ambition': 0.0,    # No change
                'community_engagement': 0.0 # No change
            },
            'communication_difficulties': {
                'openness': 0.0,           # No change
                'conscientiousness': 0.0,  # No change
                'extraversion': -0.15,     # -15% - communication challenges
                'agreeableness': 0.0,      # No change
                'neuroticism': 0.1,        # +10% - frustration
                'academic_curiosity': 0.0,  # No change
                'perfectionism': 0.0,      # No change
                'resilience': 0.1,         # +10% - builds resilience
                'leadership_tendency': -0.15, # -15% - communication challenges
                'social_anxiety': 0.2,     # +20% - social anxiety
                'extra_curricular_propensity': -0.1, # -10% - communication challenges
                'career_ambition': -0.1,   # -10% - reduced confidence
                'community_engagement': -0.1 # -10% - communication challenges
            }
        }
    
    def _load_socio_economic_modifiers(self) -> Dict:
        """Load socio-economic-based personality modifiers"""
        return {
            'high_class': {  # Ranks 1-2
                'openness': 0.1,           # +10% - exposure to new ideas
                'conscientiousness': 0.0,  # No change
                'extraversion': 0.1,       # +10% - confidence
                'agreeableness': 0.0,      # No change
                'neuroticism': -0.1,       # -10% - less stress
                'academic_curiosity': 0.15, # +15% - educational privilege
                'perfectionism': 0.1,      # +10% - high standards
                'resilience': -0.1,        # -10% - less adversity
                'leadership_tendency': 0.1, # +10% - leadership opportunities
                'social_anxiety': -0.1,    # -10% - confidence
                'extra_curricular_propensity': 0.1, # +10% - resources
                'career_ambition': 0.15,   # +15% - high expectations
                'community_engagement': 0.0 # No change
            },
            'middle_class': {  # Ranks 3-6
                'openness': 0.0,           # No change
                'conscientiousness': 0.0,  # No change
                'extraversion': 0.0,       # No change
                'agreeableness': 0.0,      # No change
                'neuroticism': 0.0,        # No change
                'academic_curiosity': 0.0,  # No change
                'perfectionism': 0.0,      # No change
                'resilience': 0.0,         # No change
                'leadership_tendency': 0.0, # No change
                'social_anxiety': 0.0,     # No change
                'extra_curricular_propensity': 0.0, # No change
                'career_ambition': 0.0,    # No change
                'community_engagement': 0.0 # No change
            },
            'low_class': {  # Ranks 7-8
                'openness': -0.05,         # -5% - limited exposure
                'conscientiousness': 0.0,  # No change
                'extraversion': -0.05,     # -5% - less confidence
                'agreeableness': 0.0,      # No change
                'neuroticism': 0.1,        # +10% - stress
                'academic_curiosity': -0.1, # -10% - limited educational access
                'perfectionism': -0.05,    # -5% - realistic standards
                'resilience': 0.15,        # +15% - builds resilience
                'leadership_tendency': -0.05, # -5% - fewer opportunities
                'social_anxiety': 0.1,     # +10% - less confidence
                'extra_curricular_propensity': -0.1, # -10% - limited resources
                'career_ambition': -0.1,   # -10% - realistic expectations
                'community_engagement': 0.1 # +10% - community support
            }
        }
    
    def _load_education_modifiers(self) -> Dict:
        """Load education-based personality modifiers"""
        return {
            'academic': {
                'openness': 0.1,           # +10% - exposure to ideas
                'conscientiousness': 0.1,  # +10% - study habits
                'extraversion': 0.0,       # No change
                'agreeableness': 0.0,      # No change
                'neuroticism': 0.0,        # No change
                'academic_curiosity': 0.2,  # +20% - proven interest
                'perfectionism': 0.1,      # +10% - academic standards
                'resilience': 0.0,         # No change
                'leadership_tendency': 0.1, # +10% - academic leadership
                'social_anxiety': -0.05,   # -5% - academic confidence
                'extra_curricular_propensity': 0.1, # +10% - academic activities
                'career_ambition': 0.1,    # +10% - academic success
                'community_engagement': 0.0 # No change
            },
            'vocational': {
                'openness': 0.0,           # No change
                'conscientiousness': 0.1,  # +10% - practical skills
                'extraversion': 0.0,       # No change
                'agreeableness': 0.0,      # No change
                'neuroticism': 0.0,        # No change
                'academic_curiosity': 0.05, # +5% - some interest
                'perfectionism': 0.05,     # +5% - practical standards
                'resilience': 0.1,         # +10% - practical experience
                'leadership_tendency': 0.05, # +5% - practical leadership
                'social_anxiety': 0.0,     # No change
                'extra_curricular_propensity': 0.0, # No change
                'career_ambition': 0.05,   # +5% - practical goals
                'community_engagement': 0.05 # +5% - practical engagement
            },
            'no_qualifications': {
                'openness': -0.05,         # -5% - limited exposure
                'conscientiousness': 0.0,  # No change
                'extraversion': 0.0,       # No change
                'agreeableness': 0.0,      # No change
                'neuroticism': 0.05,       # +5% - academic anxiety
                'academic_curiosity': -0.1, # -10% - no proven interest
                'perfectionism': -0.05,    # -5% - realistic standards
                'resilience': 0.1,         # +10% - life experience
                'leadership_tendency': -0.05, # -5% - less academic confidence
                'social_anxiety': 0.1,     # +10% - academic anxiety
                'extra_curricular_propensity': -0.05, # -5% - less academic
                'career_ambition': -0.05,  # -5% - realistic expectations
                'community_engagement': 0.05 # +5% - community support
            }
        }
    
    def _load_age_modifiers(self) -> Dict:
        """Load age-based personality modifiers"""
        return {
            'young': {  # 18-19
                'openness': 0.1,           # +10% - young and open
                'conscientiousness': -0.05, # -5% - less mature
                'extraversion': 0.1,       # +10% - social energy
                'agreeableness': 0.0,      # No change
                'neuroticism': 0.05,       # +5% - young anxiety
                'academic_curiosity': 0.05, # +5% - new to university
                'perfectionism': -0.05,    # -5% - less mature
                'resilience': -0.05,       # -5% - less life experience
                'leadership_tendency': -0.05, # -5% - less mature
                'social_anxiety': 0.1,     # +10% - new environment
                'extra_curricular_propensity': 0.1, # +10% - social energy
                'career_ambition': 0.05,   # +5% - new opportunities
                'community_engagement': 0.05 # +5% - new community
            },
            'mature': {  # 20-22
                'openness': 0.0,           # No change
                'conscientiousness': 0.05, # +5% - more mature
                'extraversion': 0.0,       # No change
                'agreeableness': 0.0,      # No change
                'neuroticism': 0.0,        # No change
                'academic_curiosity': 0.0,  # No change
                'perfectionism': 0.05,     # +5% - more mature
                'resilience': 0.05,        # +5% - more experience
                'leadership_tendency': 0.05, # +5% - more mature
                'social_anxiety': 0.0,     # No change
                'extra_curricular_propensity': 0.0, # No change
                'career_ambition': 0.0,    # No change
                'community_engagement': 0.0 # No change
            },
            'older': {  # 23-25
                'openness': -0.05,         # -5% - more settled
                'conscientiousness': 0.1,  # +10% - more mature
                'extraversion': -0.05,     # -5% - more settled
                'agreeableness': 0.0,      # No change
                'neuroticism': -0.05,      # -5% - more stable
                'academic_curiosity': 0.05, # +5% - focused interest
                'perfectionism': 0.1,      # +10% - more mature
                'resilience': 0.1,         # +10% - more experience
                'leadership_tendency': 0.1, # +10% - more mature
                'social_anxiety': -0.05,   # -5% - more confident
                'extra_curricular_propensity': -0.05, # -5% - more focused
                'career_ambition': 0.1,    # +10% - more focused
                'community_engagement': 0.05 # +5% - more mature
            }
        }
    
    def refine_personality(self, base_personality: Dict[str, float], characteristics: Dict) -> PersonalityRefinement:
        """
        Refine base personality based on student characteristics.
        
        Args:
            base_personality: Base personality traits (0-1 scale)
            characteristics: Student characteristics including disabilities, socio-economic, education, age
        
        Returns:
            PersonalityRefinement object with refined personality and applied modifiers
        """
        refined_personality = base_personality.copy()
        applied_modifiers = {}
        
        # Apply disability modifiers
        if 'disabilities' in characteristics:
            for disability in characteristics['disabilities']:
                if disability in self.disability_modifiers:
                    modifier = self.disability_modifiers[disability]
                    applied_modifiers[f'disability_{disability}'] = modifier
                    
                    for trait, adjustment in modifier.items():
                        if trait in refined_personality:
                            refined_personality[trait] = np.clip(
                                refined_personality[trait] + adjustment,
                                0.0, 1.0
                            )
        
        # Apply socio-economic modifiers
        if 'socio_economic_rank' in characteristics:
            rank = characteristics['socio_economic_rank']
            if rank <= 2:
                modifier = self.socio_economic_modifiers['high_class']
                applied_modifiers['socio_economic_high'] = modifier
            elif rank >= 7:
                modifier = self.socio_economic_modifiers['low_class']
                applied_modifiers['socio_economic_low'] = modifier
            else:
                modifier = self.socio_economic_modifiers['middle_class']
                applied_modifiers['socio_economic_middle'] = modifier
            
            for trait, adjustment in modifier.items():
                if trait in refined_personality:
                    refined_personality[trait] = np.clip(
                        refined_personality[trait] + adjustment,
                        0.0, 1.0
                    )
        
        # Apply education modifiers
        if 'education' in characteristics:
            education = characteristics['education']
            if education in self.education_modifiers:
                modifier = self.education_modifiers[education]
                applied_modifiers[f'education_{education}'] = modifier
                
                for trait, adjustment in modifier.items():
                    if trait in refined_personality:
                        refined_personality[trait] = np.clip(
                            refined_personality[trait] + adjustment,
                            0.0, 1.0
                        )
        
        # Apply age modifiers
        if 'age' in characteristics:
            age = characteristics['age']
            if age <= 19:
                modifier = self.age_modifiers['young']
                applied_modifiers['age_young'] = modifier
            elif age >= 23:
                modifier = self.age_modifiers['older']
                applied_modifiers['age_older'] = modifier
            else:
                modifier = self.age_modifiers['mature']
                applied_modifiers['age_mature'] = modifier
            
            for trait, adjustment in modifier.items():
                if trait in refined_personality:
                    refined_personality[trait] = np.clip(
                        refined_personality[trait] + adjustment,
                        0.0, 1.0
                    )
        
        return PersonalityRefinement(
            base_personality=base_personality,
            refined_personality=refined_personality,
            applied_modifiers=applied_modifiers,
            characteristics=characteristics
        )

def main():
    """Test the personality refinement system"""
    print("🧠 Stonegrove University Personality Refinement System")
    print("=" * 60)
    
    # Initialize system
    system = PersonalityRefinementSystem()
    
    # Sample base personality (from clan)
    base_personality = {
        'openness': 0.7,
        'conscientiousness': 0.6,
        'extraversion': 0.4,
        'agreeableness': 0.8,
        'neuroticism': 0.3,
        'academic_curiosity': 0.8,
        'perfectionism': 0.6,
        'resilience': 0.7,
        'leadership_tendency': 0.5,
        'social_anxiety': 0.4,
        'extra_curricular_propensity': 0.6,
        'career_ambition': 0.5,
        'community_engagement': 0.7
    }
    
    # Sample characteristics
    characteristics = {
        'disabilities': ['autistic_spectrum', 'dyslexia'],
        'socio_economic_rank': 7,  # Low class
        'education': 'no_qualifications',
        'age': 18
    }
    
    print("👤 Base personality (from clan):")
    for trait, value in base_personality.items():
        print(f"   {trait}: {value:.3f}")
    
    print(f"\n📋 Student characteristics:")
    print(f"   Disabilities: {characteristics['disabilities']}")
    print(f"   Socio-economic rank: {characteristics['socio_economic_rank']}")
    print(f"   Education: {characteristics['education']}")
    print(f"   Age: {characteristics['age']}")
    
    # Apply refinement
    refinement = system.refine_personality(base_personality, characteristics)
    
    print(f"\n🔧 Applied modifiers:")
    for modifier_name, modifier_values in refinement.applied_modifiers.items():
        print(f"\n   {modifier_name}:")
        for trait, adjustment in modifier_values.items():
            if adjustment != 0:
                print(f"     {trait}: {adjustment:+.3f}")
    
    print(f"\n✨ Refined personality:")
    for trait in base_personality.keys():
        base_val = refinement.base_personality[trait]
        refined_val = refinement.refined_personality[trait]
        change = refined_val - base_val
        print(f"   {trait}: {base_val:.3f} → {refined_val:.3f} ({change:+.3f})")
    
    print(f"\n✅ Personality refinement completed!")

if __name__ == "__main__":
    main() 