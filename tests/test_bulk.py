"""
Bulk upload workflow tests for SoilOptix Customer Portal.
Implements the complete 6-step workflow: Login → Field → Analysis → Upload → Submit.
"""

from pathlib import Path
from typing import Dict, Any

import pytest
from playwright.sync_api import Page

from pages.login_page import LoginPage
from pages.farm_page import FarmPage
from pages.analysis_page import AnalysisPage


def test_upload_workflow(
    page: Page,
    base_url: str,
    farm_id: int,
    business_id: int,
    credentials: Dict[str, str],
    test_params: Dict[str, Any],
    artifact_paths: Dict[str, Any]
):
    """
    Test the complete SoilOptix upload workflow for a specific permutation.

    Workflow:
    1. Login to Customer Portal
    2. Navigate to Farm page
    3. Create a new field with test naming convention
    4. Create a new analysis
    5. Navigate to Analysis Details → Files tab
    6. Upload Lab file (CSV)
    7. Upload Survey file (ZIP)
    8. [Optional] Upload Boundary file (ZIP)
    9. Navigate to Submit tab
    10. Select and save package
    11. Submit analysis
    12. Verify success/failure popup

    The test is parametrized by pytest_generate_tests in conftest.py to run
    all permutations of: roles × datasets × repeats.
    """
    # Extract test parameters
    catalog = test_params['catalog']
    role = test_params['role']
    dataset = test_params['dataset']
    repeat = test_params['repeat']

    # Get configuration from catalog
    selectors = catalog.get('selectors', {})
    timeouts = catalog.get('timeouts', {})

    # Extract file paths from dataset
    lab_path = Path(__file__).parent.parent / dataset.get('lab')
    survey_path = Path(__file__).parent.parent / dataset.get('survey')
    boundary_path_str = dataset.get('boundary')
    boundary_path = Path(__file__).parent.parent / boundary_path_str if boundary_path_str else None

    # Expected outcome
    expected_outcome = dataset.get('expected', 'success')

    print(f"\n{'='*80}")
    print(f"🧪 Test: {artifact_paths['test_id']}")
    print(f"   Role: {role}")
    print(f"   Dataset: {dataset['id']}")
    print(f"   Expected: {expected_outcome}")
    print(f"   Repeat: {repeat}")
    print(f"{'='*80}\n")

    # ========================================================================
    # Step 1: Login
    # ========================================================================
    print(f"🔐 Step 1: Logging in as {role}")
    login_page = LoginPage(page, base_url, selectors, timeouts)
    login_page.navigate()
    login_page.login(credentials['username'], credentials['password'])

    assert login_page.is_logged_in(), f"Login failed for role: {role}"
    print(f"✅ Successfully logged in\n")

    # ========================================================================
    # Step 2: Navigate to Business/Farm
    # ========================================================================
    if business_id:
        print(f"🏢 Step 2: Navigating to Business {business_id}")
    else:
        print(f"🚜 Step 2: Navigating to Farm {farm_id}")

    farm_page = FarmPage(page, base_url, farm_id, selectors, timeouts, business_id)
    farm_page.navigate()
    print(f"✅ Navigated to business/farm page\n")

    # ========================================================================
    # Step 3: Create Field
    # ========================================================================
    print(f"📍 Step 3: Creating test field")
    field_name = FarmPage.generate_field_name(dataset_id=dataset['id'], business_name="SoilOptix")
    farm_page.create_field(field_name)
    print(f"✅ Field created: {field_name}\n")

    # ========================================================================
    # Step 4: Create Analysis
    # ========================================================================
    print(f"📊 Step 4: Creating analysis")
    analysis_id = farm_page.create_analysis()
    print(f"✅ Analysis created: ID = {analysis_id}\n")

    # ========================================================================
    # Step 5: Upload Files
    # ========================================================================
    analysis_page = AnalysisPage(page, selectors, timeouts)

    print(f"📁 Step 5: Navigating to Files tab")
    analysis_page.navigate_to_files_tab()
    print(f"✅ Files tab loaded\n")

    # Upload Lab file
    print(f"🧪 Step 5a: Uploading Lab file: {lab_path.name}")
    if not lab_path.exists():
        pytest.fail(f"Lab file not found: {lab_path}")

    lab_success, lab_message = analysis_page.upload_lab_file(lab_path)
    assert lab_success, f"Lab file upload failed: {lab_message}"
    print(f"✅ {lab_message}\n")

    # Upload Survey file
    print(f"📡 Step 5b: Uploading Survey file: {survey_path.name}")
    if not survey_path.exists():
        pytest.fail(f"Survey file not found: {survey_path}")

    survey_success, survey_message = analysis_page.upload_survey_file(survey_path)
    assert survey_success, f"Survey file upload failed: {survey_message}"
    print(f"✅ {survey_message}\n")

    # Upload Boundary file (optional)
    if boundary_path and boundary_path.exists():
        print(f"🗺️  Step 5c: Uploading Boundary file: {boundary_path.name}")
        boundary_success, boundary_message = analysis_page.upload_boundary_file(boundary_path)
        if boundary_success:
            print(f"✅ {boundary_message}\n")
        else:
            print(f"⚠️  Boundary upload failed (optional): {boundary_message}\n")
    else:
        print(f"⏭️  Step 5c: Skipping boundary file (not provided)\n")

    # ========================================================================
    # Step 6: Submit Analysis
    # ========================================================================
    print(f"📤 Step 6: Navigating to Submit tab")
    analysis_page.navigate_to_submit_tab()
    print(f"✅ Submit tab loaded\n")

    print(f"📦 Step 6a: Selecting and saving package")
    analysis_page.select_and_save_package()
    print(f"✅ Package saved\n")

    print(f"🚀 Step 6b: Submitting analysis (this may take 30s-5min)")
    submit_success, submit_message = analysis_page.submit_analysis()

    # ========================================================================
    # Step 7: Verify Result
    # ========================================================================
    print(f"\n{'='*80}")
    if expected_outcome == 'success':
        assert submit_success, f"Expected success but got failure: {submit_message}"
        print(f"✅ TEST PASSED: {submit_message}")
    elif expected_outcome == 'input_error':
        assert not submit_success, f"Expected failure but got success: {submit_message}"
        print(f"✅ TEST PASSED: Error detected as expected: {submit_message}")
    else:
        pytest.fail(f"Unknown expected outcome: {expected_outcome}")

    print(f"{'='*80}\n")


def test_upload_workflow_smoke(page: Page, base_url: str):
    """
    Smoke test to verify basic connectivity to Customer Portal.
    This test doesn't use parametrization and just checks if the app is reachable.

    Run with: pytest -k smoke
    """
    try:
        print(f"\n🔍 Smoke Test: Checking connectivity to {base_url}")
        page.goto(base_url, timeout=30000)

        # Check that page loaded
        assert page.title(), "Page has no title"

        print(f"✅ Application is reachable at {base_url}")
        print(f"   Page title: {page.title()}")
        print(f"   Current URL: {page.url}\n")

    except Exception as e:
        pytest.fail(f"Cannot reach application at {base_url}: {str(e)}")
