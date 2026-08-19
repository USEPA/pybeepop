"""Regenerate the golden output fixtures used by test_golden_output.py.

Run this ONLY when a model change is intended to alter output:

    python tests/regenerate_golden.py

Every regenerated file must be reviewed as part of the change. The whole point of the
fixtures is that unintended output changes show up as a diff, so a regeneration commit
that is not explained by the accompanying code change is a red flag.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from golden_scenarios import GOLDEN_DIR, SCENARIOS, build_model, golden_path  # noqa: E402


def main():
    GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
    for name in SCENARIOS:
        results = build_model(name)
        path = golden_path(name)
        existed = path.exists()
        results.to_csv(path, index=False, float_format="%.10g")
        print(
            f"{'updated' if existed else 'created'} {path.relative_to(Path.cwd())} "
            f"({len(results)} rows x {len(results.columns)} columns)"
        )
    print("\nReview every diff before committing.")


if __name__ == "__main__":
    main()
