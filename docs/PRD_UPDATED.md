# PRD / RFC: Bulk Upload Workflow Test Runner - UPDATED

**Status**: Implementation
**Owner**: QA Eng
**Target Environment**: SoilOptix Staging (inside VPN)
**Tech Stack**: Python 3.10+, Playwright (Python), pytest, pytest-xdist, pytest-json-report, pyyaml, python-dotenv
**Last Updated**: 2024-11-11

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Original | Initial PRD with simple upload workflow |
| 2.0 | 2024-11-11 | Updated with actual SoilOptix workflow (6-step process) |

---

## 1) Purpose & Outcomes

Build a bulk test runner that executes the complete **SoilOptix agricultural analysis upload workflow** across multiple datasets, creating fields and analyses programmatically, uploading lab/survey/boundary files, and validating submission success.

**Key Changes from Original PRD:**
- Workflow is significantly more complex than initially scoped
- Two portals: Customer Portal (upload) and Analyst Portal (verification - Phase 2)
- Multi-step process: Field creation → Analysis creation → File uploads → Package selection → Submission
- Three file types: Lab (CSV/XLSX), Survey (ZIP with .mdl files), Boundary (optional, ZIP with shapefiles)

---

## 2) Actual Workflow Discovered

### Original PRD Assumption:
```
Login → Navigate to /upload → Upload file → Submit → Wait for result
```

### Actual SoilOptix Workflow:
```
1. Login to Customer Portal
2. Navigate to Farm page (specific Farm ID)
3. Create new Field with test naming convention
4. Create new Analysis within Field
5. Click Analysis Details link from success popup
6. Navigate to Files tab
7. Upload Lab file (CSV) - wait for success
8. Upload Survey files (ZIP with .mdl, .csv, .log) - wait for success
9. [Optional] Upload Boundary files (ZIP with shapefiles) - wait for success
10. Navigate to Submit tab
11. Select package from available options
12. Save selected package
13. Submit analysis
14. Wait for success/failure popup (30s - 5min)
```

---

## 3) System Architecture

### Two Portals

**Customer Portal (v1 scope):**
- URL: `https://customerportalstaging.local.soiloptix.com`
- Purpose: Upload and submit agricultural analyses
- Users: Customers, test automation
- Farm ID: `/Farms/20101` (test farm)

**Analyst Portal (Phase 2):**
- URL: `https://analystportalstaging.local.soiloptix.com`
- Purpose: Verify uploads, process analyses, download results
- Users: Analysts
- Out of scope for v1

### File Types

| Type | Format | Required | Description |
|------|--------|----------|-------------|
| Lab | CSV or XLSX | Yes | Soil analysis lab results (pH, OM, nutrients, etc.) |
| Survey | ZIP (contains .mdl, .csv, .log) | Yes | Field survey data from SODL device |
| Boundary | ZIP (shapefiles: .shp, .shx, .dbf, .prj) | No | Field boundary polygon |

**Note**: Only file extensions are accepted - cannot upload individual non-standard files. Survey must be zipped due to multiple file requirement.

---

## 4) Success Criteria (v1 DoD)

### Updated Acceptance Tests

1. **Full workflow test (Lab + Survey)**:
   - Creates field with test naming convention
   - Creates analysis
   - Uploads Lab CSV successfully
   - Uploads Survey ZIP successfully
   - Selects and saves package
   - Submits analysis
   - Receives success popup: "Analysis submitted successfully"
   - Generates summary report showing 100% pass rate

2. **Failure detection**:
   - If any step fails, captures failure details
   - Saves screenshot, Playwright trace, and log
   - Generates bug packet with full context
   - Reports popup message (success or failure section)

3. **Flake detection**:
   - Runs test 2 times (repeats)
   - If results differ across repeats, marks as FLAKY in summary

4. **Artifact generation**:
   - `out/summary.md` with pass rates
   - `bugs/*.md` with failure details
   - Screenshots and traces for failures only

---

## 5) Page Selectors (Chrome Inspect - CSS Selectors)

### Login Page
```yaml
login:
  username_field: "div.login__input--container:nth-child(1) > input:nth-child(3)"
  password_field: "#password"
  submit_button: ".login__button--primary"
```

### Farm Page (Field Management)
```yaml
farm:
  add_field_button: ".button__add-small"
  field_name_input: ".create-popup--input-form"
  create_field_button: ".create-popup--container > div:nth-child(1) > div:nth-child(4) > button:nth-child(2)"
```

### Analysis Creation
```yaml
analysis:
  create_analysis_button: ".button__primary-create"
  create_confirm_button: "div.create-popup--button-group:nth-child(3) > button:nth-child(2)"
  analysis_details_link: ".mb-5"  # Appears in success popup after creation
```

