import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

def visualize_assessment_data(csv_file="stonegrove_assessment_marks.csv"):
    """Create visualizations for the assessment data."""
    
    print("📊 Creating assessment visualizations...")
    
    # Load the assessment data
    df = pd.read_csv(csv_file)
    
    # Set up the plotting style
    plt.style.use('default')
    sns.set_palette("husl")
    
    # Create a large figure with multiple subplots
    fig = plt.figure(figsize=(20, 16))
    
    # 1. Overall mark distribution histogram
    ax1 = plt.subplot(3, 3, 1)
    plt.hist(df['assessment_mark'], bins=30, alpha=0.7, color='skyblue', edgecolor='black')
    plt.axvline(df['assessment_mark'].mean(), color='red', linestyle='--', label=f'Mean: {df["assessment_mark"].mean():.1f}')
    plt.axvline(56, color='green', linestyle=':', alpha=0.7, label='56')
    plt.axvline(64, color='green', linestyle=':', alpha=0.7, label='64')
    plt.fill_between([56, 64], 0, plt.gca().get_ylim()[1], alpha=0.2, color='green', label='56-64 Range')
    plt.xlabel('Assessment Mark')
    plt.ylabel('Frequency')
    plt.title('Overall Mark Distribution', fontsize=12, fontweight='bold')
    plt.legend()
    
    # 2. Grade distribution
    ax2 = plt.subplot(3, 3, 2)
    grade_counts = df['grade'].value_counts()
    colors = ['red', 'orange', 'yellow', 'lightgreen', 'green']
    plt.pie(grade_counts.values, labels=grade_counts.index, autopct='%1.1f%%', colors=colors, startangle=90)
    plt.title('Grade Distribution', fontsize=12, fontweight='bold')
    
    # 3. Performance by species
    ax3 = plt.subplot(3, 3, 3)
    species_performance = df.groupby('species')['assessment_mark'].mean()
    species_performance.plot(kind='bar', ax=ax3, color=['goldenrod', 'forestgreen'])
    plt.title('Average Performance by Species', fontsize=12, fontweight='bold')
    plt.ylabel('Average Mark')
    plt.xticks(rotation=0)
    
    # 4. Performance by ethnicity (top 10)
    ax4 = plt.subplot(3, 3, 4)
    ethnicity_performance = df.groupby('ethnicity')['assessment_mark'].mean().sort_values(ascending=False).head(10)
    ethnicity_performance.plot(kind='barh', ax=ax4, color='lightcoral')
    plt.title('Top 10 Ethnicities by Performance', fontsize=12, fontweight='bold')
    plt.xlabel('Average Mark')
    
    # 5. Performance by faculty
    ax5 = plt.subplot(3, 3, 5)
    faculty_performance = df.groupby('faculty')['assessment_mark'].mean().sort_values(ascending=False)
    faculty_performance.plot(kind='bar', ax=ax5, color='lightblue')
    plt.title('Performance by Faculty', fontsize=12, fontweight='bold')
    plt.ylabel('Average Mark')
    plt.xticks(rotation=45, ha='right')
    
    # 6. Performance by program (top 10)
    ax6 = plt.subplot(3, 3, 6)
    program_performance = df.groupby('programme')['assessment_mark'].mean().sort_values(ascending=False).head(10)
    program_performance.plot(kind='barh', ax=ax6, color='lightgreen')
    plt.title('Top 10 Programs by Performance', fontsize=12, fontweight='bold')
    plt.xlabel('Average Mark')
    
    # 7. Mark distribution by species
    ax7 = plt.subplot(3, 3, 7)
    for species in df['species'].unique():
        species_data = df[df['species'] == species]['assessment_mark']
        plt.hist(species_data, bins=20, alpha=0.6, label=species, density=True)
    plt.xlabel('Assessment Mark')
    plt.ylabel('Density')
    plt.title('Mark Distribution by Species', fontsize=12, fontweight='bold')
    plt.legend()
    
    # 8. Performance by gender
    ax8 = plt.subplot(3, 3, 8)
    gender_performance = df.groupby('gender')['assessment_mark'].mean()
    gender_performance.plot(kind='bar', ax=ax8, color=['lightblue', 'lightpink', 'lightgreen'])
    plt.title('Performance by Gender', fontsize=12, fontweight='bold')
    plt.ylabel('Average Mark')
    plt.xticks(rotation=0)
    
    # 9. Performance by socio-economic class
    ax9 = plt.subplot(3, 3, 9)
    socio_performance = df.groupby('socio_economic_class_rank')['assessment_mark'].mean()
    socio_performance.plot(kind='line', ax=ax9, marker='o', color='purple', linewidth=2, markersize=8)
    plt.title('Performance by Socio-Economic Class', fontsize=12, fontweight='bold')
    plt.ylabel('Average Mark')
    plt.xlabel('Socio-Economic Class Rank')
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('stonegrove_assessment_analysis.png', dpi=300, bbox_inches='tight')
    print("✅ Assessment visualization saved as: stonegrove_assessment_analysis.png")
    
    # Create a second figure for detailed analysis
    fig2, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    
    # Disability performance analysis
    disability_columns = [col for col in df.columns if any(disability in col for disability in 
                       ['physical_disability', 'mental_health_disability', 'specific_learning_disability', 
                        'autistic_spectrum', 'adhd', 'dyslexia', 'other_neurodivergence', 
                        'deaf_or_hearing_impaired', 'wheelchair_user', 'requires_personal_care', 
                        'blind_or_visually_impaired', 'communication_difficulties'])]
    
    if disability_columns:
        disability_performance = []
        for disability in disability_columns:
            if disability in df.columns:
                disabled_avg = df[df[disability] == True]['assessment_mark'].mean()
                non_disabled_avg = df[df[disability] == False]['assessment_mark'].mean()
                if not pd.isna(disabled_avg) and not pd.isna(non_disabled_avg):
                    disability_performance.append({
                        'disability': disability.replace('_', ' ').title(),
                        'disabled_avg': disabled_avg,
                        'non_disabled_avg': non_disabled_avg,
                        'difference': disabled_avg - non_disabled_avg
                    })
        
        if disability_performance:
            disability_df = pd.DataFrame(disability_performance)
            disability_df = disability_df.sort_values('difference', ascending=False)
            
            x = np.arange(len(disability_df))
            width = 0.35
            
            ax1.bar(x - width/2, disability_df['disabled_avg'], width, label='With Disability', color='lightcoral')
            ax1.bar(x + width/2, disability_df['non_disabled_avg'], width, label='Without Disability', color='lightblue')
            
            ax1.set_xlabel('Disability Type')
            ax1.set_ylabel('Average Mark')
            ax1.set_title('Performance by Disability Status', fontsize=14, fontweight='bold')
            ax1.set_xticks(x)
            ax1.set_xticklabels(disability_df['disability'], rotation=45, ha='right')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
    
    # Mark distribution by grade
    grade_order = ['Fail', 'Third', '2:2', '2:1', 'First']
    grade_data = [df[df['grade'] == grade]['assessment_mark'] for grade in grade_order]
    ax2.boxplot(grade_data, labels=grade_order)
    ax2.set_title('Mark Distribution by Grade', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Assessment Mark')
    ax2.grid(True, alpha=0.3)
    
    # Performance by educational background
    education_performance = df.groupby('prior_educational_experience')['assessment_mark'].mean()
    education_performance.plot(kind='bar', ax=ax3, color=['lightblue', 'lightgreen'])
    ax3.set_title('Performance by Educational Background', fontsize=14, fontweight='bold')
    ax3.set_ylabel('Average Mark')
    ax3.set_xticklabels(ax3.get_xticklabels(), rotation=0)
    ax3.grid(True, alpha=0.3)
    
    # Mark distribution by faculty
    faculty_data = [df[df['faculty'] == faculty]['assessment_mark'] for faculty in df['faculty'].unique()]
    ax4.boxplot(faculty_data, labels=df['faculty'].unique())
    ax4.set_title('Mark Distribution by Faculty', fontsize=14, fontweight='bold')
    ax4.set_ylabel('Assessment Mark')
    ax4.set_xticklabels(ax4.get_xticklabels(), rotation=45, ha='right')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('stonegrove_assessment_detailed_analysis.png', dpi=300, bbox_inches='tight')
    print("✅ Detailed assessment analysis saved as: stonegrove_assessment_detailed_analysis.png")
    
    # Print verification of specifications
    print(f"\n✅ SPECIFICATION VERIFICATION:")
    
    # Check fail rate (should be about 5%)
    fail_rate = (len(df[df['assessment_mark'] < 40]) / len(df)) * 100
    print(f"  • Fail rate: {fail_rate:.1f}% (target: ~5%)")
    
    # Check 56-64 range
    range_56_64 = len(df[(df['assessment_mark'] >= 56) & (df['assessment_mark'] <= 64)])
    range_percentage = (range_56_64 / len(df)) * 100
    print(f"  • Marks 56-64: {range_percentage:.1f}% (should be large proportion)")
    
    # Check species performance
    elf_avg = df[df['species'] == 'Elf']['assessment_mark'].mean()
    dwarf_avg = df[df['species'] == 'Dwarf']['assessment_mark'].mean()
    print(f"  • Elves vs Dwarves: {elf_avg:.1f} vs {dwarf_avg:.1f} (Elves should outperform)")
    
    # Check ethnicity performance
    baobab_avg = df[df['ethnicity'] == 'Baobab']['assessment_mark'].mean()
    alabaster_avg = df[df['ethnicity'] == 'Alabaster']['assessment_mark'].mean()
    print(f"  • Baobab vs Alabaster: {baobab_avg:.1f} vs {alabaster_avg:.1f} (Baobab should be highest, Alabaster lowest)")
    
    # Check disability performance
    if 'specific_learning_disability' in df.columns:
        sld_avg = df[df['specific_learning_disability'] == True]['assessment_mark'].mean()
        no_sld_avg = df[df['specific_learning_disability'] == False]['assessment_mark'].mean()
        print(f"  • Specific Learning Disability: {sld_avg:.1f} vs {no_sld_avg:.1f} (should perform less well)")
    
    if 'autistic_spectrum' in df.columns:
        as_avg = df[df['autistic_spectrum'] == True]['assessment_mark'].mean()
        no_as_avg = df[df['autistic_spectrum'] == False]['assessment_mark'].mean()
        print(f"  • Autistic Spectrum: {as_avg:.1f} vs {no_as_avg:.1f} (should perform better)")

if __name__ == "__main__":
    visualize_assessment_data() 