"""
Login page object for authentication flows.
Uses configurable selectors from catalog.yml.
"""

from typing import Dict, Any
from playwright.sync_api import Page, expect


class LoginPage:
    """Page object for login functionality."""

    def __init__(self, page: Page, base_url: str, selectors: Dict[str, Any], timeouts: Dict[str, int]):
        """
        Initialize the login page.

        Args:
            page: Playwright page instance
            base_url: Base URL of the application
            selectors: Selector configuration from catalog
            timeouts: Timeout configuration from catalog
        """
        self.page = page
        self.base_url = base_url
        self.selectors = selectors.get('login', {})
        self.timeouts = timeouts

    def navigate(self):
        """Navigate to the login page."""
        login_url = f"{self.base_url}/login"
        self.page.goto(login_url, timeout=self.timeouts.get('page_load', 30000))

    def login(self, username: str, password: str):
        """
        Perform login with the given credentials.

        Args:
            username: Username/email for login
            password: Password for login

        Raises:
            Exception: If login fails or elements are not found
        """
        try:
            # Wait for page to be ready
            timeout = self.timeouts.get('login', 10000)

            # Find and fill username field
            username_selector = self.selectors.get('username_field', "input[name='username']")
            username_field = self.page.locator(username_selector)
            username_field.wait_for(state="visible", timeout=timeout)
            username_field.fill(username)

            # Find and fill password field
            password_selector = self.selectors.get('password_field', "input[name='password']")
            password_field = self.page.locator(password_selector)
            password_field.wait_for(state="visible", timeout=timeout)
            password_field.fill(password)

            # Click submit button
            submit_selector = self.selectors.get('submit_button', "button[type='submit']")
            submit_button = self.page.locator(submit_selector)
            submit_button.wait_for(state="visible", timeout=timeout)

            # Click and wait for navigation
            with self.page.expect_navigation(timeout=timeout, wait_until="networkidle"):
                submit_button.click()

            # Verify we're no longer on the login page (simple check)
            # In a real app, you might check for a specific element or URL pattern
            self.page.wait_for_timeout(1000)  # Brief wait for redirect

        except Exception as e:
            raise Exception(f"Login failed: {str(e)}")

    def is_logged_in(self) -> bool:
        """
        Check if the user is currently logged in.
        This is a simple heuristic - real implementation would check for
        user menu, session cookie, or other indicators.

        Returns:
            True if logged in, False otherwise
        """
        try:
            # Check if we're NOT on the login page
            current_url = self.page.url
            return '/login' not in current_url
        except:
            return False

    def get_error_message(self) -> str:
        """
        Get the error message displayed on the login page, if any.

        Returns:
            Error message text, or empty string if no error
        """
        try:
            # Look for common error selectors
            error_selectors = [
                ".error-message",
                ".alert-error",
                ".login-error",
                "[role='alert']"
            ]

            for selector in error_selectors:
                error_elem = self.page.locator(selector)
                if error_elem.is_visible(timeout=1000):
                    return error_elem.text_content() or ""

            return ""
        except:
            return ""
