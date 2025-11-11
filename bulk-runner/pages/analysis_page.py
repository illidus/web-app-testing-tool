"""
Analysis page object for file uploads and submission.
Handles the Files tab upload workflow and Submit tab submission.
"""

from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from playwright.sync_api import Page


class AnalysisPage:
    """Page object for analysis file management and submission."""

    def __init__(self, page: Page, selectors: Dict[str, Any], timeouts: Dict[str, int]):
        """
        Initialize the analysis page.

        Args:
            page: Playwright page instance
            selectors: Selector configuration from catalog
            timeouts: Timeout configuration from catalog
        """
        self.page = page
        self.files_selectors = selectors.get('files', {})
        self.submit_selectors = selectors.get('submit', {})
        self.timeouts = timeouts

    def navigate_to_files_tab(self):
        """Navigate to the Files tab in Analysis Details."""
        try:
            files_tab_selector = self.files_selectors.get('files_tab')
            self.page.locator(files_tab_selector).click(timeout=self.timeouts.get('page_load', 30000))

            # Wait for tab content to load
            self.page.wait_for_timeout(1000)

        except Exception as e:
            raise Exception(f"Failed to navigate to Files tab: {str(e)}")

    def upload_lab_file(self, file_path: Path) -> Tuple[bool, str]:
        """
        Upload a lab file (CSV or XLSX).

        Args:
            file_path: Path to the lab file

        Returns:
            Tuple of (success: bool, message: str)
        """
        return self._upload_file(
            file_path=file_path,
            file_type='lab',
            upload_button_selector=self.files_selectors.get('upload_lab_button'),
            upload_box_selector=self.files_selectors.get('lab_upload_box'),
            upload_confirm_selector=self.files_selectors.get('lab_upload_confirm')
        )

    def upload_survey_file(self, file_path: Path) -> Tuple[bool, str]:
        """
        Upload a survey file (ZIP containing .mdl, .csv, .log files).

        Args:
            file_path: Path to the survey ZIP file

        Returns:
            Tuple of (success: bool, message: str)
        """
        return self._upload_file(
            file_path=file_path,
            file_type='survey',
            upload_button_selector=self.files_selectors.get('upload_survey_button'),
            upload_box_selector=self.files_selectors.get('survey_upload_box'),
            upload_confirm_selector=self.files_selectors.get('survey_upload_confirm')
        )

    def upload_boundary_file(self, file_path: Path) -> Tuple[bool, str]:
        """
        Upload a boundary file (ZIP containing shapefiles).

        Args:
            file_path: Path to the boundary ZIP file

        Returns:
            Tuple of (success: bool, message: str)
        """
        return self._upload_file(
            file_path=file_path,
            file_type='boundary',
            upload_button_selector=self.files_selectors.get('upload_boundary_button'),
            upload_box_selector=self.files_selectors.get('boundary_upload_box'),
            upload_confirm_selector=self.files_selectors.get('boundary_upload_confirm')
        )

    def _upload_file(
        self,
        file_path: Path,
        file_type: str,
        upload_button_selector: str,
        upload_box_selector: str,
        upload_confirm_selector: str
    ) -> Tuple[bool, str]:
        """
        Generic file upload workflow.

        Workflow:
        1. Click "Upload {type}" button → Popup opens
        2. Click upload box (label) → File input becomes active
        3. Set file input with file path
        4. Click "Upload" button to confirm
        5. Wait for progress bar (for large files) or instant completion
        6. Wait for success message
        7. Close popup

        Args:
            file_path: Path to file to upload
            file_type: Type of file (for logging)
            upload_button_selector: Selector for "Upload X" button
            upload_box_selector: Selector for upload box/label
            upload_confirm_selector: Selector for confirm upload button

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            if not file_path.exists():
                return False, f"{file_type} file not found: {file_path}"

            timeout = self.timeouts.get('file_upload', 120000)

            # Step 1: Click "Upload {type}" button to open popup
            self.page.locator(upload_button_selector).click(timeout=5000)
            self.page.wait_for_timeout(500)

            # Step 2: Find the file input associated with the upload box
            # The upload_box_selector points to a label - we need the input it's associated with
            # Try to find input[type="file"] near the label or just use set_input_files on the label
            self.page.locator(upload_box_selector).set_input_files(str(file_path), timeout=5000)

            # Brief wait for file to be selected
            self.page.wait_for_timeout(500)

            # Step 3: Click "Upload" confirm button
            self.page.locator(upload_confirm_selector).click(timeout=5000)

            # Step 4: Wait for upload to complete
            # For large files: progress bar appears, then success message
            # For small files: success appears instantly
            success_selector = self.files_selectors.get('upload_success')
            error_selector = self.files_selectors.get('upload_error')

            # Wait for either success or error
            try:
                # Try to wait for success message
                self.page.locator(success_selector).wait_for(state='visible', timeout=timeout)
                success_message = self.page.locator(success_selector).text_content() or "Upload successful"

                # Step 5: Close the popup
                close_button_selector = self.files_selectors.get('close_popup')
                self.page.locator(close_button_selector).click(timeout=5000)
                self.page.wait_for_timeout(500)

                return True, f"{file_type} upload successful: {success_message}"

            except:
                # Check if error appeared
                if self.page.locator(error_selector).is_visible(timeout=2000):
                    error_message = self.page.locator(error_selector).text_content() or "Upload error"

                    # Close popup even on error
                    try:
                        close_button_selector = self.files_selectors.get('close_popup')
                        self.page.locator(close_button_selector).click(timeout=5000)
                    except:
                        pass

                    return False, f"{file_type} upload failed: {error_message}"
                else:
                    return False, f"{file_type} upload timed out waiting for result"

        except Exception as e:
            return False, f"{file_type} upload exception: {str(e)}"

    def navigate_to_submit_tab(self):
        """Navigate to the Submit tab."""
        try:
            submit_tab_selector = self.submit_selectors.get('submit_tab')
            self.page.locator(submit_tab_selector).click(timeout=5000)

            # Wait for tab content to load
            self.page.wait_for_timeout(1000)

        except Exception as e:
            raise Exception(f"Failed to navigate to Submit tab: {str(e)}")

    def select_and_save_package(self):
        """
        Select and save a package before submission.

        Note: Package selection is business-specific and depends on lab columns.
        This method selects the first/default package.
        """
        try:
            # Click "Select package" button
            select_button_selector = self.submit_selectors.get('select_package_button')
            self.page.locator(select_button_selector).click(timeout=5000)

            # Brief wait for any UI changes (though user said no visible changes)
            self.page.wait_for_timeout(500)

            # Click "Save package" button
            save_button_selector = self.submit_selectors.get('save_package_button')
            self.page.locator(save_button_selector).click(timeout=5000)

            # Brief wait for save to complete
            self.page.wait_for_timeout(500)

        except Exception as e:
            raise Exception(f"Failed to select/save package: {str(e)}")

    def submit_analysis(self) -> Tuple[bool, str]:
        """
        Submit the analysis and wait for success/failure popup.

        Returns:
            Tuple of (success: bool, message: str)

        The success popup contains: "Analysis submitted successfully"
        The failure popup contains: "Action Failed! You must select and save..."
        """
        try:
            timeout = self.timeouts.get('submit_analysis', 300000)  # 5 minutes max

            # Click "Submit analysis" button
            submit_button_selector = self.submit_selectors.get('submit_analysis_button')
            self.page.locator(submit_button_selector).click(timeout=5000)

            # Wait for result popup (success or failure)
            success_selector = self.submit_selectors.get('success_popup')
            failure_selector = self.submit_selectors.get('failure_popup')

            # Try to detect which popup appears first
            # Use a reasonable timeout since submission can take time
            try:
                # Wait for success popup
                self.page.locator(success_selector).wait_for(state='visible', timeout=timeout)
                success_message = self.page.locator(success_selector).text_content() or "Analysis submitted successfully"
                return True, success_message.strip()

            except:
                # Check if failure popup appeared
                if self.page.locator(failure_selector).is_visible(timeout=2000):
                    failure_message = self.page.locator(failure_selector).text_content() or "Submission failed"
                    return False, failure_message.strip()
                else:
                    return False, "Submission timed out - no success or failure popup detected"

        except Exception as e:
            return False, f"Submit analysis exception: {str(e)}"

    def get_current_status(self) -> str:
        """
        Get any visible status message on the page.

        Returns:
            Status text, or empty string if no status found
        """
        try:
            # Check for success popup
            success_selector = self.submit_selectors.get('success_popup')
            if self.page.locator(success_selector).is_visible(timeout=1000):
                return self.page.locator(success_selector).text_content() or ""

            # Check for failure popup
            failure_selector = self.submit_selectors.get('failure_popup')
            if self.page.locator(failure_selector).is_visible(timeout=1000):
                return self.page.locator(failure_selector).text_content() or ""

            return ""
        except:
            return ""
