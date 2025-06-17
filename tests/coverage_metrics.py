#!/usr/bin/env python
"""
Generate test metrics for pybeepop+
"""

import subprocess
import json
from pathlib import Path


def count_tests():
    """Count the number of tests in the test suite."""
    result = subprocess.run(["pytest", "--collect-only", "-q"], capture_output=True, text=True)

    # Parse output to count tests
    lines = result.stdout.strip().split("\n")
    test_count = 0
    for line in lines:
        if "collected" in line:
            # Format: "collected X items"
            test_count = int(line.split()[1])
            break

    return test_count


def get_coverage():
    """Run tests with coverage and return coverage percentage."""
    # Run tests with coverage
    subprocess.run(["pytest", "--cov=pybeepop", "--cov-report=json"], capture_output=True)

    # Read coverage report
    try:
        with open("coverage.json", "r") as f:
            coverage_data = json.load(f)
        return coverage_data["totals"]["percent_covered"]
    except:
        return None


def main():
    """Generate and print test metrics."""
    print("pybeepop+ Test Metrics")
    print("=" * 40)

    # Count tests
    test_count = count_tests()
    print(f"Total number of unit tests: {test_count}")

    # Get coverage
    coverage = get_coverage()
    if coverage:
        print(f"Test coverage: {coverage:.1f}%")
    else:
        print("Coverage data not available")

    # Count test files
    test_dir = Path(__file__).parent  # This will always be the /tests folder
    test_files = list(test_dir.glob("test_*.py"))
    print(f"Number of test files: {len(test_files)}")


if __name__ == "__main__":
    main()