### Analysis Details - Files Tab
```yaml
files:
  files_tab: "button.tab-pill:nth-child(2)"

  # Lab file upload
  upload_lab_button: "div.file-folder-section:nth-child(2) > div:nth-child(1) > button:nth-child(2)"
  lab_upload_box: "div.file-folder-section:nth-child(4) > div:nth-child(3) > div:nth-child(1) > div:nth-child(4) > div:nth-child(3) > label:nth-child(1)"
  lab_upload_confirm: "div.file-folder-section:nth-child(4) > div:nth-child(3) > div:nth-child(1) > div:nth-child(5) > div:nth-child(1) > button:nth-child(2)"

  # Survey file upload
  upload_survey_button: "div.file-folder-section:nth-child(3) > div:nth-child(1) > button:nth-child(2)"
  survey_upload_box: "div.file-folder-section:nth-child(4) > div:nth-child(3) > div:nth-child(1) > div:nth-child(4) > div:nth-child(3) > label:nth-child(1)"
  survey_upload_confirm: "div.file-folder-section:nth-child(4) > div:nth-child(3) > div:nth-child(1) > div:nth-child(5) > div:nth-child(1) > button:nth-child(2)"

  # Boundary file upload
  upload_boundary_button: "div.file-folder-section:nth-child(4) > div:nth-child(1) > button:nth-child(2)"
  boundary_upload_box: "div.file-folder-section:nth-child(4) > div:nth-child(3) > div:nth-child(1) > div:nth-child(4) > div:nth-child(3) > label:nth-child(1)"
  boundary_upload_confirm: "div.file-folder-section:nth-child(4) > div:nth-child(3) > div:nth-child(1) > div:nth-child(5) > div:nth-child(1) > button:nth-child(2)"

  # Upload status
  upload_success: ".success-section"
  upload_error: ".upload-error"
  close_popup: "button.button__primary-dark:nth-child(1)"
```

### Submit Tab
```yaml
submit:
  submit_tab: "button.tab-pill:nth-child(4)"
  select_package_button: ".package-select-button"
  save_package_button: ".save-package-button"
  submit_analysis_button: ".submit-analysis-button"

  # Result popups
  success_popup: ".success-section"  # "Analysis submitted successfully"
  failure_popup: ".failure-section"  # "Action Failed! You must select and save..."
```

---

## 6) Test Configuration (catalog.yml)

### v1 Test Matrix

```yaml
roles:
  - customer  # Single role for v1

farm_id: 20101  # Test farm

datasets:
  - id: soiloptix_sample_valid
    lab: datasets/soiloptix/lab/sample_lab_valid.csv
    survey: datasets/soiloptix/survey/sample_survey_valid.zip
    boundary: null  # Optional, not included in v1
    expected: success

repeats: 2  # For flake detection

# Phase 2: Add more scenarios
# - Different businesses
# - XLSX lab files
# - With boundary files
# - Invalid file scenarios
```

### Timeouts

```yaml
timeouts:
  login: 10000  # 10s
  page_load: 30000  # 30s
  field_creation: 15000  # 15s
  analysis_creation: 15000  # 15s
  file_upload: 120000  # 2 minutes (for large files)
  submit_analysis: 300000  # 5 minutes (entire workflow timeout)
```

---

## 7) Field & Analysis Naming Convention

To avoid confusion with production data and enable easy cleanup:

**Fields:**
```
Format: AutoTest_{timestamp}_{business_name}
Example: AutoTest_20241111_143022_SoilOptix
```

**Analyses:**
- Auto-generated by system after creation
- ID extracted from Analysis Details URL: `/Analyses/{id}`

---

## 8) Error Handling

### Upload Errors

**Indicators:**
- `.upload-error` appears during file upload
- For large files: Progress circle appears → then error
- For small files: Error appears instantly

**Action:**
- Capture error text
- Save screenshot and trace
- Generate bug packet
- Mark test as failed

### Submit Errors

**Common error:**
```
Popup: .failure-section
Text: "Action Failed! You must select and save at least one package before submitting."
```

**Action:**
- Capture popup text
- Report which step failed
- Save artifacts
- Generate bug packet

### Success Confirmation

```
Popup: .success-section
Text: "Analysis submitted successfully."
```

---

## 9) Phase Roadmap

### Phase 1 (v1 - Current)
- ✅ Single role (customer)
- ✅ Single farm (20101)
- ✅ Lab CSV + Survey ZIP
- ✅ No boundary files
- ✅ Simple happy path
- ✅ 2 repeats for flake detection
- ✅ Local artifacts and bug packets

### Phase 2 (Future)
- Multiple businesses/farms
- XLSX lab file testing
- Boundary file inclusion
- Different survey configurations
- Analyst portal verification
- Invalid file scenario testing
- Automated cleanup of test data

