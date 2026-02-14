"""
Analyze module difficulty patterns - feminist lens on domestic/applied.

This script documents the OLD keyword-based logic (pre feminist-aware fix)
for reference. The current difficulty estimation lives in
core_systems/engagement_system.py _estimate_module_characteristics().

Run from project root: python metaanalysis/difficulty_analysis.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import yaml

# Use the actual engagement system's logic
from core_systems.engagement_system import EngagementSystem

def main():
    es = EngagementSystem()
    weekly = pd.read_csv('data/stonegrove_weekly_engagement.csv')
    modules = weekly['module_title'].unique()

    results = []
    for m in sorted(modules):
        chars = es.get_module_characteristics(m)
        results.append({
            'module': m,
            'difficulty': chars['difficulty'],
            'social': chars['social_requirements'],
            'creativity': chars['creativity_requirements']
        })

    df = pd.DataFrame(results)

    print("=== CURRENT DIFFICULTY DISTRIBUTION (feminist-aware) ===")
    print(df['difficulty'].value_counts().sort_index())
    print()

    print("=== SAMPLE: Modules by difficulty ===")
    for _, r in df.sort_values('difficulty').head(15).iterrows():
        print(f"  {r['difficulty']:.2f}: {r['module'][:60]}")
    print("  ...")
    for _, r in df.sort_values('difficulty').tail(5).iterrows():
        print(f"  {r['difficulty']:.2f}: {r['module'][:60]}")

if __name__ == "__main__":
    main()
