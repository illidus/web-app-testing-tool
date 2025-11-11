# SoilOptix Upload Workflow - Step-by-Step Guide

This document provides a detailed walkthrough of the actual SoilOptix Customer Portal upload workflow that the test framework automates.

## Overview

The complete workflow consists of **6 major steps** with multiple sub-steps:

1. **Login** to Customer Portal
2. **Navigate** to specific Farm
3. **Create Field** with test naming
4. **Create Analysis** within field
5. **Upload Files** (Lab + Survey + optional Boundary)
6. **Submit Analysis** with package selection

Total time: **30 seconds to 5 minutes** depending on file sizes and processing

---

## Detailed Step-by-Step Workflow

### Prerequisites

- Access to company VPN
- Valid customer portal credentials
- Test datasets prepared (Lab CSV, Survey ZIP)
- Farm ID (e.g., 20101 for testing)

### Step 1: Login to Customer Portal

**URL**: `https://customerportalstaging.local.soiloptix.com`

**Actions:**
1. Navigate to base URL
2. Fill email field: `div.login__input--container:nth-child(1) > input:nth-child(3)`
3. Fill password field: `#password`
4. Click login button: `.login__button--primary`
5. Wait for navigation to complete

**Success Indicator**: URL changes from login page, user is redirected

**Timeout**: 10 seconds

---

### Step 2: Navigate to Farm

**URL**: `https://customerportalstaging.local.soiloptix.com/Farms/20101`

**Actions:**
1. Navigate directly to farm page using farm ID
2. Wait for page to load

**Success Indicator**: Farm page displays with fields and analyses

**Timeout**: 30 seconds

---

### Step 3: Create Field

**Purpose**: Create a test field to contain the analysis

**Actions:**
1. Click "Add new" field button: `.button__add-small`
2. Wait for popup to appear
3. Enter field name in input: `.create-popup--input-form`
   - **Naming convention**: `AutoTest_YYYYMMDD_HHMMSS_BusinessName_DatasetID`
   - Example: `AutoTest_20241111_143022_SoilOptix_sample_valid`
4. Click "Create" button: `.create-popup--container > div:nth-child(1) > div:nth-child(4) > button:nth-child(2)`
5. Wait for field to be created

**Success Indicator**: Field appears in farm's field list

**Timeout**: 15 seconds

---

### Step 4: Create Analysis

**Purpose**: Create an analysis within the field to hold uploaded files

**Actions:**
1. Click "Create analysis" button: `.button__primary-create`
2. Wait for popup
3. Click confirm button: `div.create-popup--button-group:nth-child(3) > button:nth-child(2)`
4. Wait for success popup with "Analysis Details" link
5. Click "Analysis Details" link: `.mb-5`
6. Navigate to analysis details page
7. Extract analysis ID from URL
   - URL format: `/Analyses/{id}`
   - Example: `/Analyses/5000419`

**Success Indicator**: Analysis Details page loads, URL contains analysis ID

**Timeout**: 15 seconds

---

### Step 5: Upload Files

**Purpose**: Upload lab results, survey data, and optionally boundary files

#### Step 5.1: Navigate to Files Tab

**Actions:**
1. Click "Files" tab: `button.tab-pill:nth-child(2)`
2. Wait for tab content to load

**Timeout**: 5 seconds

#### Step 5.2: Upload Lab File (CSV)

**File Format**: CSV with columns: SampleID, pH, OM, P, K, Mg, Ca, CEC, Mn, Zn, Fe, Cu, Sand, Silt, Clay

**Actions:**
1. Click "Upload" button for Lab section: `div.file-folder-section:nth-child(2) > div:nth-child(1) > button:nth-child(2)`
2. Popup opens
3. Click upload box (label): `div.file-folder-section:nth-child(4) > div:nth-child(3) > div:nth-child(1) > div:nth-child(4) > div:nth-child(3) > label:nth-child(1)`
4. File input activates via Playwright `set_input_files()`
5. Click "Upload" confirm button: `div.file-folder-section:nth-child(4) > div:nth-child(3) > div:nth-child(1) > div:nth-child(5) > div:nth-child(1) > button:nth-child(2)`
6. **Small files**: Upload completes instantly
7. **Large files**: Progress bar appears, then success message
8. Wait for success message: `.success-section`
9. Click close button: `button.button__primary-dark:nth-child(1)`

**Success Indicator**: `.success-section` appears, file listed below upload box

**Timeout**: 2 minutes (for large files)

#### Step 5.3: Upload Survey File (ZIP)

**File Format**: ZIP containing:
- `.mdl` file (model data)
- `.csv` file (activities log)
- `.log` file (system log)

**Actions:**
1. Click "Upload" button for Survey section: `div.file-folder-section:nth-child(3) > div:nth-child(1) > button:nth-child(2)`
2. Follow same upload flow as Lab file
3. Use survey-specific selectors
4. Wait for success: `.success-section`
5. Close popup

**Success Indicator**: Survey file uploaded successfully

**Timeout**: 2 minutes

#### Step 5.4: Upload Boundary File (ZIP) - OPTIONAL

