# Bulk Upload Workflow Test Runner (Staging)

A comprehensive test automation framework for executing bulk upload workflow tests across multiple datasets, roles, and feature flags in parallel.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Requirements](#requirements)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Usage](#usage)
- [Architecture](#architecture)
- [Artifacts](#artifacts)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)

## Overview

This test runner executes the **Cartesian product** of:
- **Roles** (analyst, admin, etc.)
- **Feature flag combinations** (on/off permutations)
- **Datasets** (synthetic, sanitized, real-sensitive)
- **Repeats** (for flake detection)

It runs tests in parallel, captures rich debugging artifacts on failures, and generates:
- Pass/fail summary with flake detection
- Bug-ready Markdown packets for developers

## Features

- ✅ **Parallel Execution** - Uses pytest-xdist for fast test runs
- ✅ **Flake Detection** - Runs each permutation multiple times to catch intermittent failures
- ✅ **Rich Artifacts** - Captures screenshots, Playwright traces, and DOM snapshots on failure
- ✅ **Bug Packets** - Auto-generates Markdown files ready to paste into GitLab
- ✅ **Safety First** - Sensitive datasets excluded by default
- ✅ **Configurable** - Everything controlled via `catalog.yml` and `.env`
- ✅ **Page Objects** - Maintainable, reusable page abstractions
- ✅ **No Runtime LLM** - Fully deterministic, no external AI calls during test runs

## Requirements

- Python 3.10+
- Playwright
- Access to staging environment (inside VPN)
- Valid service account credentials

## Quick Start

### 1. Install Dependencies

```bash
cd bulk-runner

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install Python packages
pip install -r requirements.txt

# Install Playwright browsers
python -m playwright install
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your actual credentials
nano .env  # or vim, code, etc.
```

Required variables:
```bash
BASE_URL=https://staging.internal
ANALYST_USER=svc_analyst
ANALYST_PASS=your_password_here
ADMIN_USER=svc_admin
ADMIN_PASS=your_password_here
```

### 3. Prepare Test Datasets

Place your test datasets in the `datasets/` directory according to the structure defined in `catalog.yml`.

See [datasets/README.md](datasets/README.md) for details on creating test datasets.

### 4. Run Tests

```bash
# Run all tests in parallel
pytest -n auto

# Generate summary report
python tools/summarize.py

# Generate bug packets for failures
python tools/mk_bug_packets.py

# View results
cat out/summary.md
ls bugs/
```

### 5. Review Results

- **Summary**: `out/summary.md` - Pass rates and flaky test detection
- **Bug Packets**: `bugs/*.md` - One file per failure, ready for GitLab
- **Artifacts**: `out/screenshots/` and `out/traces/` - Debug artifacts

## Configuration

### catalog.yml

The authoritative test matrix configuration. Defines:

- **Roles**: User roles to test (analyst, admin, etc.)
- **Flags**: Feature flags and their values
- **Datasets**: Test data files with expected outcomes
- **Repeats**: Number of times to run each permutation
- **Selectors**: CSS selectors for page elements
- **Timeouts**: Timeout values for various operations

Example:

```yaml
roles:
  - analyst
  - admin

flags:
  - name: fast_preprocess
    values: [off, on]

datasets:
  - id: acme_small_ok
    path: datasets/acme/small_ok.zip
    classification: synthetic
    expected: success

repeats: 3
```

### .env

Environment-specific configuration:

- `BASE_URL`: Application URL
- `{ROLE}_USER`: Username for each role
- `{ROLE}_PASS`: Password for each role
- `INCLUDE_SENSITIVE`: Enable real-sensitive datasets (default: false)
- `PYTEST_WORKERS`: Override worker count (default: auto)
- `HEADED_BROWSER`: Run browser in headed mode (default: false)

## Usage

### Basic Commands

```bash
# Run all tests
pytest -n auto

# Run with specific worker count
pytest -n 4

# Run in headed mode (see browser)
pytest --headed

# Run with slow motion (for debugging)
pytest --slow-mo 1000

# Include sensitive datasets
pytest --include-sensitive

# Run specific test pattern
pytest -k "analyst_fast"

# Run smoke test only
pytest -k smoke

# Verbose output
pytest -v

# Very verbose output
pytest -vv
```

### Generating Reports

```bash
# Generate summary
python tools/summarize.py

# Generate bug packets
python tools/mk_bug_packets.py

# Do both
python tools/summarize.py && python tools/mk_bug_packets.py
```

### Complete Workflow

```bash
# 1. Ensure environment is configured
export $(grep -v '^#' .env | xargs)

# 2. Run tests
pytest -n auto

# 3. Generate reports
python tools/summarize.py
python tools/mk_bug_packets.py

# 4. Review results
cat out/summary.md

# 5. Copy bug packets to GitLab
# (Manually copy from bugs/*.md to GitLab issues)
```

## Architecture

### Project Structure

```
bulk-runner/
├── catalog.yml           # Test matrix configuration
├── requirements.txt      # Python dependencies
├── pytest.ini           # Pytest configuration
├── .env.example         # Environment template
├── conftest.py          # Test fixtures and matrix generation
├── pages/               # Page objects (POM pattern)
│   ├── login_page.py
│   └── upload_page.py
├── tests/               # Test implementations
│   └── test_bulk.py
├── tools/               # Post-processing utilities
│   ├── summarize.py     # Generate summary.md
│   └── mk_bug_packets.py # Generate bug packets
├── datasets/            # Test data files
│   ├── acme/
│   └── beta/
└── out/                 # Test results and artifacts (gitignored)
    ├── results.json
    ├── summary.md
    ├── screenshots/
    └── traces/
```

### Test Flow

1. **Matrix Generation** (`conftest.py`)
   - Reads `catalog.yml`
   - Filters datasets by classification
   - Generates Cartesian product of permutations
   - Parametrizes tests

2. **Test Execution** (`test_bulk.py`)
   - Login with role credentials
   - Navigate to upload page
   - Set feature flags
   - Upload dataset file
   - Submit for preprocessing
   - Wait for expected outcome
   - Assert result matches expectation

3. **Failure Handling** (`conftest.py` hooks)
   - Capture screenshot
   - Save Playwright trace
   - Extract page content (capped)
   - Save to artifact files

4. **Post-Processing** (`tools/`)
   - Parse pytest JSON results
   - Detect flaky tests (mixed pass/fail)
   - Generate summary report
   - Create bug packets with all context

### Page Object Pattern

The framework uses the Page Object Model (POM) for maintainability:

- **LoginPage** (`pages/login_page.py`)
  - `navigate()` - Go to login page
  - `login(username, password)` - Perform login
  - `is_logged_in()` - Check login state

- **UploadPage** (`pages/upload_page.py`)
  - `navigate()` - Go to upload page
  - `set_feature_flags(flags)` - Configure flags
  - `upload_file(path)` - Upload file
  - `submit()` - Submit form
  - `wait_for_result(expected)` - Wait and verify outcome

## Artifacts

### Test Results

**Location**: `out/results.json`

JSON report generated by pytest-json-report containing:
- Test outcomes (passed/failed/skipped)
- Durations
- Failure messages
- Test metadata

### Summary Report

**Location**: `out/summary.md`

Human-readable Markdown summary with:
- Overall statistics (pass rate, duration)
- Flaky test detection
- Permutation results grouped by outcome
- Recommendations

### Bug Packets

**Location**: `bugs/bug_*.md`

One Markdown file per failure containing:
- Test configuration (role, flags, dataset)
- Failure description
- Links to artifacts (screenshot, trace, log)
- Reproduction steps
- Investigation checklist
- Suggested labels

### Screenshots

**Location**: `out/screenshots/*.png`

Full-page screenshots captured on test failure.

### Playwright Traces

**Location**: `out/traces/*.zip`

Playwright traces for failed tests. View with:

```bash
playwright show-trace out/traces/analyst_fast_preprocess=on_acme_small_ok_rep0_*.zip
```

### Log Files

**Location**: `out/*.log`

Per-test log files with:
- Test metadata
- Error message
- Page content snapshot (capped at 100KB)

## Troubleshooting

### Tests are failing with "BASE_URL not set"

**Solution**: Ensure `.env` file exists and contains `BASE_URL`. Load environment variables:

```bash
export $(grep -v '^#' .env | xargs)
```

### Tests are failing with credential errors

**Solution**: Verify credentials in `.env` match the role names in `catalog.yml`:

```bash
# For role 'analyst', you need:
ANALYST_USER=...
ANALYST_PASS=...
```

### Dataset files not found

**Solution**: Ensure dataset files exist at paths specified in `catalog.yml`. Check:

```bash
ls -la datasets/acme/
ls -la datasets/beta/
```

### Playwright browsers not installed

**Solution**: Install browsers:

```bash
python -m playwright install
```

### Tests are running but not in parallel

**Solution**: Ensure pytest-xdist is installed and use `-n` flag:

```bash
pip install pytest-xdist
pytest -n auto
```

### How to debug a specific test failure

1. Find the test ID from `out/summary.md` or test output
2. Run the specific test with `-k`:
   ```bash
   pytest -k "analyst_fast_preprocess_on_acme_small_ok" -v
   ```
3. Review artifacts in `out/` directory
4. View Playwright trace:
   ```bash
   playwright show-trace out/traces/[matching_file].zip
   ```

### Timeouts occurring frequently

**Solution**: Adjust timeouts in `catalog.yml`:

```yaml
timeouts:
  preprocessing: 180000  # Increase to 3 minutes
  page_load: 60000       # Increase to 1 minute
```

### How to skip flaky tests temporarily

**Solution**: Mark them with pytest's skip marker:

```python
@pytest.mark.skip(reason="Flaky test - under investigation")
def test_upload_workflow(...):
    ...
```

## FAQ

### Q: How do I add a new dataset?

**A:**
1. Place the dataset file in `datasets/` subdirectory
2. Add entry to `catalog.yml`:
   ```yaml
   datasets:
     - id: my_dataset
       path: datasets/my_org/my_file.zip
       classification: synthetic
       expected: success
   ```
3. Run tests

### Q: How do I add a new role?

**A:**
1. Add role to `catalog.yml`:
   ```yaml
   roles:
     - analyst
     - admin
     - viewer  # New role
   ```
2. Add credentials to `.env`:
   ```bash
   VIEWER_USER=svc_viewer
   VIEWER_PASS=password
   ```
3. Run tests

### Q: How do I add a new feature flag?

**A:**
1. Add flag to `catalog.yml`:
   ```yaml
   flags:
     - name: fast_preprocess
       values: [off, on]
     - name: new_feature
       values: [disabled, enabled]
   ```
2. Add selector if visible in UI:
   ```yaml
   selectors:
     feature_flags:
       new_feature: "input[name='new_feature']"
   ```
3. Run tests

### Q: Can I run tests against production?

**A:** **No.** This tool is designed for staging environments only. Running bulk automated tests against production could:
- Impact performance
- Expose sensitive data
- Violate compliance requirements

### Q: How do I use real-sensitive datasets?

**A:**
1. Ensure proper authorization
2. Add dataset to `catalog.yml` with `classification: real-sensitive`
3. Store dataset securely (not in version control)
4. Run with `--include-sensitive` flag:
   ```bash
   pytest --include-sensitive -n auto
   ```

### Q: How many workers should I use?

**A:** Use `-n auto` to automatically detect CPU count. For manual control:
- Small machine (2-4 cores): `-n 2`
- Medium machine (4-8 cores): `-n 4`
- Large machine (8+ cores): `-n 8` or `-n auto`

### Q: Can I run this in CI/CD?

**A:** Yes, but not in v1. The framework is designed to be CI-ready. Future versions will include:
- GitLab CI configuration
- Automated issue creation
- Scheduled runs

### Q: How do I update selectors?

**A:** Edit `catalog.yml`:

```yaml
selectors:
  login:
    username_field: "input#username"  # Updated selector
    password_field: "input#password"
    submit_button: "button.login-submit"
  upload:
    file_input: "input[data-test='file-upload']"
    submit_button: "button[data-test='submit']"
```

### Q: What if my app doesn't have a /login or /upload URL?

**A:** Update the page objects:

```python
# In pages/login_page.py
def navigate(self):
    login_url = f"{self.base_url}/auth/signin"  # Your actual URL
    self.page.goto(login_url)
```

## Security Considerations

- **Credentials**: Never commit `.env` file. Use secure credential management.
- **Datasets**: Real-sensitive datasets must be stored securely and excluded by default.
- **VPN**: Run tests inside VPN when accessing internal staging environments.
- **Audit**: Log all test executions for compliance.
- **Access**: Limit access to test artifacts containing screenshots/traces.

## Performance Tuning

### Optimize Test Runtime

1. **Adjust worker count**: `pytest -n 8`
2. **Reduce repeats**: Set `repeats: 2` in `catalog.yml` (lower flake detection confidence)
3. **Reduce timeouts**: Lower timeout values in `catalog.yml` (may cause false failures)
4. **Selective testing**: Use `-k` to run subset of tests

### Optimize Resource Usage

1. **Headless mode**: Ensure `HEADED_BROWSER=false` (default)
2. **Disable traces on pass**: Already implemented (only saves on failure)
3. **Cleanup old artifacts**: Regularly delete `out/` directory contents

## Contributing

### Adding New Page Objects

1. Create new file in `pages/` directory
2. Follow existing pattern (LoginPage, UploadPage)
3. Accept `page`, `base_url`, `selectors`, `timeouts` in `__init__`
4. Implement methods for page interactions
5. Use configurable selectors from catalog

### Adding New Tools

1. Create new script in `tools/` directory
2. Follow existing pattern (load results from `out/results.json`)
3. Make executable: `chmod +x tools/your_tool.py`
4. Add shebang: `#!/usr/bin/env python3`
5. Document usage in this README

### Improving Selectors

Use resilient selector strategies:
- Prefer `data-test` attributes
- Use `role` and `aria-label` attributes
- Avoid positional selectors (`nth-child`)
- Use text matching for stable elements: `text=Submit`

## Support

For issues or questions:
1. Check this README and `datasets/README.md`
2. Review bug packets in `bugs/` for similar issues
3. Check Playwright traces for detailed debugging
4. Contact QA Engineering team

## License

Internal use only. Not licensed for external distribution.

---

**Version**: 1.0.0
**Status**: Ready for staging use
**Last Updated**: 2024-11-11
**Owner**: QA Engineering Team
