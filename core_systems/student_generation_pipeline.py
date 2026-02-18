import sys
from pathlib import Path

# Ensure supporting_systems is on path when run from project root
_project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_project_root))
sys.path.insert(0, str(_project_root / 'supporting_systems'))

import numpy as np
import pandas as pd
import random
from name_generator import ClanNameGenerator
from personality_refinement_system import PersonalityRefinementSystem
from motivation_profile_system import MotivationProfileSystem
import yaml

# Load config files
with open('config/clan_personality_specifications.yaml', 'r', encoding='utf-8') as f:
    CLAN_SPEC = yaml.safe_load(f)["clans"]
with open('config/disability_distribution.yaml', 'r', encoding='utf-8') as f:
    DISABILITY_DIST = yaml.safe_load(f)

# Helper: weighted random choice from dict
def weighted_choice(d):
    keys = list(d.keys())
    vals = np.array(list(d.values()), dtype=float)
    vals = vals / vals.sum()
    return np.random.choice(keys, p=vals)

def sample_age():
    # 94% are 18, rest 19-25
    if np.random.rand() < 0.94:
        return 18
    else:
        return np.random.randint(19, 26)

def sample_education():
    # Example: 60% academic, 30% vocational, 10% no qualifications
    return np.random.choice(['academic', 'vocational', 'no_qualifications'], p=[0.6, 0.3, 0.1])

def sample_socio_economic_rank():
    # Example: 8 ranks, uniform
    return np.random.choice(list(range(1,9)), p=[1/8]*8)

def sample_disabilities(species):
    """Sample disabilities using independent Bernoulli draws per disability.
    Students can have multiple disabilities (comorbidities).
    If none are drawn, returns ['no_known_disabilities']."""
    dist = DISABILITY_DIST[species]
    disabilities = [k for k, p in dist.items() if np.random.rand() < p]
    if not disabilities:
        disabilities = ['no_known_disabilities']
    return disabilities

def sample_species_and_clan():
    # Example: 60% dwarf, 40% elf; then uniform among clans
    species = np.random.choice(['Dwarf', 'Elf'], p=[0.6, 0.4])
    if species == 'Dwarf':
        clans = [k for k, v in CLAN_SPEC.items() if 'dwarves' in v['name'].lower()]
    else:
        clans = [k for k, v in CLAN_SPEC.items() if 'elves' in v['name'].lower()]
    if not clans:
        print(f"DEBUG: No clans found for species {species}. Clan names: {[v['name'] for v in CLAN_SPEC.values()]}")
        raise ValueError(f"No clans found for species {species}")
    clan = np.random.choice(clans)
    return species, clan

def sample_gender():
    # 45% male, 45% female, 10% neuter
    return np.random.choice(['male', 'female', 'neuter'], p=[0.45, 0.45, 0.1])

def sample_base_personality(clan):
    spec = CLAN_SPEC[clan]['personality_ranges']
    return {k: float(np.random.uniform(v[0], v[1])) for k, v in spec.items()}

def generate_students(n=500, seed=42):
    np.random.seed(seed)
    random.seed(seed)
    name_gen = ClanNameGenerator('config/clan_name_pools.yaml')
    personality_refiner = PersonalityRefinementSystem()
    motivation_system = MotivationProfileSystem()
    students = []
    for i in range(n):
        species, clan = sample_species_and_clan()
        gender = sample_gender()
        name = name_gen.generate_name(clan, gender)
        base_personality = sample_base_personality(clan)
        disabilities = sample_disabilities(species)
        socio_economic_rank = sample_socio_economic_rank()
        education = sample_education()
        age = sample_age()
        # Refine personality
        characteristics = {
            'disabilities': disabilities,
            'socio_economic_rank': socio_economic_rank,
            'education': education,
            'age': age
        }
        refinement = personality_refiner.refine_personality(base_personality, characteristics)
        refined_personality = refinement.refined_personality
        # Motivation profile
        motivation = motivation_system.generate_student_motivation(clan, refined_personality)
        students.append({
            'species': species,
            'clan': clan,
            'gender': gender,
            'forename': name.forename,
            'surname': name.surname,
            'full_name': name.full_name,
            'age': age,
            'education': education,
            'socio_economic_rank': socio_economic_rank,
            'disabilities': ",".join(disabilities),
            **{f'base_{k}': v for k, v in base_personality.items()},
            **{f'refined_{k}': v for k, v in refined_personality.items()},
            **{f'motivation_{k}': v for k, v in motivation['nudged'].items()}
        })
    return pd.DataFrame(students)

def main():
    df = generate_students(500)
    print("\n=== Student Sample (first 5) ===")
    print(df.head(5).T)
    print("\n=== Summary Statistics ===")
    print(df.describe(include='all').T)
    
    print("\n=== Detailed Personality Statistics ===")
    personality_cols = [c for c in df.columns if c.startswith('refined_')]
    personality_stats = df[personality_cols].agg(['min', 'max', 'mean', 'std']).round(3)
    print(personality_stats)
    
    print("\n=== Detailed Motivation Statistics ===")
    motivation_cols = [c for c in df.columns if c.startswith('motivation_')]
    motivation_stats = df[motivation_cols].agg(['min', 'max', 'mean', 'std']).round(3)
    print(motivation_stats)
    
    print("\n=== Disability Distribution ===")
    disability_counts = df['disabilities'].value_counts()
    print(disability_counts)
    
    print("\n=== Species and Clan Distribution ===")
    species_clan_counts = df.groupby(['species', 'clan']).size()
    print(species_clan_counts)
    
    # Check for critically low values
    print("\n=== Critically Low Values Analysis ===")
    print("Personality traits with mean < 0.3:")
    low_personality = personality_stats.loc['mean'][personality_stats.loc['mean'] < 0.3]
    if len(low_personality) > 0:
        print(low_personality)
    else:
        print("None found")
    
    print("\nMotivation dimensions with mean < 0.3:")
    low_motivation = motivation_stats.loc['mean'][motivation_stats.loc['mean'] < 0.3]
    if len(low_motivation) > 0:
        print(low_motivation)
    else:
        print("None found")
    
    # Save to CSV (data/ for consistency with rest of pipeline)
    output_path = _project_root / 'data' / 'stonegrove_individual_students.csv'
    df.to_csv(output_path, index=False)
    print(f"\nSaved to {output_path}")

if __name__ == "__main__":
    main()