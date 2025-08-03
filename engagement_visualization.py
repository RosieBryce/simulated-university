import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

def create_engagement_visualizations():
    """Create comprehensive visualizations of engagement patterns"""
    
    # Load engagement data
    weekly_df = pd.read_csv('stonegrove_weekly_engagement.csv')
    semester_df = pd.read_csv('stonegrove_semester_engagement.csv')
    enrolled_df = pd.read_csv('stonegrove_enrolled_students.csv')
    
    # Merge with student data for analysis
    semester_analysis = semester_df.merge(enrolled_df[['student_id', 'clan', 'race', 'gender', 'disabilities']], 
                                        left_on='student_id', right_on='student_id', how='left')
    
    # Set up the plotting style
    plt.style.use('default')
    sns.set_palette("husl")
    
    # Create figure with multiple subplots
    fig = plt.figure(figsize=(20, 24))
    
    # 1. Weekly Engagement Trends Over Time
    plt.subplot(4, 3, 1)
    weekly_avg = weekly_df.groupby('week_number')[['attendance_rate', 'participation_score', 
                                                  'academic_engagement', 'social_engagement']].mean()
    weekly_avg.plot(ax=plt.gca(), marker='o', markersize=4)
    plt.title('Weekly Engagement Trends', fontsize=12, fontweight='bold')
    plt.xlabel('Week Number')
    plt.ylabel('Engagement Score')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, alpha=0.3)
    
    # 2. Stress Level Trends Over Time
    plt.subplot(4, 3, 2)
    stress_trend = weekly_df.groupby('week_number')['stress_level'].mean()
    plt.plot(stress_trend.index, stress_trend.values, marker='o', color='red', linewidth=2)
    plt.title('Weekly Stress Level Trends', fontsize=12, fontweight='bold')
    plt.xlabel('Week Number')
    plt.ylabel('Stress Level')
    plt.grid(True, alpha=0.3)
    
    # 3. Engagement Distribution by Clan
    plt.subplot(4, 3, 3)
    clan_engagement = semester_analysis.groupby('clan')['average_attendance'].mean().sort_values(ascending=True)
    plt.barh(range(len(clan_engagement)), clan_engagement.values, color='skyblue', alpha=0.7)
    plt.yticks(range(len(clan_engagement)), clan_engagement.index, fontsize=8)
    plt.xlabel('Average Attendance Rate')
    plt.title('Average Attendance by Clan', fontsize=12, fontweight='bold')
    plt.gca().invert_yaxis()
    
    # 4. Engagement vs Personality Traits
    plt.subplot(4, 3, 4)
    # Get personality columns
    personality_cols = [col for col in enrolled_df.columns if col.startswith('refined_')]
    engagement_personality = semester_df.merge(enrolled_df[['student_id'] + personality_cols], 
                                             left_on='student_id', right_on='student_id', how='left')
    
    # Plot conscientiousness vs attendance
    plt.scatter(engagement_personality['refined_conscientiousness'], 
               engagement_personality['average_attendance'], alpha=0.6, color='blue')
    plt.xlabel('Conscientiousness')
    plt.ylabel('Average Attendance')
    plt.title('Conscientiousness vs Attendance', fontsize=12, fontweight='bold')
    plt.grid(True, alpha=0.3)
    
    # 5. Extraversion vs Participation
    plt.subplot(4, 3, 5)
    plt.scatter(engagement_personality['refined_extraversion'], 
               engagement_personality['average_participation'], alpha=0.6, color='green')
    plt.xlabel('Extraversion')
    plt.ylabel('Average Participation')
    plt.title('Extraversion vs Participation', fontsize=12, fontweight='bold')
    plt.grid(True, alpha=0.3)
    
    # 6. Openness vs Academic Engagement
    plt.subplot(4, 3, 6)
    plt.scatter(engagement_personality['refined_openness'], 
               engagement_personality['average_academic_engagement'], alpha=0.6, color='purple')
    plt.xlabel('Openness')
    plt.ylabel('Average Academic Engagement')
    plt.title('Openness vs Academic Engagement', fontsize=12, fontweight='bold')
    plt.grid(True, alpha=0.3)
    
    # 7. Engagement Distribution by Race
    plt.subplot(4, 3, 7)
    race_engagement = semester_analysis.groupby('race')[['average_attendance', 'average_participation', 
                                                        'average_academic_engagement', 'average_social_engagement']].mean()
    race_engagement.plot(kind='bar', ax=plt.gca(), alpha=0.7)
    plt.title('Engagement by Race', fontsize=12, fontweight='bold')
    plt.xlabel('Race')
    plt.ylabel('Engagement Score')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.xticks(rotation=0)
    
    # 8. Stress Level Distribution
    plt.subplot(4, 3, 8)
    plt.hist(semester_df['average_stress_level'], bins=30, alpha=0.7, color='red', edgecolor='black')
    plt.xlabel('Average Stress Level')
    plt.ylabel('Number of Students')
    plt.title('Distribution of Average Stress Levels', fontsize=12, fontweight='bold')
    plt.axvline(semester_df['average_stress_level'].mean(), color='blue', linestyle='--', 
                label=f'Mean: {semester_df["average_stress_level"].mean():.3f}')
    plt.legend()
    
    # 9. Engagement Trends Distribution
    plt.subplot(4, 3, 9)
    trend_counts = semester_df['engagement_trend'].value_counts()
    colors = ['green', 'red', 'orange']
    plt.pie(trend_counts.values, labels=trend_counts.index, autopct='%1.1f%%', 
            colors=colors, startangle=90)
    plt.title('Engagement Trends Distribution', fontsize=12, fontweight='bold')
    
    # 10. Risk Factors Analysis
    plt.subplot(4, 3, 10)
    risk_counts = semester_df['risk_factors'].value_counts().head(8)
    plt.barh(range(len(risk_counts)), risk_counts.values, color='lightcoral', alpha=0.7)
    plt.yticks(range(len(risk_counts)), risk_counts.index, fontsize=8)
    plt.xlabel('Number of Students')
    plt.title('Top Risk Factors', fontsize=12, fontweight='bold')
    plt.gca().invert_yaxis()
    
    # 11. Module Difficulty vs Engagement
    plt.subplot(4, 3, 11)
    module_engagement = weekly_df.groupby('module_title')[['attendance_rate', 'participation_score', 
                                                          'academic_engagement', 'module_difficulty']].mean()
    # Filter out any NaN values
    module_engagement = module_engagement.dropna()
    if len(module_engagement) > 0:
        plt.scatter(module_engagement['module_difficulty'], module_engagement['attendance_rate'], 
                   alpha=0.6, color='brown')
        plt.xlabel('Module Difficulty')
        plt.ylabel('Average Attendance Rate')
        plt.title('Module Difficulty vs Attendance', fontsize=12, fontweight='bold')
        plt.grid(True, alpha=0.3)
    
    # 12. Social Requirements vs Participation
    plt.subplot(4, 3, 12)
    module_engagement_social = weekly_df.groupby('module_title')[['participation_score', 'module_social_requirements']].mean()
    # Filter out any NaN values
    module_engagement_social = module_engagement_social.dropna()
    if len(module_engagement_social) > 0:
        plt.scatter(module_engagement_social['module_social_requirements'], module_engagement_social['participation_score'], 
                   alpha=0.6, color='teal')
        plt.xlabel('Module Social Requirements')
        plt.ylabel('Average Participation Score')
        plt.title('Social Requirements vs Participation', fontsize=12, fontweight='bold')
        plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('stonegrove_engagement_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # Print summary statistics
    print("=== Engagement Summary Statistics ===")
    print(f"Total weekly engagement records: {len(weekly_df)}")
    print(f"Total semester engagement records: {len(semester_df)}")
    print(f"Average attendance rate: {semester_df['average_attendance'].mean():.3f}")
    print(f"Average participation score: {semester_df['average_participation'].mean():.3f}")
    print(f"Average academic engagement: {semester_df['average_academic_engagement'].mean():.3f}")
    print(f"Average social engagement: {semester_df['average_social_engagement'].mean():.3f}")
    print(f"Average stress level: {semester_df['average_stress_level'].mean():.3f}")
    
    print(f"\n=== Engagement Trends ===")
    print(semester_df['engagement_trend'].value_counts())
    
    print(f"\n=== Top Risk Factors ===")
    print(semester_df['risk_factors'].value_counts().head())
    
    print(f"\n=== Clan Engagement Analysis ===")
    clan_stats = semester_analysis.groupby('clan')[['average_attendance', 'average_participation', 
                                                   'average_academic_engagement', 'average_stress_level']].agg(['mean', 'std']).round(3)
    print(clan_stats)
    
    # Correlation analysis
    print(f"\n=== Personality-Engagement Correlations ===")
    correlation_data = engagement_personality[personality_cols + ['average_attendance', 'average_participation', 
                                                                 'average_academic_engagement', 'average_social_engagement']]
    correlations = correlation_data.corr()
    
    # Show key correlations
    key_correlations = [
        ('refined_conscientiousness', 'average_attendance'),
        ('refined_extraversion', 'average_participation'),
        ('refined_openness', 'average_academic_engagement'),
        ('refined_agreeableness', 'average_social_engagement'),
        ('refined_neuroticism', 'average_stress_level')
    ]
    
    for trait, engagement in key_correlations:
        if trait in correlations.index and engagement in correlations.columns:
            corr_value = correlations.loc[trait, engagement]
            print(f"{trait} vs {engagement}: {corr_value:.3f}")

if __name__ == "__main__":
    create_engagement_visualizations() 