import yaml
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class ProgramAffinity:
    """Container for program affinity data"""
    program_name: str
    affinity_score: float
    affinity_level: str

class ProgramAffinitySystem:
    """
    Program affinity system for Stonegrove University.
    Determines program preferences based on clan characteristics.
    """
    
    def __init__(self, config_file: str = "config/clan_program_affinities.yaml"):
        """Initialize the program affinity system"""
        self.config_file = config_file
        self.affinity_data = self._load_affinity_data()
        self.settings = self.affinity_data.get('settings', {})
        
    def _load_affinity_data(self) -> Dict:
        """Load program affinity data from YAML configuration"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"Program affinity configuration file not found: {self.config_file}")
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing program affinity YAML: {e}")
    
    def _get_clan_affinities(self, clan_key: str) -> Dict[str, float]:
        """Get program affinities for a specific clan"""
        clans = self.affinity_data.get('clans', {})
        if clan_key not in clans:
            raise ValueError(f"Clan '{clan_key}' not found in program affinity data")
        
        clan_data = clans[clan_key]
        return clan_data.get('program_affinities', {})
    
    def _get_affinity_level(self, affinity_score: float) -> str:
        """Determine affinity level based on score"""
        affinity_levels = self.settings.get('affinity_levels', {})
        
        for level, (min_score, max_score) in affinity_levels.items():
            if min_score <= affinity_score <= max_score:
                return level
        
        return "minimal"  # Default fallback
    
    def get_clan_program_affinities(self, clan_key: str) -> List[ProgramAffinity]:
        """
        Get all program affinities for a specific clan.
        
        Args:
            clan_key: The clan identifier (e.g., 'malachite', 'baobab')
        
        Returns:
            List of ProgramAffinity objects sorted by affinity score (highest first)
        """
        affinities = self._get_clan_affinities(clan_key)
        
        program_affinities = []
        for program_name, affinity_score in affinities.items():
            affinity_level = self._get_affinity_level(affinity_score)
            program_affinities.append(ProgramAffinity(
                program_name=program_name,
                affinity_score=affinity_score,
                affinity_level=affinity_level
            ))
        
        # Sort by affinity score (highest first)
        program_affinities.sort(key=lambda x: x.affinity_score, reverse=True)
        return program_affinities
    
    def get_top_programs_for_clan(self, clan_key: str, num_programs: int = 5) -> List[ProgramAffinity]:
        """
        Get the top N programs for a specific clan.
        
        Args:
            clan_key: The clan identifier
            num_programs: Number of top programs to return
        
        Returns:
            List of top ProgramAffinity objects
        """
        all_affinities = self.get_clan_program_affinities(clan_key)
        return all_affinities[:num_programs]
    
    def calculate_program_selection_probabilities(self, clan_key: str) -> Dict[str, float]:
        """
        Calculate program selection probabilities for a clan based on affinity scores.
        
        Args:
            clan_key: The clan identifier
        
        Returns:
            Dictionary mapping program names to selection probabilities
        """
        affinities = self._get_clan_affinities(clan_key)
        selection_rules = self.settings.get('selection_rules', {})
        
        # Get base probability and multipliers
        base_prob = selection_rules.get('base_selection_probability', 0.3)
        multipliers = selection_rules.get('affinity_multipliers', {})
        min_threshold = selection_rules.get('minimum_affinity_threshold', 0.05)
        
        probabilities = {}
        
        for program_name, affinity_score in affinities.items():
            # Skip programs below minimum threshold
            if affinity_score < min_threshold:
                probabilities[program_name] = 0.0
                continue
            
            # Determine affinity level and get multiplier
            affinity_level = self._get_affinity_level(affinity_score)
            multiplier = multipliers.get(affinity_level, 1.0)
            
            # Calculate probability
            probability = base_prob * multiplier * affinity_score
            
            # Cap probability at 1.0
            probability = min(probability, 1.0)
            
            probabilities[program_name] = probability
        
        return probabilities
    
    def select_program_for_student(self, clan_key: str, personality_modifiers: Optional[Dict] = None) -> str:
        """
        Select a program for a student based on clan affinities and optional personality modifiers.
        
        Args:
            clan_key: The clan identifier
            personality_modifiers: Optional dictionary of personality traits that might influence selection
        
        Returns:
            Selected program name
        """
        probabilities = self.calculate_program_selection_probabilities(clan_key)
        
        # Apply personality modifiers if provided
        if personality_modifiers:
            probabilities = self._apply_personality_modifiers(probabilities, personality_modifiers)
        
        # Remove programs with zero probability
        valid_programs = {prog: prob for prog, prob in probabilities.items() if prob > 0}
        
        if not valid_programs:
            raise ValueError(f"No valid programs found for clan '{clan_key}'")
        
        # Normalize probabilities
        total_prob = sum(valid_programs.values())
        if total_prob == 0:
            # If all probabilities are 0, use uniform distribution
            programs = list(valid_programs.keys())
            return np.random.choice(programs)
        
        normalized_probs = {prog: prob / total_prob for prog, prob in valid_programs.items()}
        
        # Select program
        programs = list(normalized_probs.keys())
        probs = list(normalized_probs.values())
        
        return np.random.choice(programs, p=probs)
    
    def _apply_personality_modifiers(self, probabilities: Dict[str, float], personality: Dict) -> Dict[str, float]:
        """
        Apply personality-based modifiers to program selection probabilities.
        
        Args:
            probabilities: Base program selection probabilities
            personality: Dictionary of personality traits
        
        Returns:
            Modified probabilities
        """
        modified_probs = probabilities.copy()
        
        # Example personality modifiers (can be expanded)
        if 'openness' in personality:
            openness = personality['openness']
            # High openness increases probability of creative/theoretical programs
            creative_programs = [
                "Knowledge System Prototyping",
                "Embodied Research Methods", 
                "Storyweaving & Community Histories",
                "Multispecies Semantics"
            ]
            for program in creative_programs:
                if program in modified_probs:
                    modified_probs[program] *= (1 + openness * 0.5)
        
        if 'conscientiousness' in personality:
            conscientiousness = personality['conscientiousness']
            # High conscientiousness increases probability of structured programs
            structured_programs = [
                "Strategic Rituals and Civic Memory",
                "Ancient Tongues and Translation",
                "Comparative Runes and Scripts",
                "Runic Infrastructure"
            ]
            for program in structured_programs:
                if program in modified_probs:
                    modified_probs[program] *= (1 + conscientiousness * 0.3)
        
        if 'extraversion' in personality:
            extraversion = personality['extraversion']
            # High extraversion increases probability of social programs
            social_programs = [
                "Listening Circles Facilitation",
                "Mediation",
                "Hospitality as Praxis",
                "Intergenerational Learning"
            ]
            for program in social_programs:
                if program in modified_probs:
                    modified_probs[program] *= (1 + extraversion * 0.4)
        
        return modified_probs
    
    def get_available_clans(self) -> List[str]:
        """Get list of available clan keys"""
        return list(self.affinity_data.get('clans', {}).keys())
    
    def get_clan_name(self, clan_key: str) -> str:
        """Get the display name for a clan"""
        clans = self.affinity_data.get('clans', {})
        if clan_key not in clans:
            return clan_key
        
        return clans[clan_key].get('name', clan_key)
    
    def get_all_programs(self) -> List[str]:
        """Get list of all available programs"""
        programs = set()
        clans = self.affinity_data.get('clans', {})
        
        for clan_data in clans.values():
            clan_programs = clan_data.get('program_affinities', {})
            programs.update(clan_programs.keys())
        
        return sorted(list(programs))
    
    def validate_affinity_data(self) -> bool:
        """Validate that all affinity data is properly configured"""
        try:
            clans = self.affinity_data.get('clans', {})
            
            for clan_key, clan_data in clans.items():
                # Check that program affinities exist
                affinities = clan_data.get('program_affinities', {})
                if not affinities:
                    print(f"Warning: Clan '{clan_key}' has no program affinities")
                    return False
                
                # Check that affinity scores are valid
                for program, score in affinities.items():
                    if not isinstance(score, (int, float)) or score < 0 or score > 1:
                        print(f"Warning: Invalid affinity score for clan '{clan_key}', program '{program}': {score}")
                        return False
            
            return True
            
        except Exception as e:
            print(f"Error validating affinity data: {e}")
            return False

def main():
    """Test the program affinity system"""
    print("🎓 Stonegrove University Program Affinity System")
    print("=" * 60)
    
    # Initialize system
    affinity_system = ProgramAffinitySystem()
    
    # Validate configuration
    if not affinity_system.validate_affinity_data():
        print("❌ Program affinity validation failed!")
        return
    
    print("✅ Program affinity validation passed!")
    print(f"📚 Available clans: {', '.join(affinity_system.get_available_clans())}")
    print(f"🎯 Total programs: {len(affinity_system.get_all_programs())}")
    print()
    
    # Test affinity retrieval for each clan
    print("🎲 Testing program affinities for each clan:")
    print("-" * 60)
    
    for clan_key in affinity_system.get_available_clans():
        clan_name = affinity_system.get_clan_name(clan_key)
        print(f"\n🏛️ {clan_name} ({clan_key}):")
        
        # Get top 5 programs
        top_programs = affinity_system.get_top_programs_for_clan(clan_key, 5)
        for i, program in enumerate(top_programs, 1):
            print(f"  {i}. {program.program_name} (Score: {program.affinity_score:.2f}, Level: {program.affinity_level})")
    
    # Test program selection
    print("\n" + "=" * 60)
    print("📊 Testing program selection:")
    print("-" * 60)
    
    # Test selection for a few clans
    test_clans = ['malachite', 'baobab', 'flint', 'rowan']
    
    for clan_key in test_clans:
        clan_name = affinity_system.get_clan_name(clan_key)
        print(f"\n🎯 {clan_name} ({clan_key}):")
        
        # Test multiple selections
        for i in range(3):
            try:
                selected_program = affinity_system.select_program_for_student(clan_key)
                print(f"  Selection {i+1}: {selected_program}")
            except Exception as e:
                print(f"  Selection {i+1}: Error - {e}")
    
    # Test with personality modifiers
    print("\n" + "=" * 60)
    print("🧠 Testing program selection with personality modifiers:")
    print("-" * 60)
    
    test_personality = {
        'openness': 0.8,        # High openness
        'conscientiousness': 0.6,  # Moderate conscientiousness
        'extraversion': 0.3      # Low extraversion
    }
    
    for clan_key in test_clans[:2]:  # Test with first 2 clans
        clan_name = affinity_system.get_clan_name(clan_key)
        print(f"\n🧠 {clan_name} with personality modifiers:")
        
        for i in range(3):
            try:
                selected_program = affinity_system.select_program_for_student(
                    clan_key, personality_modifiers=test_personality
                )
                print(f"  Selection {i+1}: {selected_program}")
            except Exception as e:
                print(f"  Selection {i+1}: Error - {e}")
    
    print(f"\n✅ Program affinity system test completed!")

if __name__ == "__main__":
    main() 