"""
Pytest configuration and fixtures for bulk test runner.
Handles test matrix generation, browser setup, and artifact management.
"""

import os
import re
import itertools
from pathlib import Path
from typing import Any, Dict, List, Tuple
from datetime import datetime

import pytest
import yaml
from dotenv import load_dotenv
from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright


# Load environment variables
load_dotenv()

# Global configuration
BASE_DIR = Path(__file__).parent
CATALOG_PATH = BASE_DIR / "catalog.yml"
OUT_DIR = BASE_DIR / "out"
BUGS_DIR = BASE_DIR / "bugs"
TRACES_DIR = OUT_DIR / "traces"
SCREENSHOTS_DIR = OUT_DIR / "screenshots"

# Ensure output directories exist
OUT_DIR.mkdir(exist_ok=True)
BUGS_DIR.mkdir(exist_ok=True)
TRACES_DIR.mkdir(exist_ok=True)
SCREENSHOTS_DIR.mkdir(exist_ok=True)


def load_catalog() -> Dict[str, Any]:
    """Load the test catalog configuration."""
    with open(CATALOG_PATH, 'r') as f:
        return yaml.safe_load(f)


def sanitize_filename(s: str) -> str:
    """Sanitize a string to be safe for use as a filename."""
    # Replace unsafe characters with underscores
    s = re.sub(r'[<>:"/\\|?*]', '_', s)
    # Replace spaces with underscores
    s = s.replace(' ', '_')
    # Remove any other non-alphanumeric characters except dash and underscore
    s = re.sub(r'[^a-zA-Z0-9_\-.]', '', s)
    # Limit length
    return s[:200]


def should_include_dataset(dataset: Dict[str, Any]) -> bool:
    """
    Determine if a dataset should be included based on its classification
    and environment variables.
    """
    classification = dataset.get('classification', 'synthetic')

    # Always include synthetic and sanitized
    if classification in ('synthetic', 'sanitized'):
        return True

    # Only include real-sensitive if explicitly enabled
    if classification == 'real-sensitive':
        include_sensitive = os.getenv('INCLUDE_SENSITIVE', 'false').lower()
        return include_sensitive in ('true', '1', 'yes')

    # Unknown classification, exclude by default
    return False


