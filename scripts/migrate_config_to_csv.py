#!/usr/bin/env python3
"""
Migrate module_characteristics and programme_characteristics from YAML to CSV.

Run from project root. Creates config/module_characteristics.csv and
config/programme_characteristics.csv from the YAML files.
"""

import yaml
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def migrate_module_characteristics():
    yaml_path = PROJECT_ROOT / 'config' / 'module_characteristics.yaml'
    csv_path = PROJECT_ROOT / 'config' / 'module_characteristics.csv'
    if not yaml_path.exists():
        print(f"  Skip: {yaml_path} not found")
        return
    with open(yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}
    rows = []
    for title, info in (data.get('modules') or {}).items():
        if isinstance(info, dict):
            rows.append({
                'module_title': title,
                'program': info.get('program', ''),
                'year': info.get('year', 1),
                'difficulty_level': info.get('difficulty_level', 0.5),
                'social_requirements': info.get('social_requirements', 0.5),
                'creativity_requirements': info.get('creativity_requirements', 0.5),
                'practical_theoretical_balance': info.get('practical_theoretical_balance', 0.5),
                'stress_level': info.get('stress_level', 0.5),
                'group_work_intensity': info.get('group_work_intensity', 0.5),
                'independent_study_requirement': info.get('independent_study_requirement', 0.5),
                'assessment_type': info.get('assessment_type', 'mixed'),
                'description': info.get('description', ''),
            })
    df = pd.DataFrame(rows)
    df.to_csv(csv_path, index=False)
    print(f"  Created {csv_path} ({len(df)} rows)")


def migrate_programme_characteristics():
    yaml_path = PROJECT_ROOT / 'config' / 'program_characteristics.yaml'
    csv_path = PROJECT_ROOT / 'config' / 'programme_characteristics.csv'
    if not yaml_path.exists():
        print(f"  Skip: {yaml_path} not found")
        return
    with open(yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}
    rows = []
    for pname, info in (data.get('programs') or {}).items():
        if isinstance(info, dict):
            chars = info.get('characteristics', {})
            rows.append({
                'programme_name': pname,
                'faculty': info.get('faculty', ''),
                'description': info.get('description', ''),
                'social_intensity': chars.get('social_intensity', 0.5),
                'practical_theoretical_balance': chars.get('practical_theoretical_balance', 0.5),
                'stress_level': chars.get('stress_level', 0.5),
                'career_prospects': chars.get('career_prospects', 0.5),
                'academic_difficulty': chars.get('academic_difficulty', 0.5),
                'creativity_requirement': chars.get('creativity_requirement', 0.5),
                'leadership_opportunities': chars.get('leadership_opportunities', 0.5),
                'research_intensity': chars.get('research_intensity', 0.5),
                'community_engagement': chars.get('community_engagement', 0.5),
                'innovation_focus': chars.get('innovation_focus', 0.5),
            })
    df = pd.DataFrame(rows)
    df.to_csv(csv_path, index=False)
    print(f"  Created {csv_path} ({len(df)} rows)")


def main():
    print("Migrating config YAML -> CSV")
    migrate_module_characteristics()
    migrate_programme_characteristics()
    print("Done.")


if __name__ == '__main__':
    main()
