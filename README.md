# SoilOptix Bulk Upload Workflow Test Runner

Automated test framework for the SoilOptix Customer Portal upload workflow.

## What This Does

Automates the complete 6-step workflow:
1. **Login** to Customer Portal
2. **Navigate** to Farm 20101
3. **Create Field** (with "AutoTest" prefix)
4. **Create Analysis**
5. **Upload Files** (Lab CSV + Survey ZIP)
6. **Submit Analysis** with package selection
7. **Verify** success popup

## Prerequisites

✅ **Must Have:**
- Python 3.10 or higher
- **Company VPN access** (staging portal is internal only)
- 5-10 minutes for first-time setup

✅ **Already Included:**
- Test credentials (in `.env.example`)
- Sample datasets (Lab CSV, Survey ZIP)
- All selectors configured

## Quick Start (First Time)

```bash
# 1. Navigate to the bulk-runner directory
cd bulk-runner

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install Playwright browsers
python -m playwright install chromium

# 5. Copy environment template (credentials already included!)
cp .env.example .env

# 6. Run tests
python -m pytest -n auto

# 7. Generate reports
python tools/summarize.py
python tools/mk_bug_packets.py

# 8. View results
cat out/summary.md
```

## That's It!

The framework will:
- Connect to `https://customerportalstaging.local.soiloptix.com`
- Login with test credentials
- Create a field named `AutoTest_20241111_HHMMSS_SoilOptix_sample_valid`
- Upload lab and survey files
- Submit the analysis
- Report success or failure

**Expected Runtime:** 1-2 minutes per test (2 repeats = ~4 minutes total)

## View Results

**Summary Report:**
```bash
cat out/summary.md
```
Shows pass rates and any flaky tests.

**Bug Packets** (if failures occur):
```bash
ls bugs/
cat bugs/bug_*.md
```
Ready-to-paste bug reports with screenshots and traces.

**Artifacts** (on failure only):
- Screenshots: `out/screenshots/*.png`
- Playwright traces: `out/traces/*.zip` (view with `playwright show-trace <file>`)
- Logs: `out/*.log`

## Subsequent Runs

After first-time setup, just:

```bash
cd bulk-runner
python -m pytest -n auto     # Run tests
python tools/summarize.py    # Generate summary
```

## Configuration Files

| File | Purpose | Need to Edit? |
|------|---------|---------------|
| `.env` | Credentials & URLs | ❌ Already configured |
| `catalog.yml` | Selectors & timeouts | ❌ Already configured |
| `datasets/soiloptix/` | Test data files | ❌ Already included |

You **don't need to edit anything** for v1!

## Troubleshooting

### "Cannot reach application"
**Solution:** Ensure you're connected to company VPN

### "Playwright not found"
**Solution:** Run `python -m playwright install chromium`

### "BASE_URL not set"
**Solution:** Ensure you ran `cp .env.example .env`

### Tests fail with selector errors
**Solution:** Staging UI may have changed. Check `catalog.yml` selectors against current staging.

### Want to see the browser?
```bash
python -m pytest --headed --slow-mo 500
```

## What Gets Created on Staging

Each test run creates:
- 1 new field: `AutoTest_[timestamp]_SoilOptix_sample_valid`
- 1 new analysis within that field
- Files uploaded and submitted

**Note:** Test data is NOT automatically cleaned up. You may want to periodically delete "AutoTest_*" fields from staging.

## Advanced Usage

### Run smoke test only
```bash
python -m pytest -k smoke
```

### Run with specific worker count
```bash
python -m pytest -n 4  # Use 4 parallel workers
```

### Run without parallelism (for debugging)
```bash
python -m pytest -v  # Verbose, single-threaded
```

### View detailed logs
```bash
cat out/pytest.log
```

## File Structure

```
bulk-runner/
├── .env.example          # Credentials template (copy to .env)
├── catalog.yml           # Selectors and configuration
├── pytest.ini            # Pytest settings
├── conftest.py           # Test fixtures
├── requirements.txt      # Python dependencies
│
├── pages/                # Page Objects (POM pattern)
│   ├── login_page.py
│   ├── farm_page.py
│   └── analysis_page.py
│
├── tests/
│   └── test_bulk.py      # Main test implementation
│
├── tools/                # Post-processing scripts
│   ├── summarize.py      # Generate summary.md
│   └── mk_bug_packets.py # Generate bug reports
│
├── datasets/soiloptix/   # Test data
│   ├── lab/sample_lab_valid.csv
│   └── survey/sample_survey_valid.zip
│
├── docs/                 # Documentation
│   ├── PRD_UPDATED.md    # Technical specification
│   └── WORKFLOW.md       # Step-by-step guide
│
└── out/                  # Generated artifacts (gitignored)
    ├── summary.md
    ├── results.json
    ├── screenshots/
    └── traces/
```

## Documentation

- **Quick Start:** This file
- **Detailed Workflow:** [`docs/WORKFLOW.md`](docs/WORKFLOW.md) - Step-by-step with all selectors
- **Technical Spec:** [`docs/PRD_UPDATED.md`](docs/PRD_UPDATED.md) - Complete PRD

## Version

**v1.0** - Basic happy path testing
- Single role (customer)
- Single farm (20101)
- Lab + Survey files only
- 2 repeats for flake detection

**Coming in Phase 2:**
- Multiple businesses/farms
- XLSX lab file support
- Boundary file testing
- Analyst portal verification
- Invalid file scenarios
- Automated cleanup

## Support

Issues? Check:
1. Are you on VPN?
2. Did you install Playwright browsers? (`python -m playwright install chromium`)
3. Does `.env` file exist? (copy from `.env.example`)
4. Review `docs/WORKFLOW.md` for detailed troubleshooting

## Testing Status

✅ **Production Ready!** All tests passing on Windows
✅ Complete end-to-end workflow validated on staging
✅ Login, field creation, analysis creation working
✅ File uploads (Lab CSV + Survey ZIP) successful
✅ Analysis submission verified
✅ Report generation working with full emoji support
✅ Playwright trace debugging available
⏱️ **Average runtime:** ~27 seconds per test

**Recent Fixes (2025-11-11):**
- Fixed login timeout issues (networkidle → URL-based waits)
- Resolved toast notification blocking with JavaScript removal
- Added retry mechanism for field creation 404 race condition
- Fixed Windows UTF-8 encoding for report generation
- Updated all selectors to match current staging UI

---

**Last Updated:** 2025-11-11
**Maintained By:** QA Engineering
**Staging Portal:** https://customerportalstaging.local.soiloptix.com