def generate_flag_combinations(flags: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Generate all combinations of feature flag values.
    Returns a list of dictionaries mapping flag names to values.
    """
    if not flags:
        return [{}]

    flag_names = [flag['name'] for flag in flags]
    flag_values = [flag['values'] for flag in flags]

    combinations = []
    for combo in itertools.product(*flag_values):
        combinations.append(dict(zip(flag_names, combo)))

    return combinations


def pytest_addoption(parser):
    """Add custom command-line options."""
    parser.addoption(
        "--include-sensitive",
        action="store_true",
        default=False,
        help="Include real-sensitive datasets in test runs"
    )
    parser.addoption(
        "--headed",
        action="store_true",
        default=False,
        help="Run browser in headed mode (visible)"
    )
    parser.addoption(
        "--slow-mo",
        type=int,
        default=0,
        help="Slow down browser operations by N milliseconds"
    )


def pytest_configure(config):
    """Configure pytest with custom markers and environment overrides."""
    # Override environment variable if --include-sensitive is passed
    if config.getoption("--include-sensitive"):
        os.environ['INCLUDE_SENSITIVE'] = 'true'

    # Register custom markers
    config.addinivalue_line("markers", "synthetic: mark test as using synthetic data")
    config.addinivalue_line("markers", "sanitized: mark test as using sanitized data")
    config.addinivalue_line("markers", "sensitive: mark test as using real-sensitive data")


def pytest_generate_tests(metafunc):
    """
    Generate parametrized tests for all permutations in the test matrix.
    Creates the Cartesian product of: roles × flag_combinations × datasets × repeats.
    """
    if "test_params" not in metafunc.fixturenames:
        return

    catalog = load_catalog()

    # Extract configuration
    roles = catalog.get('roles', [])
    flags = catalog.get('flags', [])
    datasets = catalog.get('datasets', [])
    repeats = catalog.get('repeats', 1)

    # Filter datasets based on classification
    datasets = [ds for ds in datasets if should_include_dataset(ds)]

    # Generate flag combinations
    flag_combinations = generate_flag_combinations(flags)

    # Generate all permutations
    test_cases = []
    test_ids = []

    for role in roles:
        for flag_combo in flag_combinations:
            for dataset in datasets:
                for repeat_num in range(repeats):
                    # Create test parameters
                    params = {
                        'role': role,
                        'flags': flag_combo,
                        'dataset': dataset,
                        'repeat': repeat_num,
                        'catalog': catalog,
                    }
                    test_cases.append(params)

                    # Create readable test ID
                    flag_str = '_'.join([f"{k}={v}" for k, v in flag_combo.items()]) if flag_combo else 'noflags'
                    test_id = f"{role}_{flag_str}_{dataset['id']}_rep{repeat_num}"
                    test_ids.append(test_id)

    # Parametrize the tests
    metafunc.parametrize("test_params", test_cases, ids=test_ids)


@pytest.fixture(scope="session")
def playwright_instance():
    """Provide a Playwright instance for the entire test session."""
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="session")
def browser_type_launch_args(pytestconfig):
    """Configure browser launch arguments based on CLI options."""
    return {
        "headless": not pytestconfig.getoption("--headed"),
        "slow_mo": pytestconfig.getoption("--slow-mo"),
    }


@pytest.fixture(scope="session")
def browser(playwright_instance: Playwright, browser_type_launch_args):
    """Provide a browser instance for the entire test session."""
    browser = playwright_instance.chromium.launch(**browser_type_launch_args)
    yield browser
    browser.close()


@pytest.fixture
def context(browser: Browser, test_params: Dict[str, Any]):
    """Provide a fresh browser context for each test with tracing enabled."""
    catalog = test_params['catalog']

    # Create context with reasonable defaults
    ctx = browser.new_context(
        viewport={"width": 1280, "height": 720},
        ignore_https_errors=True,  # For staging environments
    )

    # Start tracing for failure debugging
    ctx.tracing.start(screenshots=True, snapshots=True, sources=True)

    yield ctx

    # Save trace on failure (will be checked in test teardown)
    ctx.tracing.stop()
    ctx.close()


@pytest.fixture
def page(context: BrowserContext):
    """Provide a fresh page for each test."""
    page = context.new_page()
    yield page
    page.close()


@pytest.fixture
def base_url():
    """Provide the base URL from environment variables or catalog."""
    url = os.getenv('BASE_URL')
    if not url:
        # Try to get from catalog as fallback
        catalog = load_catalog()
        url = catalog.get('base_url')
    if not url:
        pytest.fail("BASE_URL not set in environment variables or catalog.yml")
    return url


@pytest.fixture
def farm_id(test_params: Dict[str, Any]):
    """Provide the farm ID from catalog or environment variables."""
    # Try environment variable first
    farm_id = os.getenv('FARM_ID')
    if farm_id:
        return int(farm_id)

    # Fall back to catalog
    catalog = test_params.get('catalog', {})
    farm_id = catalog.get('farm_id')
    if farm_id:
        return int(farm_id)

    pytest.fail("FARM_ID not set in environment variables or catalog.yml")


@pytest.fixture
def business_id(test_params: Dict[str, Any]):
    """
    Provide the business ID from dataset or environment variables.

    Business ID determines which business page to navigate to.
    Falls back to None if not specified (uses farm_id instead).
    """
    # Try dataset-specific business_id first
    dataset = test_params.get('dataset', {})
    biz_id = dataset.get('business_id')
    if biz_id:
        return int(biz_id)

    # Try environment variable
    biz_id = os.getenv('BUSINESS_ID')
    if biz_id:
        return int(biz_id)

    # Fall back to catalog
    catalog = test_params.get('catalog', {})
    biz_id = catalog.get('business_id')
    if biz_id:
        return int(biz_id)

    # Return None - will use farm_id navigation instead
    return None


@pytest.fixture
def credentials(test_params: Dict[str, Any]):
    """Provide role-specific credentials from environment variables."""
    role = test_params['role']
    username = os.getenv(f"{role.upper()}_USER")
    password = os.getenv(f"{role.upper()}_PASS")

    if not username or not password:
        pytest.fail(f"Credentials for role '{role}' are not set in environment variables")

    return {"username": username, "password": password}


@pytest.fixture
def artifact_paths(test_params: Dict[str, Any], request):
    """Generate file paths for test artifacts (screenshots, traces, logs)."""
    # Create a safe filename from test parameters
    role = test_params['role']
    dataset_id = test_params['dataset']['id']
    repeat = test_params['repeat']
    flag_str = '_'.join([f"{k}={v}" for k, v in test_params['flags'].items()]) if test_params['flags'] else 'noflags'

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    base_name = sanitize_filename(f"{role}_{flag_str}_{dataset_id}_rep{repeat}_{timestamp}")

    return {
        'screenshot': SCREENSHOTS_DIR / f"{base_name}.png",
        'trace': TRACES_DIR / f"{base_name}.zip",
        'log': OUT_DIR / f"{base_name}.log",
        'test_id': f"{role}_{flag_str}_{dataset_id}_rep{repeat}",
        'base_name': base_name,
    }


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Hook to capture test failures and save artifacts.
    This runs after each test phase (setup, call, teardown).
    """
    outcome = yield
    report = outcome.get_result()

    # Only process failures in the test call phase
    if report.when == "call" and report.failed:
        # Get fixtures from the test
        try:
            context = item.funcargs.get('context')
            page = item.funcargs.get('page')
            artifact_paths = item.funcargs.get('artifact_paths')
            test_params = item.funcargs.get('test_params')

            if page and artifact_paths:
                # Save screenshot
                try:
                    page.screenshot(path=str(artifact_paths['screenshot']), full_page=True)
                    print(f"\n Screenshot saved: {artifact_paths['screenshot']}")
                except Exception as e:
                    print(f"\n  Failed to save screenshot: {e}")

                # Get page content snippet (capped at 100KB)
                try:
                    content = page.content()
                    if len(content) > 100000:
                        content = content[:100000] + "\n\n... [TRUNCATED]"

                    # Save to log file
                    with open(artifact_paths['log'], 'w') as f:
                        f.write(f"Test: {artifact_paths['test_id']}\n")
                        f.write(f"Time: {datetime.now().isoformat()}\n")
                        f.write(f"Role: {test_params['role']}\n")
                        f.write(f"Dataset: {test_params['dataset']['id']}\n")
                        f.write(f"Flags: {test_params['flags']}\n")
                        f.write(f"Expected: {test_params['dataset']['expected']}\n")
                        f.write(f"\nError: {report.longreprtext}\n")
                        f.write(f"\n{'='*80}\n")
                        f.write(f"Page Content (capped):\n")
                        f.write(f"{'='*80}\n")
                        f.write(content)

                    print(f" Log saved: {artifact_paths['log']}")
                except Exception as e:
                    print(f"  Failed to save log: {e}")

            # Save trace
            if context and artifact_paths:
                try:
                    context.tracing.stop(path=str(artifact_paths['trace']))
                    print(f" Trace saved: {artifact_paths['trace']}")
                    # Restart tracing for potential teardown
                    context.tracing.start(screenshots=True, snapshots=True, sources=True)
                except Exception as e:
                    print(f"  Failed to save trace: {e}")

        except Exception as e:
            print(f"\n  Error in failure handler: {e}")