**File Format**: ZIP containing shapefile set:
- `.shp` (geometry)
- `.shx` (index)
- `.dbf` (attributes)
- `.prj` (projection)

**Actions:**
1. Click "Upload" button for Boundary section: `div.file-folder-section:nth-child(4) > div:nth-child(1) > button:nth-child(2)`
2. Follow same upload flow
3. Wait for success or skip if not provided

**Success Indicator**: Boundary file uploaded (or skipped)

**Timeout**: 2 minutes

---

### Step 6: Submit Analysis

**Purpose**: Package and submit the analysis for processing

#### Step 6.1: Navigate to Submit Tab

**Actions:**
1. Click "Submit" tab: `button.tab-pill:nth-child(4)`
2. Wait for tab content to load

**Timeout**: 5 seconds

#### Step 6.2: Select and Save Package

**What is a Package?**
- Business-specific preset configuration
- Depends on lab file columns
- Usually one package available by default

**Actions:**
1. Click "Select package" button: `.package-select-button`
2. Package is selected (no visible UI change)
3. Click "Save package" button: `.save-package-button`
4. Package is saved (no visible confirmation)

**Important**: If package is not saved before submit, error popup will appear:
- "Action Failed! You must select and save at least one package before submitting."

**Timeout**: 5 seconds each

#### Step 6.3: Submit Analysis

**Actions:**
1. Click "Submit analysis" button: `.submit-analysis-button`
2. Wait for processing (30 seconds to 5 minutes)
3. Success or failure popup appears

**Success Popup:**
- Selector: `.success-section`
- Text: "Analysis submitted successfully"

**Failure Popup:**
- Selector: `.failure-section`
- Text: "Action Failed! [error description]"

**Timeout**: 5 minutes (300 seconds)

---

## Timing Summary

| Step | Typical Time | Max Timeout |
|------|--------------|-------------|
| Login | 2-5s | 10s |
| Navigate to Farm | 1-2s | 30s |
| Create Field | 2-3s | 15s |
| Create Analysis | 3-5s | 15s |
| Navigate to Files | 1s | 5s |
| Upload Lab | 1-10s | 2min |
| Upload Survey | 5-30s | 2min |
| Upload Boundary | 5-30s | 2min |
| Navigate to Submit | 1s | 5s |
| Select/Save Package | 1s | 5s each |
| Submit Analysis | 30s-5min | 5min |
| **TOTAL** | **1-2 minutes** | **~13 minutes** |

---

## Error Scenarios

### Login Fails
**Symptom**: Stays on login page, error message appears
**Action**: Check credentials in `.env` file

### Field Creation Fails
**Symptom**: Popup doesn't close, error appears
**Action**: Check field name format, ensure farm is accessible

### File Upload Fails
**Symptom**: `.upload-error` appears instead of `.success-section`
**Possible Causes**:
- Wrong file format
- File too large
- Corrupt file
- Network timeout

### Submit Fails - Missing Package
**Symptom**: Failure popup "You must select and save..."
**Action**: Ensure Step 6.2 completed successfully

### Submit Fails - Other Errors
**Symptom**: Failure popup with specific error message
**Action**: Review error text, check file validity

---

## Test Naming Convention

**Fields**: `AutoTest_{timestamp}_{business}_{dataset}`
**Example**: `AutoTest_20241111_143022_SoilOptix_sample_valid`

**Purpose**:
- Identify automated test data
- Enable easy cleanup
- Track which dataset was used
- Timestamp for uniqueness

---

## Cleanup

**v1**: Test fields and analyses are **NOT** automatically deleted
- Manual cleanup required periodically
- Filter by "AutoTest_" prefix to identify test data

**Future**: Phase 2 will include automated cleanup capability

---

## Troubleshooting

### "Cannot find element" errors
**Solution**: Check that selectors in `catalog.yml` match current staging environment

### Timeouts
**Solution**: Increase timeout values in `catalog.yml` under `timeouts:` section

### File not found
**Solution**: Ensure datasets exist in `datasets/soiloptix/` directory

### VPN issues
**Solution**: Confirm VPN connection, try accessing portal manually first

### Windows Encoding Issues (Report Generation)
**Symptom**: Tools crash with "charmap codec can't encode character" error
**Solution**: UTF-8 encoding has been added to all report tools. If you still see this:
📊 Analyzing test results...
✅ Summary generated: C:\dev\web-app-testing-toolulk-runner\out\summary.md

📈 Results:
   Total: 1
   Passed: 1
   Failed: 0
   Skipped: 0

### Test Passes But Creates 404 on Field Page
**Symptom**: Field creates successfully but page shows 404
**Solution**: Backend race condition - retry mechanism added. If persists, increase timeout in catalog.yml

---

## References

- Updated PRD: `docs/PRD_UPDATED.md`
- Selector Configuration: `catalog.yml`
- Page Objects: `pages/`
- Test Implementation: `tests/test_bulk.py`

---

**Last Updated**: 2025-11-11
**Workflow Version**: 1.0 (v1 - Lab + Survey only)
