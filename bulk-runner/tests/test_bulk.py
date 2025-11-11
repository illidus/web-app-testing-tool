"""
Bulk upload workflow tests.
Parametrized test that runs all permutations defined in catalog.yml.
"""

from pathlib import Path
from typing import Dict, Any

import pytest
from playwright.sync_api import Page

from pages.login_page import LoginPage
from pages.upload_page import UploadPage


def test_upload_workflow(page: Page, base_url: str, credentials: Dict[str, str],
                        test_params: Dict[str, Any], artifact_paths: Dict[str, Any]):
    """
    Test the complete upload workflow for a specific permutation.

    This test:
    1. Logs in with role-specific credentials
    2. Navigates to the upload page
    3. Sets feature flags (if applicable)
    4. Uploads the dataset file
    5. Submits for preprocessing
    6. Waits for and verifies the expected outcome

    The test is parametrized by pytest_generate_tests in conftest.py to run
    all permutations of: roles × flags × datasets × repeats.
    """
    # Extract test parameters
    catalog = test_params['catalog']
    role = test_params['role']
    flags = test_params['flags']
    dataset = test_params['dataset']
    repeat = test_params['repeat']

    # Get configuration from catalog
    selectors = catalog.get('selectors', {})
    timeouts = catalog.get('timeouts', {})

    # Resolve dataset path (relative to project root)
    dataset_path = Path(__file__).parent.parent / dataset['path']

    # Expected outcome
    expected_outcome = dataset.get('expected', 'success')

    # Apply pytest marker based on dataset classification
    classification = dataset.get('classification', 'synthetic')
    if classification == 'synthetic':
        pytest.mark.synthetic
    elif classification == 'sanitized':
        pytest.mark.sanitized
    elif classification == 'real-sensitive':
        pytest.mark.sensitive

    # Step 1: Login
    print(f"\n🔐 Logging in as role: {role}")
    login_page = LoginPage(page, base_url, selectors, timeouts)
    login_page.navigate()
    login_page.login(credentials['username'], credentials['password'])

    # Verify login succeeded
    assert login_page.is_logged_in(), f"Login failed for role: {role}"
    print(f"✅ Successfully logged in as {role}")

    # Step 2: Navigate to upload page
    print(f"📁 Navigating to upload page")
    upload_page = UploadPage(page, base_url, selectors, timeouts)
    upload_page.navigate()

    # Step 3: Set feature flags (if any)
    if flags:
        print(f"🚩 Setting feature flags: {flags}")
        upload_page.set_feature_flags(flags)

    # Step 4: Upload file
    print(f"📤 Uploading dataset: {dataset['id']} from {dataset_path}")

    # Check if dataset file exists
    if not dataset_path.exists():
        pytest.skip(f"Dataset file not found: {dataset_path}. Skipping test.")

    upload_page.upload_file(dataset_path)
    print(f"✅ File uploaded")

    # Step 5: Submit for preprocessing
    print(f"▶️  Submitting for preprocessing")
    upload_page.submit()

    # Step 6: Wait for result
    print(f"⏳ Waiting for result (expecting: {expected_outcome})")
    success, message = upload_page.wait_for_result(expected_outcome)

    # Assert the expected outcome
    assert success, f"Test failed: {message}\n" \
                   f"Role: {role}\n" \
                   f"Flags: {flags}\n" \
                   f"Dataset: {dataset['id']}\n" \
                   f"Expected: {expected_outcome}\n" \
                   f"Repeat: {repeat}"

    print(f"✅ Test passed: {message}")


# Additional helper test for debugging individual permutations
def test_upload_workflow_smoke(page: Page, base_url: str):
    """
    Smoke test to verify basic connectivity.
    This test doesn't use parametrization and just checks if the app is reachable.
    Run with: pytest -k smoke
    """
    try:
        page.goto(base_url, timeout=30000)
        assert page.title(), "Page has no title"
        print(f"✅ Application is reachable at {base_url}")
        print(f"   Page title: {page.title()}")
    except Exception as e:
        pytest.fail(f"Cannot reach application at {base_url}: {str(e)}")
