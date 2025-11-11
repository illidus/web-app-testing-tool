#!/usr/bin/env python3
"""
Summarize test results from pytest-json-report output.
Generates a summary.md file with pass rates and flake detection.
"""

import json
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any
from datetime import datetime


def load_results(results_path: Path) -> Dict[str, Any]:
    """Load the pytest JSON report."""
    if not results_path.exists():
        print(f"❌ Error: Results file not found: {results_path}")
        print("   Run 'pytest' first to generate results.")
        sys.exit(1)

    with open(results_path, 'r') as f:
        return json.load(f)


def parse_test_id(test_id: str) -> Dict[str, str]:
    """
    Parse a parametrized test ID into components.

    Example: test_bulk.py::test_upload_workflow[analyst_fast_preprocess=on_acme_small_ok_rep0]
    Returns: {
        'role': 'analyst',
        'flags': 'fast_preprocess=on',
        'dataset': 'acme_small_ok',
        'repeat': '0'
    }
    """
    try:
        # Extract the parameter part from brackets
        if '[' in test_id:
            param_part = test_id.split('[')[1].rstrip(']')
            parts = param_part.split('_')

            # Parse components
            role = parts[0]

            # Find where rep starts
            rep_idx = -1
            for i, part in enumerate(parts):
                if part.startswith('rep'):
                    rep_idx = i
                    break

            if rep_idx == -1:
                # No repeat found, assume last part is dataset
                flags = '_'.join(parts[1:-1])
                dataset = parts[-1]
                repeat = '0'
            else:
                repeat = parts[rep_idx][3:]  # Remove 'rep' prefix
                dataset = parts[rep_idx - 1]
                flags = '_'.join(parts[1:rep_idx - 1]) if rep_idx > 2 else ''

            return {
                'role': role,
                'flags': flags or 'noflags',
                'dataset': dataset,
                'repeat': repeat
            }
        else:
            # Non-parametrized test
            return {
                'role': 'unknown',
                'flags': 'unknown',
                'dataset': 'unknown',
                'repeat': '0'
            }
    except Exception as e:
        print(f"⚠️  Warning: Could not parse test ID: {test_id} ({e})")
        return {
            'role': 'unknown',
            'flags': 'unknown',
            'dataset': 'unknown',
            'repeat': '0'
        }


