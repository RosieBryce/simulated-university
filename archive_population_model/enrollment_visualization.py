import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

def create_enrollment_visualizations():
    """Create comprehensive visualizations of enrollment patterns"""
    
    # Load enrolled students data (paths relative to project root)
    df = pd.read_csv('data/stonegrove_enrolled_students.csv')
    
    # Set up the plotting style
    plt.style.use('default')
    sns.set_palette("husl")
    
    # Create figure with multiple subplots
    fig = plt.figure(figsize=(20, 24))
    
    # 1. Program Distribution (Top 15)
    plt.subplot(4, 2, 1)
    program_counts = df['program_name'].value_counts().head(15)
    bars = plt.barh(range(len(program_counts)), program_counts.values)
    plt.yticks(range(len(program_counts)), program_counts.index, fontsize=8)
    plt.xlabel('Number of Students')
    plt.title('Top 15 Programs by Enrollment', fontsize=12, fontweight='bold')
    plt.gca().invert_yaxis()
    
    # Color bars by faculty
    faculty_colors = {'Faculty of Applied Forging': 'orange', 
                     'Faculty of Hearth and Transformation': 'green',
                     'Faculty of Integrative Inquiry': 'blue', 
                     'Faculty of Living Lore': 'purple'}
    
    for i, (program, count) in enumerate(program_counts.items()):
        faculty = df[df['program_name'] == program]['faculty'].iloc[0]
        bars[i].set_color(faculty_colors.get(faculty, 'gray'))
    
    # 2. Faculty Distribution
    plt.subplot(4, 2, 2)
    faculty_counts = df['faculty'].value_counts()
    colors = ['orange', 'green', 'blue', 'purple']
    plt.pie(faculty_counts.values, labels=faculty_counts.index, autopct='%1.1f%%', 
            colors=colors, startangle=90)
    plt.title('Student Distribution by Faculty', fontsize=12, fontweight='bold')
    
    # 3. Clan-Program Affinity Heatmap (Top 10 programs)
    plt.subplot(4, 2, 3)
    top_programs = df['program_name'].value_counts().head(10).index
    affinity_data = df[df['program_name'].isin(top_programs)].groupby(['clan', 'program_name'])['clan_affinity'].mean().unstack()
    
    sns.heatmap(affinity_data, annot=True, fmt='.2f', cmap='YlOrRd', cbar_kws={'label': 'Affinity Score'})
    plt.title('Clan-Program Affinity Heatmap (Top 10 Programs)', fontsize=12, fontweight='bold')
    plt.xlabel('Program')
    plt.ylabel('Clan')
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    
    # 4. Selection Probability Distribution
    plt.subplot(4, 2, 4)
    plt.hist(df['selection_probability'], bins=30, alpha=0.7, color='skyblue', edgecolor='black')
    plt.xlabel('Selection Probability')
    plt.ylabel('Number of Students')
    plt.title('Distribution of Program Selection Probabilities', fontsize=12, fontweight='bold')
    plt.axvline(df['selection_probability'].mean(), color='red', linestyle='--', 
                label=f'Mean: {df["selection_probability"].mean():.3f}')
    plt.legend()
    
    # 5. Clan Affinity by Race
    plt.subplot(4, 2, 5)
    race_affinity = df.groupby('race')['clan_affinity'].agg(['mean', 'std']).reset_index()
    x_pos = np.arange(len(race_affinity))
    plt.bar(x_pos, race_affinity['mean'], yerr=race_affinity['std'], 
            capsize=5, color=['orange', 'green'], alpha=0.7)
    plt.xlabel('Race')
    plt.ylabel('Average Clan Affinity')
    plt.title('Average Clan-Program Affinity by Race', fontsize=12, fontweight='bold')
    plt.xticks(x_pos, race_affinity['race'])
    
    # 6. Number of Year 1 Modules Distribution
    plt.subplot(4, 2, 6)
    module_counts = df['num_year1_modules'].value_counts().sort_index()
    plt.bar(module_counts.index, module_counts.values, color='lightcoral', alpha=0.7)
    plt.xlabel('Number of Year 1 Modules')
    plt.ylabel('Number of Students')
    plt.title('Distribution of Year 1 Modules per Student', fontsize=12, fontweight='bold')
    
    # 7. Clan Distribution
    plt.subplot(4, 2, 7)
    clan_counts = df['clan'].value_counts()
    plt.barh(range(len(clan_counts)), clan_counts.values, color='lightblue', alpha=0.7)
    plt.yticks(range(len(clan_counts)), clan_counts.index, fontsize=8)
    plt.xlabel('Number of Students')
    plt.title('Student Distribution by Clan', fontsize=12, fontweight='bold')
    plt.gca().invert_yaxis()
    
    # 8. Faculty-Program Relationship
    plt.subplot(4, 2, 8)
    faculty_program = df.groupby(['faculty', 'program_name']).size().reset_index(name='count')
    top_faculty_programs = faculty_program.nlargest(15, 'count')
    
    # Create a grouped bar chart
    faculties = top_faculty_programs['faculty'].unique()
    x = np.arange(len(faculties))
    width = 0.35
    
    for i, faculty in enumerate(faculties):
        faculty_data = top_faculty_programs[top_faculty_programs['faculty'] == faculty]
        if len(faculty_data) > 0:
            plt.bar(i, faculty_data['count'].iloc[0], 
                   color=faculty_colors.get(faculty, 'gray'), alpha=0.7,
                   label=faculty if i == 0 else "")
    
    plt.xlabel('Faculty')
    plt.ylabel('Number of Students')
    plt.title('Top Programs by Faculty', fontsize=12, fontweight='bold')
    plt.xticks(range(len(faculties)), [f.split()[-1] for f in faculties], rotation=45)
    plt.legend()
    
    plt.tight_layout()
    plt.savefig('visualizations/stonegrove_enrollment_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # Print summary statistics
    print("=== Enrollment Summary Statistics ===")
    print(f"Total students enrolled: {len(df)}")
    print(f"Total programs: {df['program_name'].nunique()}")
    print(f"Total faculties: {df['faculty'].nunique()}")
    print(f"Average clan affinity: {df['clan_affinity'].mean():.3f}")
    print(f"Average selection probability: {df['selection_probability'].mean():.3f}")
    print(f"Average Year 1 modules per student: {df['num_year1_modules'].mean():.1f}")
    
    print(f"\n=== Top 5 Programs ===")
    print(df['program_name'].value_counts().head())
    
    print(f"\n=== Faculty Distribution ===")
    print(df['faculty'].value_counts())
    
    print(f"\n=== Clan Affinity Analysis ===")
    clan_affinity_stats = df.groupby('clan')['clan_affinity'].agg(['mean', 'min', 'max', 'count']).round(3)
    print(clan_affinity_stats)

if __name__ == "__main__":
    create_enrollment_visualizations() 