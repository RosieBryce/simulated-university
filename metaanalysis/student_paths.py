"""
Stonegrove University — Student Paths Validation Script

Reads progression and individual student data to produce:
1. Per-student year-by-year trajectory view
2. Aggregate path archetype distribution
3. Species / SES breakdowns
4. Sample case studies: withdrawal, repeater-graduate, straight-through high-performer

Run from project root:
    python metaanalysis/student_paths.py
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

DATA_DIR = PROJECT_ROOT / "data"


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_data():
    prog_path = DATA_DIR / "stonegrove_progression_outcomes.csv"
    indiv_path = DATA_DIR / "stonegrove_individual_students.csv"
    assess_path = DATA_DIR / "stonegrove_assessment_events.csv"

    if not prog_path.exists():
        raise FileNotFoundError(f"Progression file not found: {prog_path}")
    if not indiv_path.exists():
        raise FileNotFoundError(f"Individual students file not found: {indiv_path}")

    prog = pd.read_csv(prog_path)
    indiv = pd.read_csv(indiv_path)

    # Assessment: per-student per-year avg/min (FINAL rows only, use combined_mark)
    assess_agg = None
    if assess_path.exists():
        assess = pd.read_csv(assess_path)
        if 'component_code' in assess.columns:
            assess = assess[assess['component_code'] == 'FINAL'].copy()
        if 'combined_mark' in assess.columns:
            assess['mark'] = assess['combined_mark'].fillna(assess['assessment_mark'])
        else:
            assess['mark'] = assess['assessment_mark']
        assess_agg = (
            assess.groupby(['student_id', 'academic_year'])
            .agg(avg_mark=('mark', 'mean'), min_mark=('mark', 'min'))
            .reset_index()
        )
        assess_agg['student_id'] = assess_agg['student_id'].astype(str)

    prog['student_id'] = prog['student_id'].astype(str)
    indiv['student_id'] = indiv['student_id'].astype(str)

    # Deduplicate individual students: one record per student_id (take first academic year)
    indiv_dedup = indiv.sort_values('academic_year').drop_duplicates('student_id')

    return prog, indiv_dedup, assess_agg


# ---------------------------------------------------------------------------
# Path archetype classification
# ---------------------------------------------------------------------------

def classify_path(student_history: pd.DataFrame) -> str:
    """
    Classify a student's journey into one of these archetypes:
      - straight_through: graduated with no repeating years
      - repeat_graduate_1: one repeat year then graduated
      - repeat_graduate_2plus: two or more repeat years then graduated
      - repeat_then_withdraw: had at least one repeat, then withdrew
      - withdraw_yr1 / withdraw_yr2 / withdraw_yr3: withdrew (no repeat) from that year
      - still_enrolled: no terminal outcome yet
    """
    # Sort by academic_year
    hist = student_history.sort_values('academic_year')
    statuses = hist['status'].tolist()
    years = hist['programme_year_next'].tolist()  # can be NaN
    prog_years = []
    # use programme_year from hist if available
    if 'programme_year' in hist.columns:
        prog_years = hist['programme_year'].tolist()

    final_status = statuses[-1] if statuses else 'unknown'
    n_repeats = statuses.count('repeating')
    withdrew = 'withdrawn' in statuses
    graduated = 'graduated' in statuses

    if graduated:
        if n_repeats == 0:
            return 'straight_through'
        elif n_repeats == 1:
            return 'repeat_graduate_1'
        else:
            return 'repeat_graduate_2plus'

    if withdrew:
        if n_repeats > 0:
            return 'repeat_then_withdraw'
        # Determine year of withdrawal
        withdraw_idx = next((i for i, s in enumerate(statuses) if s == 'withdrawn'), None)
        if withdraw_idx is not None and prog_years:
            wy = prog_years[withdraw_idx] if withdraw_idx < len(prog_years) else None
            if wy == 1:
                return 'withdraw_yr1'
            elif wy == 2:
                return 'withdraw_yr2'
            elif wy == 3:
                return 'withdraw_yr3'
        return 'withdraw_yr1'  # default if year unknown

    # No terminal outcome
    if final_status in ('enrolled', 'repeating'):
        return 'still_enrolled'

    return 'unknown'


# ---------------------------------------------------------------------------
# Per-student trajectory
# ---------------------------------------------------------------------------

def build_trajectories(prog: pd.DataFrame, indiv: pd.DataFrame,
                        assess_agg: pd.DataFrame | None) -> pd.DataFrame:
    """Build a per-student trajectory table with path archetype and summary stats."""
    # Sort progression by student then year
    prog_sorted = prog.sort_values(['student_id', 'academic_year'])

    rows = []
    for sid, grp in prog_sorted.groupby('student_id'):
        archetype = classify_path(grp)
        student_info = indiv[indiv['student_id'] == sid]

        species = student_info['species'].iloc[0] if len(student_info) > 0 else 'unknown'
        clan = student_info['clan'].iloc[0] if len(student_info) > 0 else 'unknown'
        ses = int(student_info['socio_economic_rank'].iloc[0]) if len(student_info) > 0 else 0
        prog_code = grp['programme_code'].iloc[0] if 'programme_code' in grp.columns else '?'

        # Summary marks (from progression agg or assess_agg)
        if assess_agg is not None:
            student_assess = assess_agg[assess_agg['student_id'] == sid]
            overall_avg = round(student_assess['avg_mark'].mean(), 1) if len(student_assess) > 0 else None
        else:
            overall_avg = round(grp['avg_mark'].mean(), 1) if 'avg_mark' in grp.columns else None

        rows.append({
            'student_id': sid,
            'species': species,
            'clan': clan,
            'ses': ses,
            'programme_code': prog_code,
            'n_years': len(grp),
            'n_repeats': list(grp['status']).count('repeating'),
            'final_status': grp.sort_values('academic_year')['status'].iloc[-1],
            'archetype': archetype,
            'overall_avg_mark': overall_avg,
        })

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Printing helpers
# ---------------------------------------------------------------------------

def _bar(count: int, total: int, width: int = 30) -> str:
    if total == 0:
        return ' ' * width
    filled = round(count / total * width)
    return '#' * filled + '.' * (width - filled)


def print_per_student_sample(prog: pd.DataFrame, traj: pd.DataFrame,
                              assess_agg: pd.DataFrame | None, n: int = 10):
    """Print year-by-year path for a sample of students."""
    print("\n" + "=" * 70)
    print("PER-STUDENT TRAJECTORY SAMPLE (first 10 students by id)")
    print("=" * 70)

    sample_ids = traj.sort_values('student_id')['student_id'].head(n).tolist()
    prog_sorted = prog.sort_values(['student_id', 'academic_year'])

    for sid in sample_ids:
        row = traj[traj['student_id'] == sid].iloc[0]
        print(f"\nStudent {sid:>6} | {row['species']:<6} | {row['clan']:<14} | "
              f"SES {row['ses']} | {row['programme_code']}")

        grp = prog_sorted[prog_sorted['student_id'] == sid]
        for _, yr in grp.iterrows():
            ay = yr['academic_year']
            pyr = int(yr.get('programme_year', '?')) if pd.notna(yr.get('programme_year')) else '?'
            status = yr['status']
            avg = round(yr['avg_mark'], 1) if pd.notna(yr.get('avg_mark')) else '?'
            mn = round(yr['min_mark'], 1) if pd.notna(yr.get('min_mark')) else '?'
            outcome = yr.get('year_outcome', '?')
            next_yr = yr.get('programme_year_next')
            next_yr_str = str(int(next_yr)) if pd.notna(next_yr) else '?'
            arrow = {
                'enrolled': f'-> PASS -> enrolled Yr{next_yr_str}',
                'repeating': '-> FAIL -> repeating',
                'withdrawn': '-> WITHDRAWN',
                'graduated': '-> GRADUATED',
            }.get(status, f'-> {status}')
            print(f"  {ay}  Yr{pyr}  avg {avg:>5}  min {mn:>5}  {outcome:<5}  {arrow}")


def print_aggregate_distributions(traj: pd.DataFrame):
    """Print path archetype distribution.

    Reports two rates:
    - % of all students (raw, includes still_enrolled truncation)
    - % of terminal students only (meaningful headline figure)
    """
    print("\n" + "=" * 70)
    print("AGGREGATE PATH DISTRIBUTIONS")
    print("=" * 70)

    archetype_order = [
        'straight_through', 'repeat_graduate_1', 'repeat_graduate_2plus',
        'repeat_then_withdraw', 'withdraw_yr1', 'withdraw_yr2', 'withdraw_yr3',
        'still_enrolled', 'unknown',
    ]
    terminal_archetypes = [
        'straight_through', 'repeat_graduate_1', 'repeat_graduate_2plus',
        'repeat_then_withdraw', 'withdraw_yr1', 'withdraw_yr2', 'withdraw_yr3',
    ]

    counts = traj['archetype'].value_counts()
    total = len(traj)
    n_terminal = traj[traj['archetype'].isin(terminal_archetypes)].shape[0]
    n_still = counts.get('still_enrolled', 0)

    print(f"\n  Total students:   {total}")
    print(f"  Terminal:         {n_terminal}  (reached graduation, withdrawal, or final year)")
    print(f"  Still enrolled:   {n_still}  (longitudinal truncation -- later cohorts mid-journey)")
    print(f"\n  NOTE: '% of terminal' is the meaningful headline rate.")
    print(f"        '% of all' is diluted by the {n_still/total*100:.0f}% still enrolled.\n")

    print(f"  {'Archetype':<28} {'Count':>6}  {'% all':>6}  {'% terminal':>10}  {'Distribution (of terminal)'}")
    print("  " + "-" * 76)
    for arch in archetype_order:
        n = counts.get(arch, 0)
        pct_all = n / total * 100 if total > 0 else 0
        if arch == 'still_enrolled' or arch == 'unknown':
            pct_term = None
            bar = _bar(0, 1)
        else:
            pct_term = n / n_terminal * 100 if n_terminal > 0 else 0
            bar = _bar(n, n_terminal)
        pct_term_str = f"{pct_term:>9.1f}%" if pct_term is not None else f"{'--':>9}"
        print(f"  {arch:<28} {n:>6}  {pct_all:>5.1f}%  {pct_term_str}  {bar}")


def print_breakdowns(traj: pd.DataFrame):
    """Print archetype frequencies by species and SES quintile."""
    print("\n" + "=" * 70)
    print("BREAKDOWNS BY SPECIES AND SES QUINTILE")
    print("=" * 70)

    # By species
    print("\n--- By Species ---")
    terminal = ['straight_through', 'repeat_graduate_1', 'repeat_graduate_2plus',
                'repeat_then_withdraw', 'withdraw_yr1', 'withdraw_yr2', 'withdraw_yr3']
    grad_archetypes = ['straight_through', 'repeat_graduate_1', 'repeat_graduate_2plus']
    withdraw_archetypes = ['repeat_then_withdraw', 'withdraw_yr1', 'withdraw_yr2', 'withdraw_yr3']

    for species, grp in traj.groupby('species'):
        n = len(grp)
        n_terminal = grp[grp['archetype'].isin(terminal)]
        n_grad = grp[grp['archetype'].isin(grad_archetypes)]
        n_withdraw = grp[grp['archetype'].isin(withdraw_archetypes)]
        n_enrolled = grp[grp['archetype'] == 'still_enrolled']
        avg_mark = grp['overall_avg_mark'].mean()
        print(f"  {species:<8}  n={n:>4}  "
              f"graduated={len(n_grad)/n*100:>5.1f}%  "
              f"withdrawn={len(n_withdraw)/n*100:>5.1f}%  "
              f"still enrolled={len(n_enrolled)/n*100:>5.1f}%  "
              f"avg_mark={avg_mark:.1f}")

    # By SES quintile (top 20% vs bottom 20%)
    print("\n--- By SES Quintile ---")
    traj['ses_quintile'] = pd.qcut(traj['ses'], q=5, labels=['Q1 (lowest)', 'Q2', 'Q3', 'Q4', 'Q5 (highest)'])
    for qt, grp in traj.groupby('ses_quintile', observed=True):
        n = len(grp)
        n_grad = grp[grp['archetype'].isin(grad_archetypes)]
        n_withdraw = grp[grp['archetype'].isin(withdraw_archetypes)]
        avg_mark = grp['overall_avg_mark'].mean()
        print(f"  {str(qt):<14}  n={n:>4}  "
              f"graduated={len(n_grad)/n*100:>5.1f}%  "
              f"withdrawn={len(n_withdraw)/n*100:>5.1f}%  "
              f"avg_mark={avg_mark:.1f}")


def print_case_studies(prog: pd.DataFrame, traj: pd.DataFrame, seed: int = 42):
    """Print 3 sample case studies each for: withdrawal, repeater-graduate, straight-through high-performer."""
    rng = np.random.default_rng(seed)
    print("\n" + "=" * 70)
    print("SAMPLE CASE STUDIES")
    print("=" * 70)

    def pick_samples(archetype_filter, n=3, extra_filter=None):
        pool = traj[traj['archetype'].isin(archetype_filter)]
        if extra_filter is not None:
            pool = pool[extra_filter(pool)]
        if len(pool) == 0:
            return []
        idx = rng.choice(len(pool), size=min(n, len(pool)), replace=False)
        return pool.iloc[idx]['student_id'].tolist()

    prog_sorted = prog.sort_values(['student_id', 'academic_year'])

    def print_student(sid):
        row = traj[traj['student_id'] == sid].iloc[0]
        print(f"\n  Student {sid} | {row['species']} | {row['clan']} | "
              f"SES {row['ses']} | {row['programme_code']} | archetype: {row['archetype']}")
        grp = prog_sorted[prog_sorted['student_id'] == sid]
        for _, yr in grp.iterrows():
            pyr = int(yr.get('programme_year', 0)) if pd.notna(yr.get('programme_year')) else '?'
            avg = f"{yr['avg_mark']:.1f}" if pd.notna(yr.get('avg_mark')) else '?'
            status = yr['status']
            outcome = yr.get('year_outcome', '?')
            print(f"    {yr['academic_year']}  Yr{pyr}  avg={avg:<5}  {outcome:<5}  -> {status}")

    # (a) Withdrawals
    print("\n  --- (a) Withdrawals ---")
    withdrawal_archetypes = ['withdraw_yr1', 'withdraw_yr2', 'withdraw_yr3', 'repeat_then_withdraw']
    sids = pick_samples(withdrawal_archetypes)
    if sids:
        for sid in sids:
            print_student(sid)
    else:
        print("  (no withdrawals found in data)")

    # (b) Repeater-graduates
    print("\n  --- (b) Repeater-Graduates ---")
    repeater_archetypes = ['repeat_graduate_1', 'repeat_graduate_2plus']
    sids = pick_samples(repeater_archetypes)
    if sids:
        for sid in sids:
            print_student(sid)
    else:
        print("  (no repeater-graduates found in data)")

    # (c) Straight-through high-performers (avg_mark >= 65)
    print("\n  --- (c) Straight-Through High-Performers (avg mark >= 65) ---")
    sids = pick_samples(
        ['straight_through'],
        extra_filter=lambda df: df['overall_avg_mark'] >= 65,
    )
    if sids:
        for sid in sids:
            print_student(sid)
    else:
        # Relax threshold if none found
        sids = pick_samples(['straight_through'])
        if sids:
            print("  (relaxed threshold — showing straight-through graduates)")
            for sid in sids:
                print_student(sid)
        else:
            print("  (no straight-through graduates found in data yet — may need more years)")


def print_coherence_checks(prog: pd.DataFrame, traj: pd.DataFrame):
    """Basic coherence checks: no Yr3 without passing Yr1+Yr2; graduates only after Yr3 pass."""
    print("\n" + "=" * 70)
    print("COHERENCE CHECKS")
    print("=" * 70)

    issues = []

    # Check: students who reach programme_year 3 should have had programme_year 1 and 2 in their history
    prog_sorted = prog.sort_values(['student_id', 'academic_year'])
    for sid, grp in prog_sorted.groupby('student_id'):
        years_seen = set(grp.get('programme_year', pd.Series(dtype=int)).dropna().astype(int).tolist()
                         if 'programme_year' in grp.columns else [])
        if 3 in years_seen and 1 not in years_seen:
            issues.append(f"Student {sid}: reached Yr3 without Yr1 record")
        if 3 in years_seen and 2 not in years_seen:
            issues.append(f"Student {sid}: reached Yr3 without Yr2 record")

    # Check: graduates must have had a Yr3 pass
    graduated_sids = traj[traj['archetype'].isin(
        ['straight_through', 'repeat_graduate_1', 'repeat_graduate_2plus']
    )]['student_id'].tolist()
    for sid in graduated_sids:
        grp = prog_sorted[prog_sorted['student_id'] == sid]
        yr3 = grp[grp.get('programme_year', pd.Series(dtype=int)) == 3] if 'programme_year' in grp.columns else pd.DataFrame()
        if len(yr3) == 0:
            issues.append(f"Student {sid}: classified as graduated but no Yr3 record found")
        elif not (yr3['year_outcome'] == 'pass').any():
            issues.append(f"Student {sid}: classified as graduated but Yr3 outcome not 'pass'")

    if issues:
        print(f"\n  ISSUES FOUND ({len(issues)}):")
        for issue in issues[:20]:
            print(f"  WARN  {issue}")
        if len(issues) > 20:
            print(f"  ... and {len(issues) - 20} more")
    else:
        print("\n  OK All coherence checks passed.")
        print("    - No student in Yr3 without Yr1+Yr2 records")
        print("    - All graduates have a Yr3 pass record")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("Stonegrove University — Student Path Analysis")
    print("=" * 70)

    prog, indiv, assess_agg = load_data()
    print(f"Loaded: {len(prog)} progression records, "
          f"{len(indiv)} students, "
          f"{'assessment data' if assess_agg is not None else 'no assessment file'}")

    # Add programme_year to progression if available from enrollment
    enroll_path = DATA_DIR / "stonegrove_enrollment.csv"
    if enroll_path.exists():
        enroll = pd.read_csv(enroll_path)
        enroll['student_id'] = enroll['student_id'].astype(str)
        # programme_year
        if 'programme_year' not in prog.columns and 'programme_year' in enroll.columns:
            prog = prog.merge(
                enroll[['student_id', 'academic_year', 'programme_year']].drop_duplicates(),
                on=['student_id', 'academic_year'], how='left',
            )
        # programme_code (enrollment uses 'program_code')
        if 'programme_code' not in prog.columns:
            code_col = 'programme_code' if 'programme_code' in enroll.columns else 'program_code'
            if code_col in enroll.columns:
                tmp = enroll[['student_id', 'academic_year', code_col]].drop_duplicates()
                tmp = tmp.rename(columns={code_col: 'programme_code'})
                prog = prog.merge(tmp, on=['student_id', 'academic_year'], how='left')

    traj = build_trajectories(prog, indiv, assess_agg)
    print(f"Built trajectories for {len(traj)} unique students")

    print_per_student_sample(prog, traj, assess_agg)
    print_aggregate_distributions(traj)
    print_breakdowns(traj)
    print_case_studies(prog, traj)
    print_coherence_checks(prog, traj)

    print("\n" + "=" * 70)
    print("Done.")


if __name__ == "__main__":
    main()
