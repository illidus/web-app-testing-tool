"""
Upload page object for file upload and preprocessing workflows.
Uses configurable selectors from catalog.yml.
"""

from pathlib import Path
from typing import Dict, Any, Optional, Literal
from playwright.sync_api import Page


class UploadPage:
    """Page object for upload functionality."""

    def __init__(self, page: Page, base_url: str, selectors: Dict[str, Any], timeouts: Dict[str, int]):
        """
        Initialize the upload page.

        Args:
            page: Playwright page instance
            base_url: Base URL of the application
            selectors: Selector configuration from catalog
            timeouts: Timeout configuration from catalog
        """
        self.page = page
        self.base_url = base_url
        self.upload_selectors = selectors.get('upload', {})
        self.flag_selectors = selectors.get('feature_flags', {})
        self.timeouts = timeouts

    def navigate(self):
        """Navigate to the upload page."""
        upload_url = f"{self.base_url}/upload"
        self.page.goto(upload_url, timeout=self.timeouts.get('page_load', 30000))

    def set_feature_flags(self, flags: Dict[str, str]):
        """
        Set feature flags in the UI if they are visible.

        Args:
            flags: Dictionary mapping flag names to their values (e.g., {"fast_preprocess": "on"})
        """
        for flag_name, flag_value in flags.items():
            try:
                flag_selector = self.flag_selectors.get(flag_name)
                if not flag_selector:
                    # No selector defined, skip
                    continue

                # Try to find the flag control
                flag_element = self.page.locator(flag_selector)

                # Check if element exists and is visible (with short timeout)
                if not flag_element.is_visible(timeout=2000):
                    # Flag not visible in UI, skip
                    continue

                # Determine how to set the flag based on element type
                element_type = flag_element.evaluate("el => el.type")

                if element_type == "checkbox":
                    # Checkbox: check for "on", uncheck for "off"
                    should_check = flag_value.lower() in ("on", "true", "1", "yes")
                    if should_check:
                        flag_element.check()
                    else:
                        flag_element.uncheck()

                elif element_type in ("radio", "radiobutton"):
                    # Radio button: click if value matches
                    if flag_value.lower() in ("on", "true", "1", "yes"):
                        flag_element.click()

                elif element_type == "select-one":
                    # Dropdown: select the value
                    flag_element.select_option(flag_value)

                else:
                    # Text input or other: fill with value
                    flag_element.fill(flag_value)

            except Exception as e:
                # Flag setting failed, but continue (flags might not be visible)
                print(f"⚠️  Could not set flag {flag_name}={flag_value}: {e}")
                continue

    def upload_file(self, file_path: Path):
        """
        Upload a file using the file input.

        Args:
            file_path: Path to the file to upload

        Raises:
            Exception: If file upload fails or file doesn't exist
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Dataset file not found: {file_path}")

        try:
            # Find the file input element
            file_input_selector = self.upload_selectors.get('file_input', "input[type='file']")
            file_input = self.page.locator(file_input_selector)

            # Wait for the input to be present (it might be hidden)
            file_input.wait_for(state="attached", timeout=self.timeouts.get('upload', 5000))

            # Set the file
            file_input.set_input_files(str(file_path))

            # Brief wait for file to be processed by frontend
            self.page.wait_for_timeout(500)

        except Exception as e:
            raise Exception(f"File upload failed: {str(e)}")

    def submit(self):
        """
        Click the submit/upload button to start processing.

        Raises:
            Exception: If submit button is not found or click fails
        """
        try:
            submit_selector = self.upload_selectors.get('submit_button', "button#upload-submit")
            submit_button = self.page.locator(submit_selector)

            # Wait for button to be visible and enabled
            submit_button.wait_for(state="visible", timeout=self.timeouts.get('upload', 5000))

            # Click the button
            submit_button.click()

            # Brief wait for submission to start
            self.page.wait_for_timeout(1000)

        except Exception as e:
            raise Exception(f"Submit failed: {str(e)}")

    def wait_for_result(self, expected_outcome: Literal["success", "input_error"]) -> tuple[bool, str]:
        """
        Wait for the preprocessing result to appear.

        Args:
            expected_outcome: Expected outcome - "success" or "input_error"

        Returns:
            Tuple of (success: bool, message: str)
            - success: True if the expected outcome occurred
            - message: Descriptive message about what was found
        """
        timeout = self.timeouts.get('preprocessing', 120000)

        # Define what we're looking for based on expected outcome
        success_selector = self.upload_selectors.get('success_indicator', "text=Preprocessing complete")
        error_selector = self.upload_selectors.get('error_banner', ".error-banner")

        try:
            if expected_outcome == "success":
                # Wait for success indicator
                success_element = self.page.locator(success_selector)
                success_element.wait_for(state="visible", timeout=timeout)

                # Verify no error is shown
                error_element = self.page.locator(error_selector)
                if error_element.is_visible(timeout=1000):
                    error_text = error_element.text_content() or "Unknown error"
                    return False, f"Expected success but found error: {error_text}"

                return True, "Preprocessing completed successfully"

            elif expected_outcome == "input_error":
                # Wait for error banner
                error_element = self.page.locator(error_selector)
                error_element.wait_for(state="visible", timeout=timeout)

                error_text = error_element.text_content() or "Error detected"

                # Verify no success is shown
                success_element = self.page.locator(success_selector)
                if success_element.is_visible(timeout=1000):
                    return False, f"Expected error but found success indicator"

                return True, f"Input error detected as expected: {error_text}"

            else:
                return False, f"Unknown expected outcome: {expected_outcome}"

        except Exception as e:
            # Timeout or other error
            # Try to capture what's actually on the page
            try:
                page_text = self.page.locator("body").text_content()[:500]
                return False, f"Timeout waiting for {expected_outcome}. Page content: {page_text}..."
            except:
                return False, f"Timeout waiting for {expected_outcome}: {str(e)}"

    def get_current_status(self) -> str:
        """
        Get the current status message from the page.

        Returns:
            Status text, or empty string if no status found
        """
        try:
            # Look for common status indicators
            status_selectors = [
                ".status-message",
                ".processing-status",
                ".upload-status",
                "#status"
            ]

            for selector in status_selectors:
                status_elem = self.page.locator(selector)
                if status_elem.is_visible(timeout=1000):
                    return status_elem.text_content() or ""

            return ""
        except:
            return ""

    def has_error(self) -> bool:
        """
        Check if an error is currently displayed.

        Returns:
            True if error is visible, False otherwise
        """
        try:
            error_selector = self.upload_selectors.get('error_banner', ".error-banner")
            error_element = self.page.locator(error_selector)
            return error_element.is_visible(timeout=1000)
        except:
            return False

    def get_error_message(self) -> str:
        """
        Get the error message text if an error is displayed.

        Returns:
            Error message text, or empty string if no error
        """
        try:
            error_selector = self.upload_selectors.get('error_banner', ".error-banner")
            error_element = self.page.locator(error_selector)
            if error_element.is_visible(timeout=1000):
                return error_element.text_content() or ""
            return ""
        except:
            return ""
