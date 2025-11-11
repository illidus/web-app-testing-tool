#!/usr/bin/env python3
"""
Generate bug packets (Markdown files) for failed tests.
Each bug packet contains all the information needed to paste into GitLab.
"""

import json
import re
import sys
import io
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# Set UTF-8 encoding for Windows console to support emojis
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def sanitize_filename(s: str) -> str:
    """Sanitize a string to be safe for use as a filename."""
    s = re.sub(r'[<>:"/\\|?*]', '_', s)
    s = s.replace(' ', '_')
    s = re.sub(r'[^a-zA-Z0-9_\-.]', '', s)
    return s[:200]


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
    Same logic as in summarize.py.
    """
    try:
        if '[' in test_id:
            param_part = test_id.split('[')[1].rstrip(']')
            parts = param_part.split('_')

            role = parts[0]

            rep_idx = -1
            for i, part in enumerate(parts):
                if part.startswith('rep'):
                    rep_idx = i
                    break

            if rep_idx == -1:
                flags = '_'.join(parts[1:-1])
                dataset = parts[-1]
                repeat = '0'
            else:
                repeat = parts[rep_idx][3:]
                dataset = parts[rep_idx - 1]
                flags = '_'.join(parts[1:rep_idx - 1]) if rep_idx > 2 else ''

            return {
                'role': role,
                'flags': flags or 'noflags',
                'dataset': dataset,
                'repeat': repeat
            }
        else:
            return {
                'role': 'unknown',
                'flags': 'unknown',
                'dataset': 'unknown',
                'repeat': '0'
            }
    except Exception as e:
        return {
            'role': 'unknown',
            'flags': 'unknown',
            'dataset': 'unknown',
            'repeat': '0'
        }


def find_artifact_files(base_dir: Path, test_id: str, parsed: Dict[str, str]) -> Dict[str, Path]:
    """
    Find artifact files (screenshot, trace, log) for a given test.
    Returns paths if they exist, None otherwise.
    """
    artifacts = {
        'screenshot': None,
        'trace': None,
        'log': None,
    }

    # Try to find files matching the test
    # Files are named with pattern: role_flags_dataset_repN_timestamp.*
    pattern_base = f"{parsed['role']}_{parsed['flags']}_{parsed['dataset']}_rep{parsed['repeat']}"

    screenshots_dir = base_dir / "out" / "screenshots"
    traces_dir = base_dir / "out" / "traces"
    out_dir = base_dir / "out"

    # Find screenshot
    if screenshots_dir.exists():
        for f in screenshots_dir.glob(f"{pattern_base}_*.png"):
            artifacts['screenshot'] = f
            break

    # Find trace
    if traces_dir.exists():
        for f in traces_dir.glob(f"{pattern_base}_*.zip"):
            artifacts['trace'] = f
            break

    # Find log
    if out_dir.exists():
        for f in out_dir.glob(f"{pattern_base}_*.log"):
            artifacts['log'] = f
            break

    return artifacts


def generate_bug_packet(test: Dict[str, Any], base_dir: Path, bugs_dir: Path) -> Path:
    """
    Generate a bug packet Markdown file for a failed test.
    Returns the path to the created file.
    """
    test_id = test.get('nodeid', 'unknown')
    parsed = parse_test_id(test_id)

    # Find artifacts
    artifacts = find_artifact_files(base_dir, test_id, parsed)

    # Extract failure information
    failure_msg = ""
    if 'call' in test and 'longrepr' in test['call']:
        failure_msg = test['call']['longrepr']
    elif 'longrepr' in test:
        failure_msg = test['longrepr']

    # Create bug packet
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    bug_id = sanitize_filename(f"{parsed['role']}_{parsed['flags']}_{parsed['dataset']}_rep{parsed['repeat']}")

    bug_file = bugs_dir / f"bug_{bug_id}.md"

    with open(bug_file, 'w', encoding='utf-8') as f:
        f.write("# Bug Report: Upload Workflow Failure\n\n")

        # Metadata
        f.write("## Metadata\n\n")
        f.write(f"- **Generated:** {timestamp}\n")
        f.write(f"- **Test ID:** `{test_id}`\n")
        f.write(f"- **Duration:** {test.get('duration', 0):.2f}s\n")
        f.write("\n")

        # Test Configuration
        f.write("## Test Configuration\n\n")
        f.write(f"- **Role:** {parsed['role']}\n")
        f.write(f"- **Feature Flags:** {parsed['flags']}\n")
        f.write(f"- **Dataset:** {parsed['dataset']}\n")
        f.write(f"- **Repeat:** {parsed['repeat']}\n")
        f.write("\n")

        # Failure Description
        f.write("## Failure Description\n\n")
        f.write("```\n")
        f.write(failure_msg or "No failure message available")
        f.write("\n```\n\n")

        # Artifacts
        f.write("## Artifacts\n\n")

        if artifacts['screenshot']:
            f.write(f"- **Screenshot:** `{artifacts['screenshot'].relative_to(base_dir)}`\n")
        else:
            f.write("- **Screenshot:** Not available\n")

        if artifacts['trace']:
            f.write(f"- **Playwright Trace:** `{artifacts['trace'].relative_to(base_dir)}`\n")
            f.write("  - View with: `playwright show-trace {}`\n".format(artifacts['trace']))
        else:
            f.write("- **Playwright Trace:** Not available\n")

        if artifacts['log']:
            f.write(f"- **Log File:** `{artifacts['log'].relative_to(base_dir)}`\n")
        else:
            f.write("- **Log File:** Not available\n")

        f.write("\n")

        # Reproduction Steps
        f.write("## Reproduction Steps\n\n")
        f.write("To reproduce this failure:\n\n")
        f.write("```bash\n")
        f.write(f"# Run the specific test\n")
        f.write(f"pytest -k '{bug_id}' -v\n")
        f.write("\n")
        f.write("# Or run with specific parameters\n")
        f.write(f"# Role: {parsed['role']}\n")
        f.write(f"# Flags: {parsed['flags']}\n")
        f.write(f"# Dataset: {parsed['dataset']}\n")
        f.write("```\n\n")

        # Log Excerpt (if available)
        if artifacts['log'] and artifacts['log'].exists():
            f.write("## Log Excerpt\n\n")
            try:
                with open(artifacts['log'], 'r') as log_file:
                    log_content = log_file.read()
                    # Cap at 5000 characters
                    if len(log_content) > 5000:
                        log_content = log_content[:5000] + "\n\n... [TRUNCATED]"
                    f.write("```\n")
                    f.write(log_content)
                    f.write("\n```\n\n")
            except Exception as e:
                f.write(f"*Could not read log file: {e}*\n\n")

        # Investigation Notes
        f.write("## Investigation Notes\n\n")
        f.write("*TODO: Add investigation notes here*\n\n")
        f.write("- [ ] Reviewed screenshot\n")
        f.write("- [ ] Reviewed Playwright trace\n")
        f.write("- [ ] Reviewed logs\n")
        f.write("- [ ] Identified root cause\n")
        f.write("- [ ] Created fix\n")
        f.write("\n")

        # Labels
        f.write("## Suggested Labels\n\n")
        f.write("`bug`, `test-failure`, `upload-workflow`")

        # Add role-specific label
        if parsed['role'] != 'unknown':
            f.write(f", `role-{parsed['role']}`")

        # Add flag-specific labels
        if parsed['flags'] and parsed['flags'] != 'noflags':
            for flag in parsed['flags'].split('_'):
                if '=' in flag:
                    flag_name = flag.split('=')[0]
                    f.write(f", `flag-{flag_name}`")

        f.write("\n\n")

        # Footer
        f.write("---\n\n")
        f.write("*Generated by tools/mk_bug_packets.py*\n")

    return bug_file


def main():
    """Main entry point."""
    # Paths
    base_dir = Path(__file__).parent.parent
    results_path = base_dir / "out" / "results.json"
    bugs_dir = base_dir / "bugs"

    # Ensure bugs directory exists
    bugs_dir.mkdir(exist_ok=True)

    print("🐛 Generating bug packets from test failures...")

    # Load results
    results = load_results(results_path)

    # Find failed tests
    failed_tests = [
        test for test in results.get('tests', [])
        if test.get('outcome') == 'failed'
    ]

    if not failed_tests:
        print("✅ No failed tests found. No bug packets to generate.")
        return 0

    print(f"   Found {len(failed_tests)} failed test(s)")

    # Generate bug packet for each failure
    generated_files = []
    for test in failed_tests:
        try:
            bug_file = generate_bug_packet(test, base_dir, bugs_dir)
            generated_files.append(bug_file)
            print(f"   ✓ Generated: {bug_file.name}")
        except Exception as e:
            print(f"   ⚠️  Failed to generate bug packet for {test.get('nodeid', 'unknown')}: {e}")

    print(f"\n✅ Generated {len(generated_files)} bug packet(s) in {bugs_dir}/")
    print(f"\n📋 Next steps:")
    print(f"   1. Review bug packets in {bugs_dir}/")
    print(f"   2. Copy relevant packets to GitLab issues")
    print(f"   3. Attach screenshots and traces as needed")

    return 0


if __name__ == '__main__':
    sys.exit(main())
