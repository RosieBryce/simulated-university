import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def analyze_population(csv_file="stonegrove_university_population.csv"):
    """Analyze the generated population and display interesting statistics."""
    
    print("🏛️  STONEGROVE UNIVERSITY POPULATION ANALYSIS")
    print("=" * 60)
    
    # Load the data
    df = pd.read_csv(csv_file)
    
    # Basic statistics
    print(f"\n📊 BASIC STATISTICS:")
    print(f"Total students: {len(df):,}")
    print(f"Total columns: {len(df.columns)}")
    
    # Race distribution
    print(f"\n👥 SPECIES DISTRIBUTION:")
    species_counts = df['species'].value_counts()
    for species, count in species_counts.items():
        percentage = (count / len(df)) * 100
        print(f"  {species}: {count:,} students ({percentage:.1f}%)")
    
    # Gender distribution
    print(f"\n⚧ GENDER DISTRIBUTION:")
    gender_counts = df['gender'].value_counts()
    for gender, count in gender_counts.items():
        percentage = (count / len(df)) * 100
        print(f"  {gender}: {count:,} students ({percentage:.1f}%)")
    
    # Ethnicity distribution by species
    print(f"\n🌍 ETHNICITY DISTRIBUTION BY SPECIES:")
    for species in ['Dwarf', 'Elf']:
        species_subset = df[df['species'] == species]
        print(f"\n  {species} Ethnicities:")
        ethnicity_counts = species_subset['ethnicity'].value_counts()
        for ethnicity, count in ethnicity_counts.items():
            percentage = (count / len(species_subset)) * 100
            print(f"    {ethnicity}: {count:,} students ({percentage:.1f}%)")
    
    # Educational experience by species
    print(f"\n🎓 PRIOR EDUCATIONAL EXPERIENCE BY SPECIES:")
    for species in ['Dwarf', 'Elf']:
        species_subset = df[df['species'] == species]
        print(f"\n  {species}:")
        education_counts = species_subset['prior_educational_experience'].value_counts()
        for education, count in education_counts.items():
            percentage = (count / len(species_subset)) * 100
            print(f"    {education}: {count:,} students ({percentage:.1f}%)")
    
    # Socio-economic class distribution
    print(f"\n💰 SOCIO-ECONOMIC CLASS DISTRIBUTION:")
    class_counts = df['socio_economic_class_rank'].value_counts().sort_index()
    for class_rank, count in class_counts.items():
        percentage = (count / len(df)) * 100
        print(f"  Class {class_rank}: {count:,} students ({percentage:.1f}%)")
    
    # Disability statistics
    print(f"\n♿ DISABILITY STATISTICS:")
    disability_columns = [col for col in df.columns if col not in ['student_id', 'species', 'gender', 'ethnicity', 'prior_educational_experience', 'socio_economic_class_rank']]
    
    total_with_disabilities = 0
    for disability in disability_columns:
        if disability != 'no_known_disabilities':
            count = df[disability].sum()
            percentage = (count / len(df)) * 100
            print(f"  {disability.replace('_', ' ').title()}: {count:,} students ({percentage:.1f}%)")
            total_with_disabilities += count
    
    no_disabilities = df['no_known_disabilities'].sum()
    print(f"  No Known Disabilities: {no_disabilities:,} students ({(no_disabilities/len(df))*100:.1f}%)")
    
    # Cross-analysis: Disability rates by species
    print(f"\n♿ DISABILITY RATES BY SPECIES:")
    for species in ['Dwarf', 'Elf']:
        species_subset = df[df['species'] == species]
        print(f"\n  {species} Disability Rates:")
        for disability in disability_columns:
            if disability != 'no_known_disabilities':
                rate = species_subset[disability].mean() * 100
                print(f"    {disability.replace('_', ' ').title()}: {rate:.1f}%")
    
    # Socio-economic class by species and ethnicity
    print(f"\n💰 SOCIO-ECONOMIC CLASS BY SPECIES AND ETHNICITY:")
    for species in ['Dwarf', 'Elf']:
        species_subset = df[df['species'] == species]
        print(f"\n  {species} Average Socio-Economic Class by Ethnicity:")
        for ethnicity in species_subset['ethnicity'].unique():
            ethnicity_subset = species_subset[species_subset['ethnicity'] == ethnicity]
            avg_class = ethnicity_subset['socio_economic_class_rank'].mean()
            print(f"    {ethnicity}: {avg_class:.2f}")
    
    # Create some visualizations
    print(f"\n📈 CREATING VISUALIZATIONS...")
    
    # Set up the plotting style
    plt.style.use('default')
    sns.set_palette("husl")
    
    # Create a figure with multiple subplots
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('Stonegrove University Population Analysis', fontsize=16, fontweight='bold')
    
    # 1. Species and Gender distribution
    ax1 = axes[0, 0]
    species_gender = pd.crosstab(df['species'], df['gender'])
    species_gender.plot(kind='bar', ax=ax1, stacked=True)
    ax1.set_title('Species and Gender Distribution')
    ax1.set_ylabel('Number of Students')
    ax1.legend(title='Gender')
    ax1.tick_params(axis='x', rotation=0)
    
    # 2. Ethnicity distribution by species
    ax2 = axes[0, 1]
    ethnicity_species = pd.crosstab(df['ethnicity'], df['species'])
    ethnicity_species.plot(kind='bar', ax=ax2)
    ax2.set_title('Ethnicity Distribution by Species')
    ax2.set_ylabel('Number of Students')
    ax2.legend(title='Species')
    ax2.tick_params(axis='x', rotation=45)
    
    # 3. Socio-economic class distribution
    ax3 = axes[1, 0]
    class_counts.plot(kind='bar', ax=ax3, color='skyblue')
    ax3.set_title('Socio-Economic Class Distribution')
    ax3.set_xlabel('Class Rank (1=Low, 5=High)')
    ax3.set_ylabel('Number of Students')
    ax3.tick_params(axis='x', rotation=0)
    
    # 4. Disability rates by species
    ax4 = axes[1, 1]
    disability_rates = []
    disability_names = []
    for disability in disability_columns:
        if disability != 'no_known_disabilities':
            dwarf_rate = df[df['species'] == 'Dwarf'][disability].mean() * 100
            elf_rate = df[df['species'] == 'Elf'][disability].mean() * 100
            disability_rates.extend([dwarf_rate, elf_rate])
            disability_names.extend([f'{disability.replace("_", " ").title()}\n(Dwarf)', 
                                   f'{disability.replace("_", " ").title()}\n(Elf)'])
    
    bars = ax4.bar(range(len(disability_rates)), disability_rates, 
                   color=['lightcoral' if i % 2 == 0 else 'lightblue' for i in range(len(disability_rates))])
    ax4.set_title('Disability Rates by Species')
    ax4.set_ylabel('Percentage (%)')
    ax4.set_xticks(range(len(disability_names)))
    ax4.set_xticklabels(disability_names, rotation=45, ha='right')
    
    plt.tight_layout()
    plt.savefig('stonegrove_population_analysis.png', dpi=300, bbox_inches='tight')
    print(f"✅ Analysis chart saved as: stonegrove_population_analysis.png")
    
    # Summary statistics
    print(f"\n📋 SUMMARY:")
    print(f"  • Most common ethnicity: {df['ethnicity'].mode()[0]}")
    print(f"  • Average socio-economic class: {df['socio_economic_class_rank'].mean():.2f}")
    print(f"  • Students with at least one disability: {total_with_disabilities:,} ({(total_with_disabilities/len(df))*100:.1f}%)")
    print(f"  • Students with no known disabilities: {no_disabilities:,} ({(no_disabilities/len(df))*100:.1f}%)")
    
    # Find the most diverse ethnicity group
    most_diverse_ethnicity = df.groupby('ethnicity')['socio_economic_class_rank'].std().idxmax()
    print(f"  • Most socio-economically diverse ethnicity: {most_diverse_ethnicity}")
    
    return df

if __name__ == "__main__":
    df = analyze_population() 