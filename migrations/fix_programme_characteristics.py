#!/usr/bin/env python3
"""
Migration: fix programme_characteristics.csv.

- Removes 5 orphaned entries (names not in curriculum)
- Adds 13 missing programmes with values derived from faculty/department context
- Preserves all existing valid rows unchanged

Run once from project root.
"""

from pathlib import Path
import pandas as pd

PROJECT_ROOT  = Path(__file__).resolve().parent.parent
CURRICULUM    = PROJECT_ROOT / "Instructions and guides" / "Stonegrove_University_Curriculum.xlsx"
OUT_PATH      = PROJECT_ROOT / "config" / "programme_characteristics.csv"

# Values for the 13 missing programmes.
# Columns: social_intensity, practical_theoretical_balance, stress_level, career_prospects,
#          academic_difficulty, creativity_requirement, leadership_opportunities,
#          research_intensity, community_engagement, innovation_focus, description
MISSING = [
    # --- Faculty of Applied Forging: Forge Arts and Metallurgy ---
    dict(
        programme_name="Precision Smithing and Design",
        faculty="Faculty of Applied Forging",
        description="Advanced craft programme developing precision metalwork, design methodology, and technical mastery.",
        social_intensity=0.45, practical_theoretical_balance=0.90, stress_level=0.55,
        career_prospects=0.75, academic_difficulty=0.65, creativity_requirement=0.75,
        leadership_opportunities=0.45, research_intensity=0.40, community_engagement=0.40,
        innovation_focus=0.70,
    ),
    dict(
        programme_name="Hammercraft",
        faculty="Faculty of Applied Forging",
        description="Intensive hands-on programme in traditional hammer forging, rhythm, and embodied metal practice.",
        social_intensity=0.40, practical_theoretical_balance=0.92, stress_level=0.50,
        career_prospects=0.68, academic_difficulty=0.52, creativity_requirement=0.62,
        leadership_opportunities=0.35, research_intensity=0.25, community_engagement=0.45,
        innovation_focus=0.52,
    ),
    dict(
        programme_name="Artefact Restoration",
        faculty="Faculty of Applied Forging",
        description="Specialist programme in the ethical conservation and restoration of historical artefacts across materials.",
        social_intensity=0.50, practical_theoretical_balance=0.78, stress_level=0.55,
        career_prospects=0.65, academic_difficulty=0.65, creativity_requirement=0.70,
        leadership_opportunities=0.40, research_intensity=0.65, community_engagement=0.50,
        innovation_focus=0.55,
    ),
    # --- Faculty of Applied Forging: Mechanics and Engineering ---
    dict(
        programme_name="Logic & Leverage (Systems Engineering)",
        faculty="Faculty of Applied Forging",
        description="Systems engineering programme integrating logical analysis, mechanical design, and emergent complexity.",
        social_intensity=0.50, practical_theoretical_balance=0.72, stress_level=0.65,
        career_prospects=0.80, academic_difficulty=0.72, creativity_requirement=0.60,
        leadership_opportunities=0.65, research_intensity=0.60, community_engagement=0.45,
        innovation_focus=0.75,
    ),
    dict(
        programme_name="Hydraulics, Heuristics & Harmonics",
        faculty="Faculty of Applied Forging",
        description="Experimental engineering programme exploring fluid dynamics, acoustic structures, and intuitive design.",
        social_intensity=0.45, practical_theoretical_balance=0.75, stress_level=0.60,
        career_prospects=0.65, academic_difficulty=0.68, creativity_requirement=0.70,
        leadership_opportunities=0.45, research_intensity=0.55, community_engagement=0.40,
        innovation_focus=0.72,
    ),
    # --- Faculty of Applied Forging: Stonework and Structural Alchemy ---
    dict(
        programme_name="Living Stone Architecture",
        faculty="Faculty of Applied Forging",
        description="Architecture programme grounded in organic form, stone lore, sacred geometry, and ecosystem-aligned building.",
        social_intensity=0.55, practical_theoretical_balance=0.78, stress_level=0.60,
        career_prospects=0.70, academic_difficulty=0.65, creativity_requirement=0.82,
        leadership_opportunities=0.55, research_intensity=0.50, community_engagement=0.65,
        innovation_focus=0.75,
    ),
    dict(
        programme_name="Maintenance Rituals for Ancient Systems",
        faculty="Faculty of Applied Forging",
        description="Specialist programme in the care, ritual maintenance, and cultural stewardship of ancient built systems.",
        social_intensity=0.55, practical_theoretical_balance=0.82, stress_level=0.50,
        career_prospects=0.58, academic_difficulty=0.58, creativity_requirement=0.58,
        leadership_opportunities=0.45, research_intensity=0.55, community_engagement=0.65,
        innovation_focus=0.48,
    ),
    # --- Faculty of Hearth and Transformation: Education, Eldership, and Mentoring ---
    dict(
        programme_name="Radical Mentorship",
        faculty="Faculty of Hearth and Transformation",
        description="Relational programme exploring mentorship as political practice, transformative presence, and care.",
        social_intensity=0.88, practical_theoretical_balance=0.65, stress_level=0.50,
        career_prospects=0.55, academic_difficulty=0.55, creativity_requirement=0.60,
        leadership_opportunities=0.82, research_intensity=0.35, community_engagement=0.82,
        innovation_focus=0.60,
    ),
    # --- Faculty of Hearth and Transformation: Healing and Embodied Knowledge ---
    dict(
        programme_name="Dreaming and Somatic Inquiry",
        faculty="Faculty of Hearth and Transformation",
        description="Embodied inquiry programme exploring dreamwork, somatic practice, and the body as knowledge archive.",
        social_intensity=0.65, practical_theoretical_balance=0.60, stress_level=0.40,
        career_prospects=0.45, academic_difficulty=0.55, creativity_requirement=0.82,
        leadership_opportunities=0.40, research_intensity=0.50, community_engagement=0.55,
        innovation_focus=0.68,
    ),
    # --- Faculty of Hearth and Transformation: Hospitality and Conflict Holding ---
    dict(
        programme_name="Restorative Space Design",
        faculty="Faculty of Hearth and Transformation",
        description="Design programme focused on creating spaces that hold healing, transition, and communal restoration.",
        social_intensity=0.75, practical_theoretical_balance=0.70, stress_level=0.45,
        career_prospects=0.60, academic_difficulty=0.55, creativity_requirement=0.80,
        leadership_opportunities=0.55, research_intensity=0.45, community_engagement=0.72,
        innovation_focus=0.70,
    ),
    # --- Faculty of Hearth and Transformation: Rites, Rest, and Renewal ---
    dict(
        programme_name="Ceremonies",
        faculty="Faculty of Hearth and Transformation",
        description="Practice-based programme in the design, facilitation, and ethics of ceremonial and ritual forms.",
        social_intensity=0.85, practical_theoretical_balance=0.65, stress_level=0.45,
        career_prospects=0.50, academic_difficulty=0.55, creativity_requirement=0.80,
        leadership_opportunities=0.65, research_intensity=0.45, community_engagement=0.82,
        innovation_focus=0.65,
    ),
    dict(
        programme_name="Ancient Rites",
        faculty="Faculty of Hearth and Transformation",
        description="Scholarly and embodied study of historical rites across Elven, Dwarven, and other traditions.",
        social_intensity=0.75, practical_theoretical_balance=0.60, stress_level=0.45,
        career_prospects=0.45, academic_difficulty=0.60, creativity_requirement=0.72,
        leadership_opportunities=0.55, research_intensity=0.65, community_engagement=0.75,
        innovation_focus=0.55,
    ),
    # --- Faculty of Integrative Inquiry: Ecologies of Knowledge ---
    dict(
        programme_name="Indigenous and Folk Knowledge Systems",
        faculty="Faculty of Integrative Inquiry",
        description="Interdisciplinary programme engaging Indigenous and folk epistemologies, land-based knowledge, and oral traditions.",
        social_intensity=0.70, practical_theoretical_balance=0.42, stress_level=0.50,
        career_prospects=0.50, academic_difficulty=0.65, creativity_requirement=0.65,
        leadership_opportunities=0.50, research_intensity=0.72, community_engagement=0.82,
        innovation_focus=0.55,
    ),
]

