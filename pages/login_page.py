"""Page object for the Customer Login panel on the Home page (index.htm)."""
from playwright.sync_api import Page, Locator
from pages.base_page import BasePage


class LoginPage(BasePage):
    URL = "index.htm"

    def __init__(self, page: Page):
        super().__init__(page)
        panel = page.locator("#loginPanel")
        self.username_input: Locator = panel.locator("input[name='username']")
        self.password_input: Locator = panel.locator("input[name='password']")
        self.login_button: Locator = panel.locator("input[type='submit'][value='Log In']")
        # After a failed login ParaBank shows its message in the right panel
        self.error_message: Locator = self.right_panel.locator("p.error")

    def login(self, username: str, password: str):
        """Fill in the login form and submit it. Does not open the page first."""
        self.username_input.fill(username)
        self.password_input.fill(password)
        # LOG IN posts the form and loads a new page; wait for it
        self.click_and_wait_for_page(self.login_button)
