import pandas as pd
import numpy as np
import random
import yaml
import os
from typing import Dict, List, Tuple

class StonegrovePopulationGenerator:
    """
    Generates fictional student population for Stonegrove University
    according to the specified distributions and requirements.
    """
    
    def __init__(self, total_students: int = 12000, seed: int = 42, config_dir: str = "config"):
        """
        Initialize the population generator.
        
        Args:
            total_students: Total number of students to generate
            seed: Random seed for reproducibility
            config_dir: Directory containing YAML configuration files
        """
        self.total_students = total_students
        self.seed = seed
        self.config_dir = config_dir
        random.seed(seed)
        np.random.seed(seed)
        
        # Calculate student counts by species
        self.dwarf_count = int(total_students * 0.55)  # 55% Dwarves
        self.elf_count = total_students - self.dwarf_count  # 45% Elves
        
        # Load distributions from YAML files
        self._load_distributions()
    
    def _load_distributions(self):
        """Load all distribution specifications from YAML files."""
        
        # Load species distribution
        with open(os.path.join(self.config_dir, 'species_distribution.yaml'), 'r') as f:
            self.species_distribution = yaml.safe_load(f)
        
        # Load gender distribution
        with open(os.path.join(self.config_dir, 'gender_distribution.yaml'), 'r') as f:
            self.gender_distribution = yaml.safe_load(f)
        
        # Load ethnicity distribution
        with open(os.path.join(self.config_dir, 'ethnicity_distribution.yaml'), 'r') as f:
            self.ethnicity_distribution = yaml.safe_load(f)
        
        # Load disability distribution
        with open(os.path.join(self.config_dir, 'disability_distribution.yaml'), 'r') as f:
            self.disability_distribution = yaml.safe_load(f)
        
        # Load education distribution
        with open(os.path.join(self.config_dir, 'education_distribution.yaml'), 'r') as f:
            self.education_distribution = yaml.safe_load(f)
        
        # Load socio-economic distribution
        with open(os.path.join(self.config_dir, 'socio_economic_distribution.yaml'), 'r') as f:
            self.socio_economic_distribution = yaml.safe_load(f)
        
        # Validate that all distributions sum to 1.0
        self._validate_distributions()
    
    def _validate_distributions(self):
        """Validate that all distributions sum to 1.0 (100%)."""
        print("Validating distribution configurations...")
        
        # Validate species distribution
        species_sum = sum(self.species_distribution.values())
        if abs(species_sum - 1.0) > 0.001:
            raise ValueError(f"Species distribution must sum to 1.0, got {species_sum}")
        
        # Validate gender distribution
        gender_sum = sum(self.gender_distribution.values())
        if abs(gender_sum - 1.0) > 0.001:
            raise ValueError(f"Gender distribution must sum to 1.0, got {gender_sum}")
        
        # Validate ethnicity distributions
        for species, ethnicities in self.ethnicity_distribution.items():
            ethnicity_sum = sum(ethnicities.values())
            if abs(ethnicity_sum - 1.0) > 0.001:
                raise ValueError(f"Ethnicity distribution for {species} must sum to 1.0, got {ethnicity_sum}")
        
        # Validate disability distributions
        for species, disabilities in self.disability_distribution.items():
            disability_sum = sum(disabilities.values())
            if abs(disability_sum - 1.0) > 0.001:
                raise ValueError(f"Disability distribution for {species} must sum to 1.0, got {disability_sum}")
        
        # Validate education distributions
        for species, education in self.education_distribution.items():
            education_sum = sum(education.values())
            if abs(education_sum - 1.0) > 0.001:
                raise ValueError(f"Education distribution for {species} must sum to 1.0, got {education_sum}")
        
        # Validate socio-economic distributions
        for species, ethnicities in self.socio_economic_distribution.items():
            for ethnicity, classes in ethnicities.items():
                class_sum = sum(classes.values())
                if abs(class_sum - 1.0) > 0.001:
                    raise ValueError(f"Socio-economic distribution for {species} {ethnicity} must sum to 1.0, got {class_sum}")
        
        print("✅ All distributions validated successfully!")
    
    def _generate_species_data(self) -> pd.Series:
        """Generate species data according to distribution."""
        species_list = ['Dwarf'] * self.dwarf_count + ['Elf'] * self.elf_count
        random.shuffle(species_list)
        return pd.Series(species_list)
    
    def _generate_gender_data(self) -> pd.Series:
        """Generate gender data according to distribution."""
        genders = []
        for _ in range(self.total_students):
            gender = np.random.choice(
                list(self.gender_distribution.keys()),
                p=list(self.gender_distribution.values())
            )
            genders.append(gender)
        return pd.Series(genders)
    
    def _generate_ethnicity_data(self, species_data: pd.Series) -> pd.Series:
        """Generate ethnicity data based on species."""
        ethnicities = []
        for species in species_data:
            ethnicity_dist = self.ethnicity_distribution[species]
            ethnicity = np.random.choice(
                list(ethnicity_dist.keys()),
                p=list(ethnicity_dist.values())
            )
            ethnicities.append(ethnicity)
        return pd.Series(ethnicities)
    
    def _generate_disability_data(self, species_data: pd.Series) -> pd.DataFrame:
        """Generate disability data as boolean columns."""
        disability_columns = [
            'physical_disability', 'mental_health_disability', 'specific_learning_disability',
            'autistic_spectrum', 'adhd', 'dyslexia', 'other_neurodivergence',
            'deaf_or_hearing_impaired', 'wheelchair_user', 'requires_personal_care',
            'blind_or_visually_impaired', 'communication_difficulties', 'no_known_disabilities'
        ]
        
        disability_data = {}
        
        for disability in disability_columns:
            values = []
            for species in species_data:
                prob = self.disability_distribution[species][disability]
                has_disability = np.random.random() < prob
                values.append(has_disability)
            disability_data[disability] = values
        
        return pd.DataFrame(disability_data)
    
    def _generate_education_data(self, species_data: pd.Series) -> pd.Series:
        """Generate prior educational experience data."""
        education_types = []
        for species in species_data:
            education_dist = self.education_distribution[species]
            education_type = np.random.choice(
                list(education_dist.keys()),
                p=list(education_dist.values())
            )
            education_types.append(education_type)
        return pd.Series(education_types)
    
    def _generate_socio_economic_data(self, species_data: pd.Series, ethnicity_data: pd.Series) -> pd.Series:
        """Generate socio-economic class rank data."""
        class_ranks = []
        for species, ethnicity in zip(species_data, ethnicity_data):
            rank_dist = self.socio_economic_distribution[species][ethnicity]
            class_rank = np.random.choice(
                list(rank_dist.keys()),
                p=list(rank_dist.values())
            )
            class_ranks.append(class_rank)
        return pd.Series(class_ranks)
    
    def generate_population(self) -> pd.DataFrame:
        """Generate the complete student population."""
        print(f"Generating population of {self.total_students} students...")
        
        # Generate base data
        student_ids = range(1, self.total_students + 1)
        species_data = self._generate_species_data()
        gender_data = self._generate_gender_data()
        ethnicity_data = self._generate_ethnicity_data(species_data)
        disability_data = self._generate_disability_data(species_data)
        education_data = self._generate_education_data(species_data)
        socio_economic_data = self._generate_socio_economic_data(species_data, ethnicity_data)
        
        # Combine all data
        population_data = {
            'student_id': student_ids,
            'species': species_data,
            'gender': gender_data,
            'ethnicity': ethnicity_data,
            'prior_educational_experience': education_data,
            'socio_economic_class_rank': socio_economic_data
        }
        
        # Add disability columns
        for col in disability_data.columns:
            population_data[col] = disability_data[col]
        
        # Create DataFrame
        df = pd.DataFrame(population_data)
        
        print("Population generation completed!")
        return df
    
    def validate_distributions(self, df: pd.DataFrame) -> Dict:
        """Validate that the generated data matches the specified distributions."""
        print("\nValidating distributions...")
        
        validation_results = {}
        
        # Validate species distribution
        species_counts = df['species'].value_counts(normalize=True)
        validation_results['species'] = {
            'expected': self.species_distribution,
            'actual': species_counts.to_dict(),
            'difference': {k: abs(species_counts.get(k, 0) - v) for k, v in self.species_distribution.items()}
        }
        
        # Validate gender distribution
        gender_counts = df['gender'].value_counts(normalize=True)
        validation_results['gender'] = {
            'expected': self.gender_distribution,
            'actual': gender_counts.to_dict(),
            'difference': {k: abs(gender_counts.get(k, 0) - v) for k, v in self.gender_distribution.items()}
        }
        
        # Validate ethnicity distribution by species
        for species in ['Dwarf', 'Elf']:
            species_subset = df[df['species'] == species]
            if len(species_subset) > 0:
                ethnicity_counts = species_subset['ethnicity'].value_counts(normalize=True)
                validation_results[f'ethnicity_{species}'] = {
                    'expected': self.ethnicity_distribution[species],
                    'actual': ethnicity_counts.to_dict(),
                    'difference': {k: abs(ethnicity_counts.get(k, 0) - v) for k, v in self.ethnicity_distribution[species].items()}
                }
        
        # Validate disability distributions
        disability_columns = [col for col in df.columns if col not in ['student_id', 'species', 'gender', 'ethnicity', 'prior_educational_experience', 'socio_economic_class_rank']]
        
        for species in ['Dwarf', 'Elf']:
            species_subset = df[df['species'] == species]
            if len(species_subset) > 0:
                for disability in disability_columns:
                    actual_rate = species_subset[disability].mean()
                    expected_rate = self.disability_distribution[species][disability]
                    validation_results[f'disability_{species}_{disability}'] = {
                        'expected': expected_rate,
                        'actual': actual_rate,
                        'difference': abs(actual_rate - expected_rate)
                    }
        
        return validation_results
    
    def print_validation_summary(self, validation_results: Dict):
        """Print a summary of validation results."""
        print("\n" + "="*60)
        print("VALIDATION SUMMARY")
        print("="*60)
        
        max_differences = []
        
        for category, results in validation_results.items():
            if 'difference' in results:
                if isinstance(results['difference'], dict):
                    max_diff = max(results['difference'].values())
                    max_differences.append((category, max_diff))
                else:
                    max_differences.append((category, results['difference']))
        
        print(f"Maximum distribution differences:")
        for category, diff in sorted(max_differences, key=lambda x: x[1], reverse=True):
            print(f"  {category}: {diff:.4f}")
        
        overall_max = max(max_differences, key=lambda x: x[1])[1]
        print(f"\nOverall maximum difference: {overall_max:.4f}")
        
        if overall_max < 0.05:  # 5% tolerance
            print("✅ All distributions are within acceptable tolerance!")
        else:
            print("⚠️  Some distributions may need adjustment.")

def main():
    """Main function to generate and export the population."""
    print("Stonegrove University Population Generator")
    print("="*50)
    
    # Generate population
    generator = StonegrovePopulationGenerator(total_students=12000, seed=42)
    population_df = generator.generate_population()
    
    # Validate distributions
    validation_results = generator.validate_distributions(population_df)
    generator.print_validation_summary(validation_results)
    
    # Export to CSV
    output_filename = "stonegrove_university_population.csv"
    population_df.to_csv(output_filename, index=False)
    print(f"\n✅ Population exported to: {output_filename}")
    
    # Print summary statistics
    print(f"\n📊 SUMMARY STATISTICS:")
    print(f"Total students: {len(population_df)}")
    print(f"Columns: {len(population_df.columns)}")
    print(f"Memory usage: {population_df.memory_usage(deep=True).sum() / 1024:.2f} KB")
    
    # Show first few rows
    print(f"\n📋 SAMPLE DATA (first 5 rows):")
    print(population_df.head())
    
    # Show column names
    print(f"\n📋 COLUMNS:")
    for i, col in enumerate(population_df.columns, 1):
        print(f"  {i:2d}. {col}")

if __name__ == "__main__":
    main() 