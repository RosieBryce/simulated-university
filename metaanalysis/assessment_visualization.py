"""
Assessment marks visualization - distribution across demographics, faculties, etc.
Run from project root: python metaanalysis/assessment_visualization.py
"""
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for script runs
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path


def create_assessment_visualizations():
    """Create visualizations of assessment mark distributions across demographics and faculties."""
    
    # Load data (paths relative to project root)
    assessment_df = pd.read_csv('data/stonegrove_assessment_events.csv')
    enrolled_df = pd.read_csv('data/stonegrove_enrolled_students.csv')
    
    # Merge with student demographics
    demo_cols = ['student_id', 'species', 'clan', 'gender', 'education', 'socio_economic_rank', 
                 'disabilities', 'faculty', 'program_name']
    demo_cols = [c for c in demo_cols if c in enrolled_df.columns]
    df = assessment_df.merge(enrolled_df[demo_cols], on='student_id', how='left')
    
    # Simplify disability for analysis
    df['has_disability'] = ~df['disabilities'].fillna('').str.contains('no_known_disabilities', case=False, na=False)
    
    # Ensure visualizations dir exists
    Path('visualizations').mkdir(exist_ok=True)
    
    plt.style.use('default')
    sns.set_palette("husl")
    
    fig = plt.figure(figsize=(20, 24))
    
    # 1. Overall mark distribution (histogram)
    ax1 = plt.subplot(4, 3, 1)
    ax1.hist(df['assessment_mark'], bins=30, alpha=0.7, color='steelblue', edgecolor='black')
    ax1.axvline(df['assessment_mark'].mean(), color='red', linestyle='--', 
                label=f'Mean: {df["assessment_mark"].mean():.1f}')
    ax1.set_xlabel('Assessment Mark')
    ax1.set_ylabel('Count')
    ax1.set_title('Overall Mark Distribution', fontsize=12, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. Grade distribution
    ax2 = plt.subplot(4, 3, 2)
    grade_order = ['First', '2:1', '2:2', 'Third', 'Fail']
    grade_counts = df['grade'].value_counts().reindex(grade_order).fillna(0)
    colors = ['gold', 'silver', 'sienna', 'tan', 'coral']
    ax2.bar(range(len(grade_counts)), grade_counts.values, color=colors[:len(grade_counts)], alpha=0.8)
    ax2.set_xticks(range(len(grade_counts)))
    ax2.set_xticklabels(grade_counts.index)
    ax2.set_xlabel('Grade')
    ax2.set_ylabel('Count')
    ax2.set_title('Grade Distribution', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='y')
    
    # 3. Marks by species
    ax3 = plt.subplot(4, 3, 3)
    sns.boxplot(data=df, x='species', y='assessment_mark', ax=ax3)
    ax3.set_xlabel('Species')
    ax3.set_ylabel('Assessment Mark')
    ax3.set_title('Marks by Species', fontsize=12, fontweight='bold')
    ax3.grid(True, alpha=0.3, axis='y')
    
    # 4. Marks by gender
    ax4 = plt.subplot(4, 3, 4)
    sns.boxplot(data=df, x='gender', y='assessment_mark', ax=ax4)
    ax4.set_xlabel('Gender')
    ax4.set_ylabel('Assessment Mark')
    ax4.set_title('Marks by Gender', fontsize=12, fontweight='bold')
    ax4.grid(True, alpha=0.3, axis='y')
    
    # 5. Marks by faculty
    ax5 = plt.subplot(4, 3, 5)
    faculty_order = df.groupby('faculty')['assessment_mark'].mean().sort_values(ascending=False).index
    sns.boxplot(data=df, x='faculty', y='assessment_mark', order=faculty_order, ax=ax5)
    ax5.tick_params(axis='x', rotation=30)
    ax5.set_xlabel('Faculty')
    ax5.set_ylabel('Assessment Mark')
    ax5.set_title('Marks by Faculty', fontsize=12, fontweight='bold')
    ax5.grid(True, alpha=0.3, axis='y')
    
    # 6. Marks by education
    ax6 = plt.subplot(4, 3, 6)
    sns.boxplot(data=df, x='education', y='assessment_mark', ax=ax6)
    ax6.tick_params(axis='x', rotation=20)
    ax6.set_xlabel('Prior Education')
    ax6.set_ylabel('Assessment Mark')
    ax6.set_title('Marks by Prior Education', fontsize=12, fontweight='bold')
    ax6.grid(True, alpha=0.3, axis='y')
    
    # 7. Marks by socio-economic rank
    ax7 = plt.subplot(4, 3, 7)
    df_rank = df.copy()
    df_rank['socio_economic_rank'] = df_rank['socio_economic_rank'].astype(int)
    sns.boxplot(data=df_rank, x='socio_economic_rank', y='assessment_mark', ax=ax7)
    ax7.set_xlabel('Socio-Economic Rank (1=lowest)')
    ax7.set_ylabel('Assessment Mark')
    ax7.set_title('Marks by Socio-Economic Rank', fontsize=12, fontweight='bold')
    ax7.grid(True, alpha=0.3, axis='y')
    
    # 8. Marks by disability status
    ax8 = plt.subplot(4, 3, 8)
    df['disability_status'] = df['has_disability'].map({True: 'With disability', False: 'No known disability'})
    sns.boxplot(data=df, x='disability_status', y='assessment_mark', ax=ax8)
    ax8.set_xlabel('Disability Status')
    ax8.set_ylabel('Assessment Mark')
    ax8.set_title('Marks by Disability Status', fontsize=12, fontweight='bold')
    ax8.grid(True, alpha=0.3, axis='y')
    
    # 9. Marks by assessment type
    ax9 = plt.subplot(4, 3, 9)
    sns.boxplot(data=df, x='assessment_type', y='assessment_mark', ax=ax9)
    ax9.set_xlabel('Assessment Type')
    ax9.set_ylabel('Assessment Mark')
    ax9.set_title('Marks by Assessment Type', fontsize=12, fontweight='bold')
    ax9.grid(True, alpha=0.3, axis='y')
    
    # 10. Marks by clan (top 10 clans by count)
    ax10 = plt.subplot(4, 3, 10)
    top_clans = df['clan'].value_counts().head(10).index
    df_clan = df[df['clan'].isin(top_clans)]
    clan_order = df_clan.groupby('clan')['assessment_mark'].mean().sort_values(ascending=True).index
    sns.boxplot(data=df_clan, y='clan', x='assessment_mark', order=clan_order, ax=ax10)
    ax10.set_xlabel('Assessment Mark')
    ax10.set_ylabel('Clan')
    ax10.set_title('Marks by Clan (top 10)', fontsize=12, fontweight='bold')
    ax10.grid(True, alpha=0.3, axis='x')
    
    # 11. Faculty mean marks (bar chart)
    ax11 = plt.subplot(4, 3, 11)
    faculty_means = df.groupby('faculty')['assessment_mark'].mean().sort_values(ascending=True)
    bars = ax11.barh(range(len(faculty_means)), faculty_means.values, color='teal', alpha=0.7)
    ax11.set_yticks(range(len(faculty_means)))
    ax11.set_yticklabels([f.replace('Faculty of ', '') for f in faculty_means.index], fontsize=9)
    ax11.set_xlabel('Mean Assessment Mark')
    ax11.set_title('Mean Marks by Faculty', fontsize=12, fontweight='bold')
    ax11.axvline(df['assessment_mark'].mean(), color='red', linestyle='--', alpha=0.7)
    ax11.grid(True, alpha=0.3, axis='x')
    
    # 12. Species × Faculty heatmap (mean marks)
    ax12 = plt.subplot(4, 3, 12)
    pivot = df.pivot_table(values='assessment_mark', index='species', columns='faculty', aggfunc='mean')
    pivot.columns = [c.replace('Faculty of ', '')[:15] for c in pivot.columns]
    sns.heatmap(pivot, annot=True, fmt='.1f', cmap='RdYlGn', center=60, ax=ax12, cbar_kws={'label': 'Mean Mark'})
    ax12.set_title('Mean Marks: Species × Faculty', fontsize=12, fontweight='bold')
    ax12.tick_params(axis='x', rotation=30)
    
    plt.tight_layout()
    out_path = Path('visualizations/stonegrove_assessment_analysis.png')
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    # Print summary
    print("=== Assessment Mark Summary ===")
    print(f"Total assessment events: {len(df)}")
    print(f"Mean mark: {df['assessment_mark'].mean():.2f}")
    print(f"Std: {df['assessment_mark'].std():.2f}")
    print(f"\nGrade distribution:")
    print(df['grade'].value_counts().sort_index())
    print(f"\nMean mark by species:")
    print(df.groupby('species')['assessment_mark'].agg(['mean', 'count']).round(2))
    print(f"\nMean mark by faculty:")
    print(df.groupby('faculty')['assessment_mark'].agg(['mean', 'count']).round(2))
    print(f"\nMean mark by disability status:")
    print(df.groupby('disability_status')['assessment_mark'].agg(['mean', 'count']).round(2))
    print(f"\nSaved to {out_path}")


if __name__ == "__main__":
    create_assessment_visualizations()
