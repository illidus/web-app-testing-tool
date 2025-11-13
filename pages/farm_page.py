"""
Farm page object for field creation and management.
Handles navigation to farm and creating test fields.
"""

from datetime import datetime
from typing import Dict, Any
from playwright.sync_api import Page


class FarmPage:
    """Page object for farm and field management."""

    def __init__(
        self,
        page: Page,
        base_url: str,
        farm_id: int,
        selectors: Dict[str, Any],
        timeouts: Dict[str, int],
        business_id: int = None
    ):
        """
        Initialize the farm page.

        Args:
            page: Playwright page instance
            base_url: Base URL of the application
            farm_id: Farm ID to navigate to (used if business_id not provided)
            selectors: Selector configuration from catalog
            timeouts: Timeout configuration from catalog
            business_id: Optional business ID for multi-business testing
        """
        self.page = page
        self.base_url = base_url
        self.farm_id = farm_id
        self.business_id = business_id
        self.farm_selectors = selectors.get('farm', {})
        self.analysis_selectors = selectors.get('analysis', {})
        self.timeouts = timeouts

    def navigate(self):
        """
        Navigate to the business or farm page.

        If business_id is set, navigates to /Businesses/{business_id}.
        Otherwise, navigates to /Farms/{farm_id} (legacy behavior).
        """
        if self.business_id:
            # Multi-business testing: navigate to business page
            nav_url = f"{self.base_url}/Businesses/{self.business_id}"
            print(f"   Navigating to Business {self.business_id}")
        else:
            # Legacy: navigate directly to farm page
            nav_url = f"{self.base_url}/Farms/{self.farm_id}"
            print(f"   Navigating to Farm {self.farm_id}")

        self.page.goto(nav_url, timeout=self.timeouts.get('page_load', 30000))

    def create_field(self, field_name: str) -> str:
        """
        Create a new field with the given name.

        If on a business page, will first create a farm then create the field.

        Args:
            field_name: Name for the new field

        Returns:
            The field name that was created

        Raises:
            Exception: If field creation fails
        """
        try:
            timeout = self.timeouts.get('field_creation', 15000)
            current_url = self.page.url

            # If we're on a business page, we need to create a farm first
            if '/Businesses/' in current_url:
                print(f"   On business page, creating farm first...")
                farm_name = f"TestFarm_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                self._create_farm(farm_name)
                print(f"   ✅ Farm created, now creating field...")

            # Remove any toast notifications using JavaScript (they block clicks even with force=True)
            try:
                self.page.evaluate("""
                    document.querySelectorAll('.Toastify__toast-container').forEach(el => el.remove());
                    document.querySelectorAll('.Toastify__toast').forEach(el => el.remove());
                """)
                self.page.wait_for_timeout(1000)  # Wait longer for DOM to settle
            except:
                pass  # Toasts may not exist, that's fine

            # Click "Add new" field button
            # On a farm page, use the generic .button__add-small selector (it's for adding fields)
            # Use force=True to bypass any remaining toast notifications
            if '/Farms/' in self.page.url:
                # On farm page - the .button__add-small is for adding fields
                add_button_selector = '.button__add-small'
            else:
                # Use configured selector
                add_button_selector = self.farm_selectors.get('add_field_button')
            self.page.locator(add_button_selector).click(force=True, timeout=timeout)

            # Wait for popup to appear
            self.page.wait_for_timeout(500)

            # Enter field name
            field_input_selector = self.farm_selectors.get('field_name_input')
            self.page.locator(field_input_selector).fill(field_name, timeout=timeout)

            # Click create button
            create_button_selector = self.farm_selectors.get('create_field_button')
            self.page.locator(create_button_selector).click(timeout=timeout)

            # Wait for navigation to the new field page (auto-navigates after creation)
            # URL format: https://.../Fields/XXXXX
            self.page.wait_for_url(lambda url: '/Fields/' in url, timeout=timeout)

            # Retry mechanism for backend race condition - field may not be ready immediately
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Check if page loaded successfully (not 404)
                    if 'NOT FOUND' in self.page.content():
                        if attempt < max_retries - 1:
                            self.page.wait_for_timeout(2000)  # Wait 2 seconds
                            self.page.reload(timeout=timeout)  # Reload the page
                            continue
                        else:
                            raise Exception('Field page still returning 404 after retries')
                    
                    # Wait for Create Analysis button to confirm page is ready
                    self.page.locator('.button__primary-create').wait_for(state='visible', timeout=5000)
                    break  # Success!
                except Exception as e:
                    if attempt < max_retries - 1:
                        self.page.wait_for_timeout(2000)
                        self.page.reload(timeout=timeout)
                    else:
                        raise

            return field_name

        except Exception as e:
            raise Exception(f"Field creation failed: {str(e)}")

    def _create_farm(self, farm_name: str):
        """
        Helper method to create a farm when on a business page.

        Args:
            farm_name: Name for the new farm
        """
        timeout = self.timeouts.get('field_creation', 15000)

        # Remove any toast notifications
        try:
            self.page.evaluate("""
                document.querySelectorAll('.Toastify__toast-container').forEach(el => el.remove());
                document.querySelectorAll('.Toastify__toast').forEach(el => el.remove());
            """)
            self.page.wait_for_timeout(500)
        except:
            pass

        # Click "Add new Farm" button
        farm_button_selector = self.farm_selectors.get('add_field_button')  # Uses same selector
        self.page.locator(farm_button_selector).click(force=True, timeout=timeout)

        # Wait for popup to appear
        self.page.wait_for_timeout(500)

        # Enter farm name
        farm_input_selector = self.farm_selectors.get('field_name_input')  # Uses same input
        self.page.locator(farm_input_selector).fill(farm_name, timeout=timeout)

        # Click create button
        create_button_selector = self.farm_selectors.get('create_field_button')  # Uses same button
        self.page.locator(create_button_selector).click(timeout=timeout)

        # Wait for navigation to the new farm page
        # URL format: https://.../Farms/XXXXX
        self.page.wait_for_url(lambda url: '/Farms/' in url, timeout=timeout)
        self.page.wait_for_timeout(1000)  # Let the farm page load

    def create_analysis(self) -> str:
        """
        Create a new analysis and extract the analysis ID from the details link.

        Returns:
            The analysis ID (extracted from URL)

        Raises:
            Exception: If analysis creation fails
        """
        try:
            timeout = self.timeouts.get('analysis_creation', 15000)

            # Remove any toast notifications using JavaScript (they block clicks even with force=True)
            try:
                self.page.evaluate("""
                    document.querySelectorAll('.Toastify__toast-container').forEach(el => el.remove());
                    document.querySelectorAll('.Toastify__toast').forEach(el => el.remove());
                """)
                self.page.wait_for_timeout(500)
            except:
                pass  # Toasts may not exist, that's fine

            # Click "Create analysis" button
            # Use force=True to bypass any toast notifications that may be overlaying
            create_button_selector = self.analysis_selectors.get('create_analysis_button')
            self.page.locator(create_button_selector).click(force=True, timeout=timeout)

            # Wait for popup
            self.page.wait_for_timeout(500)

            # Click confirm button in popup
            confirm_button_selector = self.analysis_selectors.get('create_confirm_button')
            self.page.locator(confirm_button_selector).first.click(timeout=timeout)

            # Wait for success popup with analysis details link
            self.page.wait_for_timeout(1000)

            # Click the "Analysis Details" link to navigate
            details_link_selector = self.analysis_selectors.get('analysis_details_link')
            self.page.locator(details_link_selector).click(timeout=timeout)

            # Wait for navigation to analysis page (URL-based, more reliable than networkidle)
            self.page.wait_for_url(lambda url: '/Analyses/' in url, timeout=timeout)

            # Extract analysis ID from URL
            # URL format: https://customerportalstaging.local.soiloptix.com/Analyses/5000419
            current_url = self.page.url
            if '/Analyses/' in current_url:
                analysis_id = current_url.split('/Analyses/')[-1].split('/')[0]
                return analysis_id
            else:
                raise Exception(f"Could not extract analysis ID from URL: {current_url}")

        except Exception as e:
            raise Exception(f"Analysis creation failed: {str(e)}")

    @staticmethod
    def generate_field_name(dataset_id: str = "", business_name: str = "SoilOptix") -> str:
        """
        Generate a test field name with timestamp.

        Args:
            dataset_id: Optional dataset identifier
            business_name: Optional business name

        Returns:
            Generated field name in format: AutoTest_YYYYMMDD_HHMMSS_Business_Dataset
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        parts = ["AutoTest", timestamp]

        if business_name:
            parts.append(business_name)
        if dataset_id:
            parts.append(dataset_id)

        return "_".join(parts)
