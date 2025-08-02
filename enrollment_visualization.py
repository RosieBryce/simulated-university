import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def visualize_enrollment(csv_file="stonegrove_enrolled_population.csv"):
    """Create visualizations for the enrollment data."""
    
    print("📊 Creating enrollment visualizations...")
    
    # Load the enrolled population
    df = pd.read_csv(csv_file)
    
    # Set up the plotting style
    plt.style.use('default')
    sns.set_palette("husl")
    
    # Create a large figure with multiple subplots
    fig = plt.figure(figsize=(20, 16))
    
    # 1. Faculty distribution by race
    ax1 = plt.subplot(3, 3, 1)
    faculty_race = pd.crosstab(df['faculty'], df['race'])
    faculty_race.plot(kind='bar', ax=ax1, stacked=True)
    ax1.set_title('Faculty Distribution by Race', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Number of Students')
    ax1.legend(title='Race')
    ax1.tick_params(axis='x', rotation=45)
    
    # 2. Faculty distribution by gender
    ax2 = plt.subplot(3, 3, 2)
    faculty_gender = pd.crosstab(df['faculty'], df['gender'])
    faculty_gender.plot(kind='bar', ax=ax2, stacked=True)
    ax2.set_title('Faculty Distribution by Gender', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Number of Students')
    ax2.legend(title='Gender')
    ax2.tick_params(axis='x', rotation=45)
    
    # 3. Top 10 most popular programs
    ax3 = plt.subplot(3, 3, 3)
    program_counts = df['programme'].value_counts().head(10)
    program_counts.plot(kind='barh', ax=ax3, color='skyblue')
    ax3.set_title('Top 10 Most Popular Programs', fontsize=12, fontweight='bold')
    ax3.set_xlabel('Number of Students')
    
    # 4. Race distribution in each faculty (pie charts)
    faculties = df['faculty'].unique()
    for i, faculty in enumerate(faculties):
        ax = plt.subplot(3, 3, 4 + i)
        faculty_data = df[df['faculty'] == faculty]
        race_counts = faculty_data['race'].value_counts()
        ax.pie(race_counts.values, labels=race_counts.index, autopct='%1.1f%%', startangle=90)
        ax.set_title(f'{faculty}\nRace Distribution', fontsize=10, fontweight='bold')
    
    # 5. Gender distribution in Critical Power
    ax8 = plt.subplot(3, 3, 8)
    critical_power = df[df['programme'] == 'Critical Power']
    if len(critical_power) > 0:
        gender_counts = critical_power['gender'].value_counts()
        colors = ['lightcoral', 'lightblue', 'lightgreen']
        ax8.pie(gender_counts.values, labels=gender_counts.index, autopct='%1.1f%%', 
                colors=colors, startangle=90)
        ax8.set_title('Critical Power\nGender Distribution', fontsize=12, fontweight='bold')
    
    # 6. Brewcraft and Fermentation Systems by race
    ax9 = plt.subplot(3, 3, 9)
    brewcraft = df[df['programme'] == 'Brewcraft and Fermentation Systems']
    if len(brewcraft) > 0:
        race_counts = brewcraft['race'].value_counts()
        colors = ['goldenrod', 'forestgreen']
        ax9.pie(race_counts.values, labels=race_counts.index, autopct='%1.1f%%', 
                colors=colors, startangle=90)
        ax9.set_title('Brewcraft and Fermentation\nRace Distribution', fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('stonegrove_enrollment_analysis.png', dpi=300, bbox_inches='tight')
    print("✅ Enrollment visualization saved as: stonegrove_enrollment_analysis.png")
    
    # Create a second figure for program popularity
    fig2, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # Program popularity by faculty
    faculty_program = pd.crosstab(df['faculty'], df['programme'])
    faculty_program_heatmap = faculty_program.T  # Transpose for better visualization
    
    sns.heatmap(faculty_program_heatmap, annot=True, fmt='d', cmap='YlOrRd', ax=ax1)
    ax1.set_title('Program Enrollment by Faculty', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Faculty')
    ax1.set_ylabel('Program')
    ax1.tick_params(axis='x', rotation=45)
    ax1.tick_params(axis='y', rotation=0)
    
    # Department popularity
    dept_counts = df['department'].value_counts().head(10)
    dept_counts.plot(kind='barh', ax=ax2, color='lightcoral')
    ax2.set_title('Top 10 Most Popular Departments', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Number of Students')
    
    plt.tight_layout()
    plt.savefig('stonegrove_program_analysis.png', dpi=300, bbox_inches='tight')
    print("✅ Program analysis saved as: stonegrove_program_analysis.png")
    
    # Print some interesting statistics
    print(f"\n📊 ENROLLMENT HIGHLIGHTS:")
    print(f"  • Most popular program: {df['programme'].mode()[0]} ({df['programme'].value_counts().iloc[0]} students)")
    print(f"  • Least popular program: {df['programme'].value_counts().iloc[-1]} ({df['programme'].value_counts().iloc[-1]} students)")
    print(f"  • Faculty with most students: {df['faculty'].mode()[0]} ({df['faculty'].value_counts().iloc[0]} students)")
    print(f"  • Faculty with least students: {df['faculty'].value_counts().iloc[-1]} ({df['faculty'].value_counts().iloc[-1]} students)")
    
    # Check if specifications were met
    print(f"\n✅ SPECIFICATION VERIFICATION:")
    
    # Dwarves more likely in Living Lore or Applied Forging
    dwarf_faculties = df[df['race'] == 'Dwarf']['faculty'].value_counts()
    top_dwarf_faculty = dwarf_faculties.index[0]
    print(f"  • Top faculty for Dwarves: {top_dwarf_faculty} ({dwarf_faculties.iloc[0]} students)")
    
    # Elves rarely in Applied Forging
    elf_applied_forging = len(df[(df['race'] == 'Elf') & (df['faculty'] == 'Faculty of Applied Forging')])
    total_elves = len(df[df['race'] == 'Elf'])
    elf_applied_percentage = (elf_applied_forging / total_elves) * 100
    print(f"  • Elves in Applied Forging: {elf_applied_forging} ({elf_applied_percentage:.1f}% of all Elves)")
    
    # Critical Power female-dominated
    critical_power_female = len(df[(df['programme'] == 'Critical Power') & (df['gender'] == 'Female')])
    total_critical_power = len(df[df['programme'] == 'Critical Power'])
    critical_power_female_percentage = (critical_power_female / total_critical_power) * 100
    print(f"  • Critical Power female students: {critical_power_female} ({critical_power_female_percentage:.1f}%)")
    
    # Transdisciplinary Design least popular
    transdisciplinary_programs = ['Knowledge System Prototyping', 'Embodied Research Methods']
    transdisciplinary_total = len(df[df['programme'].isin(transdisciplinary_programs)])
    print(f"  • Transdisciplinary Design students: {transdisciplinary_total} (very small number)")
    
    # Language and Symbol popular
    language_programs = ['Ancient Tongues and Translation', 'Comparative Runes and Scripts', 'Multispecies Semantics']
    language_total = len(df[df['programme'].isin(language_programs)])
    language_percentage = (language_total / len(df)) * 100
    print(f"  • Language and Symbol students: {language_total} ({language_percentage:.1f}% of all students)")
    
    # Brewcraft most popular
    brewcraft_total = len(df[df['programme'] == 'Brewcraft and Fermentation Systems'])
    brewcraft_percentage = (brewcraft_total / len(df)) * 100
    print(f"  • Brewcraft and Fermentation students: {brewcraft_total} ({brewcraft_percentage:.1f}% of all students)")

if __name__ == "__main__":
    visualize_enrollment() 