import yaml
import random
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class GeneratedName:
    """Container for a generated name with metadata"""
    forename: str
    surname: str
    gender: str
    clan: str
    full_name: str

class ClanNameGenerator:
    """
    Name generation system for Stonegrove University clans.
    Generates culturally appropriate names based on clan characteristics.
    """
    
    def __init__(self, config_file: str = "config/clan_name_pools.yaml"):
        """Initialize the name generator with clan name pools"""
        self.config_file = config_file
        self.name_pools = self._load_name_pools()
        self.settings = self.name_pools.get('settings', {})
        
    def _load_name_pools(self) -> Dict:
        """Load name pools from YAML configuration"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"Name pools configuration file not found: {self.config_file}")
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing name pools YAML: {e}")
    
    def _get_clan_data(self, clan_key: str) -> Dict:
        """Get name pool data for a specific clan"""
        clans = self.name_pools.get('clans', {})
        if clan_key not in clans:
            raise ValueError(f"Clan '{clan_key}' not found in name pools")
        return clans[clan_key]
    
    def _weighted_choice(self, options: List[Dict], weight_key: str = 'frequency') -> str:
        """Make a weighted random choice from a list of options"""
        if not options:
            raise ValueError("No options provided for weighted choice")
        
        names = [option['name'] for option in options]
        weights = [option[weight_key] for option in options]
        
        # Normalize weights to sum to 1
        total_weight = sum(weights)
        if total_weight == 0:
            # If all weights are 0, use uniform distribution
            weights = [1.0] * len(weights)
            total_weight = len(weights)
        
        normalized_weights = [w / total_weight for w in weights]
        
        return np.random.choice(names, p=normalized_weights)
    
    def _determine_gender(self, clan_key: str) -> str:
        """Determine gender for a student based on clan and settings"""
        # Get base gender distribution
        gender_dist = self.settings.get('gender_distribution', {
            'male': 0.45,
            'female': 0.45,
            'neuter': 0.10
        })
        
        # Apply clan-specific rules
        clan_rules = self.settings.get('rules', {}).get('clan_specific_rules', {})
        if clan_key in clan_rules:
            clan_rule = clan_rules[clan_key]
            
            # Adjust neuter probability for specific clans
            if 'neuter_probability' in clan_rule:
                neuter_prob = clan_rule['neuter_probability']
                # Redistribute probabilities
                remaining_prob = 1.0 - neuter_prob
                gender_dist['neuter'] = neuter_prob
                gender_dist['male'] = remaining_prob * 0.5
                gender_dist['female'] = remaining_prob * 0.5
        
        # Make weighted choice
        genders = list(gender_dist.keys())
        weights = list(gender_dist.values())
        return np.random.choice(genders, p=weights)
    
    def generate_name(self, clan_key: str, gender: Optional[str] = None) -> GeneratedName:
        """
        Generate a complete name for a student of a specific clan.
        
        Args:
            clan_key: The clan identifier (e.g., 'malachite', 'baobab')
            gender: Optional gender override. If None, will be determined automatically.
        
        Returns:
            GeneratedName object with forename, surname, gender, clan, and full name
        """
        clan_data = self._get_clan_data(clan_key)
        
        # Determine gender if not provided
        if gender is None:
            gender = self._determine_gender(clan_key)
        
        # Get forename options for the gender
        forename_options = clan_data.get('forenames', {}).get(gender, [])
        if not forename_options:
            # Fallback to neuter names if gender-specific names not available
            forename_options = clan_data.get('forenames', {}).get('neuter', [])
            if not forename_options:
                raise ValueError(f"No forename options available for clan '{clan_key}' and gender '{gender}'")
        
        # Get surname options
        surname_options = clan_data.get('surnames', [])
        if not surname_options:
            raise ValueError(f"No surname options available for clan '{clan_key}'")
        
        # Generate forename and surname
        forename = self._weighted_choice(forename_options)
        surname = self._weighted_choice(surname_options)
        
        # Create full name
        full_name = f"{forename} {surname}"
        
        return GeneratedName(
            forename=forename,
            surname=surname,
            gender=gender,
            clan=clan_key,
            full_name=full_name
        )
    
    def generate_names_batch(self, clan_counts: Dict[str, int]) -> List[GeneratedName]:
        """
        Generate names for multiple students across different clans.
        
        Args:
            clan_counts: Dictionary mapping clan keys to number of students needed
        
        Returns:
            List of GeneratedName objects
        """
        names = []
        
        for clan_key, count in clan_counts.items():
            for _ in range(count):
                try:
                    name = self.generate_name(clan_key)
                    names.append(name)
                except Exception as e:
                    print(f"Warning: Could not generate name for clan '{clan_key}': {e}")
                    # Create a fallback name
                    fallback_name = GeneratedName(
                        forename=f"Unknown_{clan_key}",
                        surname="Unknown",
                        gender="neuter",
                        clan=clan_key,
                        full_name=f"Unknown_{clan_key} Unknown"
                    )
                    names.append(fallback_name)
        
        return names
    
    def get_available_clans(self) -> List[str]:
        """Get list of available clan keys"""
        return list(self.name_pools.get('clans', {}).keys())
    
    def get_clan_name(self, clan_key: str) -> str:
        """Get the display name for a clan"""
        clan_data = self._get_clan_data(clan_key)
        return clan_data.get('name', clan_key)
    
    def validate_name_pools(self) -> bool:
        """Validate that all name pools are properly configured"""
        try:
            clans = self.name_pools.get('clans', {})
            
            for clan_key, clan_data in clans.items():
                # Check that forenames exist for at least one gender
                forenames = clan_data.get('forenames', {})
                if not forenames:
                    print(f"Warning: Clan '{clan_key}' has no forename options")
                    return False
                
                # Check that surnames exist
                surnames = clan_data.get('surnames', [])
                if not surnames:
                    print(f"Warning: Clan '{clan_key}' has no surname options")
                    return False
                
                # Check that at least one gender has forename options
                has_forenames = False
                for gender, gender_names in forenames.items():
                    if gender_names:
                        has_forenames = True
                        break
                
                if not has_forenames:
                    print(f"Warning: Clan '{clan_key}' has no forename options for any gender")
                    return False
            
            return True
            
        except Exception as e:
            print(f"Error validating name pools: {e}")
            return False

def main():
    """Test the name generation system"""
    print("🧙‍♂️ Stonegrove University Name Generator")
    print("=" * 50)
    
    # Initialize generator
    generator = ClanNameGenerator()
    
    # Validate configuration
    if not generator.validate_name_pools():
        print("❌ Name pools validation failed!")
        return
    
    print("✅ Name pools validation passed!")
    print(f"📚 Available clans: {', '.join(generator.get_available_clans())}")
    print()
    
    # Test name generation for each clan
    print("🎲 Testing name generation for each clan:")
    print("-" * 50)
    
    for clan_key in generator.get_available_clans():
        clan_name = generator.get_clan_name(clan_key)
        print(f"\n🏛️ {clan_name} ({clan_key}):")
        
        # Generate 3 names for each clan
        for i in range(3):
            try:
                name = generator.generate_name(clan_key)
                print(f"  {i+1}. {name.full_name} ({name.gender})")
            except Exception as e:
                print(f"  {i+1}. Error: {e}")
    
    # Test batch generation
    print("\n" + "=" * 50)
    print("📊 Testing batch name generation:")
    print("-" * 50)
    
    # Generate 2 names for each of the first 5 clans
    test_clans = list(generator.get_available_clans())[:5]
    clan_counts = {clan: 2 for clan in test_clans}
    
    batch_names = generator.generate_names_batch(clan_counts)
    
    for name in batch_names:
        clan_display = generator.get_clan_name(name.clan)
        print(f"  {name.full_name} ({name.gender}) - {clan_display}")
    
    print(f"\n✅ Generated {len(batch_names)} names successfully!")

if __name__ == "__main__":
    main() 