def analyze_results(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze test results and detect flakes.

    Returns a dictionary with:
    - total_tests: Total number of tests
    - passed: Number of passed tests
    - failed: Number of failed tests
    - skipped: Number of skipped tests
    - duration: Total duration
    - permutations: Dict of permutation -> list of outcomes
    - flaky_permutations: List of permutations with mixed results
    """
    analysis = {
        'total_tests': results.get('summary', {}).get('total', 0),
        'passed': results.get('summary', {}).get('passed', 0),
        'failed': results.get('summary', {}).get('failed', 0),
        'skipped': results.get('summary', {}).get('skipped', 0),
        'duration': results.get('duration', 0),
        'permutations': defaultdict(list),
        'flaky_permutations': [],
    }

    # Process each test
    for test in results.get('tests', []):
        test_id = test.get('nodeid', '')
        outcome = test.get('outcome', 'unknown')

        # Parse test ID to get permutation (without repeat)
        parsed = parse_test_id(test_id)
        permutation = f"{parsed['role']}_{parsed['flags']}_{parsed['dataset']}"

        # Record outcome for this permutation
        analysis['permutations'][permutation].append({
            'outcome': outcome,
            'repeat': parsed['repeat'],
            'test_id': test_id,
            'duration': test.get('duration', 0),
        })

    # Detect flakes: permutations with mixed pass/fail outcomes
    for permutation, outcomes in analysis['permutations'].items():
        outcome_set = set(o['outcome'] for o in outcomes)

        # Skip if all skipped
        if outcome_set == {'skipped'}:
            continue

        # Flaky if we have both passed and failed
        if 'passed' in outcome_set and 'failed' in outcome_set:
            analysis['flaky_permutations'].append({
                'permutation': permutation,
                'outcomes': outcomes,
                'pass_count': sum(1 for o in outcomes if o['outcome'] == 'passed'),
                'fail_count': sum(1 for o in outcomes if o['outcome'] == 'failed'),
            })

    return analysis


def generate_summary_markdown(analysis: Dict[str, Any], output_path: Path):
    """Generate a Markdown summary report."""
    with open(output_path, 'w') as f:
        f.write("# Bulk Upload Workflow Test Summary\n\n")

        # Timestamp
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # Overall statistics
        f.write("## Overall Statistics\n\n")
        f.write(f"- **Total Tests:** {analysis['total_tests']}\n")
        f.write(f"- **Passed:** {analysis['passed']} ✅\n")
        f.write(f"- **Failed:** {analysis['failed']} ❌\n")
        f.write(f"- **Skipped:** {analysis['skipped']} ⏭️\n")
        f.write(f"- **Duration:** {analysis['duration']:.2f}s\n\n")

        # Pass rate
        if analysis['total_tests'] > 0:
            pass_rate = (analysis['passed'] / analysis['total_tests']) * 100
            f.write(f"**Pass Rate:** {pass_rate:.1f}%\n\n")

        # Flaky tests
        if analysis['flaky_permutations']:
            f.write("## ⚠️ Flaky Permutations Detected\n\n")
            f.write("The following permutations had mixed pass/fail results across repeats:\n\n")

            for flaky in analysis['flaky_permutations']:
                f.write(f"### {flaky['permutation']} **(FLAKY)**\n\n")
                f.write(f"- Pass count: {flaky['pass_count']}\n")
                f.write(f"- Fail count: {flaky['fail_count']}\n\n")

                f.write("Outcomes by repeat:\n\n")
                for outcome in flaky['outcomes']:
                    icon = "✅" if outcome['outcome'] == 'passed' else "❌"
                    f.write(f"- Repeat {outcome['repeat']}: {icon} {outcome['outcome']}\n")
                f.write("\n")
        else:
            f.write("## ✅ No Flaky Tests Detected\n\n")
            f.write("All test permutations had consistent results across repeats.\n\n")

        # Permutation results
        f.write("## Permutation Results\n\n")

        # Group by pass/fail
        passed_perms = []
        failed_perms = []
        skipped_perms = []

        for permutation, outcomes in sorted(analysis['permutations'].items()):
            outcome_set = set(o['outcome'] for o in outcomes)

            if outcome_set == {'passed'}:
                passed_perms.append((permutation, outcomes))
            elif outcome_set == {'skipped'}:
                skipped_perms.append((permutation, outcomes))
            elif 'failed' in outcome_set:
                failed_perms.append((permutation, outcomes))

        # Passed permutations
        if passed_perms:
            f.write("### ✅ Passed Permutations\n\n")
            for permutation, outcomes in passed_perms:
                avg_duration = sum(o['duration'] for o in outcomes) / len(outcomes)
                f.write(f"- `{permutation}` ({len(outcomes)} repeats, avg {avg_duration:.2f}s)\n")
            f.write("\n")

        # Failed permutations
        if failed_perms:
            f.write("### ❌ Failed Permutations\n\n")
            for permutation, outcomes in failed_perms:
                fail_count = sum(1 for o in outcomes if o['outcome'] == 'failed')
                f.write(f"- `{permutation}` ({fail_count}/{len(outcomes)} failures)\n")
            f.write("\n")

        # Skipped permutations
        if skipped_perms:
            f.write("### ⏭️ Skipped Permutations\n\n")
            for permutation, outcomes in skipped_perms:
                f.write(f"- `{permutation}` ({len(outcomes)} repeats)\n")
            f.write("\n")

        # Recommendations
        f.write("## Recommendations\n\n")

        if analysis['flaky_permutations']:
            f.write("1. **Investigate flaky tests** - These permutations have inconsistent behavior\n")
            f.write("2. Review trace files and screenshots in `out/traces/` and `out/screenshots/`\n")
            f.write("3. Check bug packets in `bugs/` directory\n\n")
        elif analysis['failed'] > 0:
            f.write("1. **Review failed tests** - Check bug packets in `bugs/` directory\n")
            f.write("2. Examine screenshots and traces in `out/` directory\n\n")
        else:
            f.write("✅ All tests passed! No action required.\n\n")

        f.write("---\n\n")
        f.write("*Generated by tools/summarize.py*\n")


def main():
    """Main entry point."""
    # Paths
    base_dir = Path(__file__).parent.parent
    results_path = base_dir / "out" / "results.json"
    output_path = base_dir / "out" / "summary.md"

    print("📊 Analyzing test results...")

    # Load and analyze results
    results = load_results(results_path)
    analysis = analyze_results(results)

    # Generate summary
    generate_summary_markdown(analysis, output_path)

    print(f"✅ Summary generated: {output_path}")
    print(f"\n📈 Results:")
    print(f"   Total: {analysis['total_tests']}")
    print(f"   Passed: {analysis['passed']}")
    print(f"   Failed: {analysis['failed']}")
    print(f"   Skipped: {analysis['skipped']}")

    if analysis['flaky_permutations']:
        print(f"\n⚠️  {len(analysis['flaky_permutations'])} flaky permutation(s) detected!")

    return 0 if analysis['failed'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
