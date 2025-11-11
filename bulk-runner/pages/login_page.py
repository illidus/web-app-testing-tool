"""
Login page object for SoilOptix Customer Portal authentication.
Uses real selectors from the staging environment.
"""

from typing import Dict, Any
from playwright.sync_api import Page


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
        self.page.goto(self.base_url, timeout=self.timeouts.get('page_load', 30000))

    def login(self, username: str, password: str):
        """
        Perform login with the given credentials.

        Args:
            username: Email for login
            password: Password for login

        Raises:
            Exception: If login fails or elements are not found
        """
        try:
            timeout = self.timeouts.get('login', 10000)

            # Find and fill username/email field
            username_selector = self.selectors.get('username_field')
            self.page.locator(username_selector).fill(username, timeout=timeout)

            # Find and fill password field
            password_selector = self.selectors.get('password_field')
            self.page.locator(password_selector).fill(password, timeout=timeout)

            # Click submit button and wait for navigation
            submit_selector = self.selectors.get('submit_button')
            self.page.locator(submit_selector).click(timeout=timeout)

            # Wait for page to load after login
            self.page.wait_for_load_state('networkidle', timeout=timeout)

        except Exception as e:
            raise Exception(f"Login failed: {str(e)}")

    def is_logged_in(self) -> bool:
        """
        Check if the user is currently logged in.

        Returns:
            True if logged in, False otherwise
        """
        try:
            # Check if we're NOT on the login page
            current_url = self.page.url
            return '/login' not in current_url.lower()
        except:
            return False
