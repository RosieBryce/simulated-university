# Longitudinal Pipeline Flow

End-to-end trace of student data through the pipeline, with focus on `student_id` and duplicate-column handling.

## 1. Main Loop (run_longitudinal_pipeline.py)

For each academic year:
- **New cohort**: `generate_students(n=COHORT_SIZE)` → no student_id
- **Continuing students**: `progression_prev` (enrolled/repeating) merged with `prev_enrolled_df`
- Calls `run_year(acad_year, year_index, new_students, continuing_students, progression_prev, seed)`

## 2. New Students Path

```
generate_students(n)          → traits only, no student_id
↓
Pipeline assigns: new_students_df["student_id"] = range(offset, offset + len)
  (offset = year_index * COHORT_SIZE, e.g. year 0: 0–499, year 1: 500–999)
↓
enroll_students_batch(new_students_df)
  - Uses student_id from input (pipeline assigns before calling)
  - Merges enrollment_df onto students_df on student_id → single student_id column
  - Returns: student traits + enrollment cols, one student_id column
```

## 3. Continuing Students Path

```
progression_prev[status in enrolled|repeating]
↓
Merge with prev_enrolled_df (drop prog-specific cols from prev first)
  - active.merge(prev, on="student_id") → one student_id (merge key)
↓
enroll_continuing_students(cont)
  - Uses row.get("student_id", idx) — should add Series handling for robustness
  - Merge on student_id → single student_id
  - Returns: one row per continuing student, one student_id column
```

## 4. Combined Enrolled

```
enrolled_df = concat([_dedup_cols(new_enrolled), _dedup_cols(continuing_enrolled)], ignore_index=True)
  - Both inputs have single student_id
  - _dedup_cols removes any duplicate column names
  - Index 0,1,2,... does NOT equal student_id (continuing students have varied ids)
```

## 5. Downstream Systems

All receive `enrolled_clean` (deduplicated columns). Built once after concat, passed to engagement → assessment → progression.

| System | Input | student_id source | Notes |
|--------|-------|-------------------|-------|
| **Engagement** | enrolled_clean | `student.get('student_id', idx)` with Series handling | Was using idx; fixed to use actual student_id |
| **Assessment** | enrolled_clean | `student.get('student_id', idx)` with Series handling | Robust to duplicate columns |
| **Progression** | enrolled_clean, assessment_df | From assessment agg; itertuples for scalars | agg deduped; student_lookup from enrolled_clean |

## 6. Output Concatenation

- `all_enrollment`: each year deduped before append
- `all_progression`: each year from compute_progression (clean)
- Final CSVs: `pd.concat(..., ignore_index=True).to_csv()`