### Phase 3 (Future)
- CI/CD integration
- Multiple roles with different permissions
- Automated GitLab issue creation
- Performance benchmarking
- Cross-browser testing

---

## 10) Data & Privacy

**Dataset Classifications:**

| Classification | Description | Usage in v1 |
|----------------|-------------|-------------|
| Synthetic | Completely artificial test data | ✅ Primary |
| Sanitized | Real data with PII removed | Phase 2 |
| Real-Sensitive | Production data | ❌ Not used |

**Security:**
- All tests run inside company VPN
- Credentials stored in `.env` (gitignored)
- Artifacts saved locally only
- No external data transfer
- Test data clearly marked with "AutoTest" prefix

---

## 11) Technical Notes

### Upload Behavior

**File Upload Flow:**
1. Click "Upload {type}" button → Popup opens
2. Click upload box → File dialog OR drag-and-drop
3. Selected file appears at bottom of popup
4. Click "Upload" button in popup
5. **Small files**: Upload instant, file appears below
6. **Large files**: Progress circle → Success message
7. Wait for `.success-section` to appear
8. Click close button to dismiss popup
9. Repeat for next file type

**Package Selection:**
- Packages are business-specific presets based on lab columns
- No visual confirmation after save
- Must select then save before submit
- If not saved: Error popup appears on submit

### Analysis ID Extraction

After creating analysis:
1. Success popup appears with "Analysis Details" link
2. Click link to navigate
3. URL format: `https://customerportalstaging.local.soiloptix.com/Analyses/{id}`
4. Alternative: Extract `href` from link and construct URL manually

---

## 12) File Structure (Updated)

```
bulk-runner/
├── catalog.yml              # Updated with real selectors
├── conftest.py              # Matrix generation, fixtures
├── pytest.ini              # Pytest config
├── requirements.txt         # Dependencies
├── .env.example            # Credential template
├── pages/
│   ├── login_page.py       # Updated with real selectors
│   ├── farm_page.py        # NEW - Field creation
│   ├── analysis_page.py    # NEW - Analysis creation, file uploads, submit
│   └── upload_page.py      # DEPRECATED - not used in actual workflow
├── tests/
│   └── test_bulk.py        # Updated for 6-step workflow
├── tools/
│   ├── summarize.py        # Generate summary.md
│   └── mk_bug_packets.py   # Generate bug packets
├── datasets/
│   └── soiloptix/
│       ├── lab/
│       │   └── sample_lab_valid.csv
│       ├── survey/
│       │   └── sample_survey_valid.zip
│       └── boundary/
│           └── sample_boundary_valid.zip
├── docs/
│   ├── PRD_UPDATED.md      # This file
│   └── WORKFLOW.md         # Step-by-step workflow documentation
└── out/                    # Test results (gitignored)
```

---

## 13) Dependencies & Constraints

**Environment:**
- Must be inside company VPN to access staging portals
- Chrome browser with Playwright
- Farm 20101 must exist and be accessible
- Test credentials must have field/analysis creation permissions

**Technical Constraints:**
- File extensions enforced - cannot upload arbitrary file types
- Survey files must be zipped (multiple files)
- Boundary files must be zipped (shapefile set)
- Upload timeout: 2 minutes per file
- Submit timeout: 5 minutes total workflow
- No runtime LLM calls (fully deterministic)

**Known Limitations:**
- No cleanup of test data in v1 (manual cleanup required)
- Single farm testing only
- No analyst portal verification
- No invalid file testing
- CSV lab files only (XLSX in Phase 2)

---

## 14) Success Metrics

**v1 is successful if:**
1. ✅ Test runner completes full workflow end-to-end
2. ✅ Creates fields with proper naming convention
3. ✅ Uploads files successfully
4. ✅ Submits analysis and receives success popup
5. ✅ Generates summary report with pass rates
6. ✅ Generates bug packets for any failures
7. ✅ Runs in parallel with pytest-xdist
8. ✅ Detects flakes across repeats
9. ✅ Captures rich debugging artifacts
10. ✅ Documentation is comprehensive and accurate

---

## Appendix A: Original PRD vs Actual Implementation

| Aspect | Original PRD | Actual Implementation |
|--------|--------------|----------------------|
| Workflow Steps | 2 (login, upload) | 6+ (field, analysis, 3 uploads, package, submit) |
| Portals | 1 (generic staging) | 2 (customer + analyst) |
| File Types | 1 (generic dataset) | 3 (lab, survey, boundary) |
| Upload Method | Single file input | Multiple popups with separate upload flows |
| Success Indicator | Simple text/banner | Popup with specific selectors |
| Complexity | Simple | Medium-High |
| Test Scope | Matrix of datasets | Matrix of file combinations |

---

**End of Updated PRD**
