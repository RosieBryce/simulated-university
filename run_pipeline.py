#!/usr/bin/env python3
"""
Run the full Stonegrove University simulation pipeline.

Execute from project root. Runs in order:
  1. Student generation (individual_students)
  2. Program enrollment (enrolled_students)
  3. Engagement (weekly + semester engagement)
  4. Assessment (assessment_events)
"""

import subprocess
import sys
from pathlib import Path

# Project root = parent of this script
PROJECT_ROOT = Path(__file__).resolve().parent

STEPS = [
    ("Student generation", ["core_systems/student_generation_pipeline.py"]),
    ("Program enrollment", ["core_systems/program_enrollment_system.py"]),
    ("Engagement", ["core_systems/engagement_system.py"]),
    ("Assessment", ["core_systems/assessment_system.py"]),
]


def main():
    print("Stonegrove University pipeline")
    print("=" * 40)
    import os
    os.chdir(PROJECT_ROOT)
    for i, (name, args) in enumerate(STEPS, 1):
        print(f"\n[{i}/{len(STEPS)}] {name}...")
        cmd = [sys.executable] + args
        result = subprocess.run(cmd, cwd=PROJECT_ROOT)
        if result.returncode != 0:
            print(f"Pipeline failed at step {i} ({name}). Exit code: {result.returncode}")
            sys.exit(result.returncode)
    print("\n" + "=" * 40)
    print("Pipeline complete.")


if __name__ == "__main__":
    main()