ORPHANED = {
    "Food System Resilience",
    "Language and Symbol",
    "Lorekeeper Apprenticeship",
    "Strategic Rituals and Civic Memory",
    "Transdisciplinary Design and Praxis",
}


def main():
    existing = pd.read_csv(OUT_PATH)

    # Drop orphaned rows
    before = len(existing)
    existing = existing[~existing["programme_name"].isin(ORPHANED)].copy()
    print(f"Removed {before - len(existing)} orphaned rows.")

    # Add missing
    new_rows = pd.DataFrame(MISSING)
    combined = pd.concat([existing, new_rows], ignore_index=True)

    # Sort to match curriculum order
    progs = pd.read_excel(CURRICULUM, sheet_name="Programmes")
    order = list(progs["Programme"])
    combined["_sort"] = combined["programme_name"].map({v: i for i, v in enumerate(order)})
    combined = combined.sort_values("_sort").drop(columns=["_sort"]).reset_index(drop=True)

    combined.to_csv(OUT_PATH, index=False)
    print(f"Written: {OUT_PATH}")
    print(f"  {len(combined)} programmes (was {before})")

    # Verify against curriculum
    curriculum_names = set(progs["Programme"].str.strip())
    config_names     = set(combined["programme_name"].str.strip())
    still_missing  = curriculum_names - config_names
    still_orphaned = config_names - curriculum_names
    if still_missing:
        print(f"\nWARNING — still missing: {still_missing}")
    if still_orphaned:
        print(f"WARNING — still orphaned: {still_orphaned}")
    if not still_missing and not still_orphaned:
        print("\nAll 44 programmes matched.")


if __name__ == "__main__":
    main()
