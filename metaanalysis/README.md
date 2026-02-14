# Metaanalysis

Cross-cutting analysis scripts and outputs that synthesise results across the Stonegrove modeling pipeline.

## Purpose

- **Validation**: Check model outputs for realism, consistency, and edge cases
- **Cross-system insights**: Compare patterns across student generation, enrollment, engagement, and (future) assessment
- **Documentation**: Generate summary statistics and figures for reports
- **Pick-up context**: Run analyses to understand current state after time away

## Contents (planned)

| File | Purpose |
|------|---------|
| `validate_model_outputs.py` | Sanity checks on generated data (distributions, correlations, missing values) |
| `cross_system_summary.py` | Combine insights across pipeline stages |
| `difficulty_analysis.py` | Module difficulty distribution using current (feminist-aware) algorithm |
| `engagement_visualization.py` | Engagement visualizations (trends, clan/race analysis, personality correlations) |
| `outputs/` | Generated reports, summary tables, validation logs |

## Usage

Run from project root:

```bash
python metaanalysis/difficulty_analysis.py
python metaanalysis/engagement_visualization.py
# python metaanalysis/validate_model_outputs.py   # (planned)
# python metaanalysis/cross_system_summary.py     # (planned)
```

## Relationship to Other Folders

- **data/** – Reads generated CSVs; does not write (except metaanalysis-specific outputs)
- **visualizations/** – Analysis produces figures; metaanalysis focuses on validation and summary
- **config/** – May reference config for validation rules
