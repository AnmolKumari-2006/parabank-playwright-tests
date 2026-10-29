"""Base class with elements and actions shared by every ParaBank page."""
import pytest
from playwright.sync_api import Page, Locator, Response

CLOUDFLARE_SKIP_REASON = (
    "Blocked by Cloudflare (HTTP 403): the request never reached ParaBank, "
    "so ParaBank's own behaviour could not be tested.")


class BasePage:
    URL = ""  # each page sets its own relative path, e.g. "register.htm"

    def __init__(self, page: Page):
        self.page = page
        # Left panel (visible on every page)
        self.left_panel: Locator = page.locator("#leftPanel")
        self.account_services_heading: Locator = self.left_panel.get_by_role("heading", name="Account Services")
        self.logout_link: Locator = self.left_panel.get_by_role("link", name="Log Out")
        # "Welcome <first name> <last name>" line above the Account Services menu
        self.welcome_text: Locator = self.left_panel.locator("p.smallText")
        # Right panel (main content of every page)
        self.right_panel: Locator = page.locator("#rightPanel")
        self.page_title: Locator = self.right_panel.locator("h1.title").first
        # HTTP status of the last page loaded by click_and_wait_for_page()
        self.last_status: int | None = None

    def open(self):
        """Open this page using the --base-url from pytest.ini."""
        response = self.page.goto(self.URL)
        self._record(response)
        return self

    def _record(self, response: Response | None):
        """Remember the HTTP status and skip the test if Cloudflare blocked the request.

        The public ParaBank site sits behind Cloudflare, which stops some requests
        (e.g. SQL injection text) before they reach ParaBank. Such a test can
        neither pass nor fail on ParaBank's behaviour, so it is skipped with the
        reason shown in the report (status "Blocked" in the Test Case Sheet).
        """
        self.last_status = response.status if response is not None else None
        if self.last_status == 403 and "cloudflare" in self.page.content().lower():
            pytest.skip(CLOUDFLARE_SKIP_REASON)

    def click_and_wait_for_page(self, target: Locator):
        """Click something that loads a new page, wait for it, and remember its HTTP status."""
        with self.page.expect_navigation() as navigation:
            target.click()
        self._record(navigation.value)

    def logout(self):
        # Log Out loads the Home page; wait for it before continuing
        self.click_and_wait_for_page(self.logout_link)

    def is_logged_in(self) -> bool:
        """True when the Account Services menu is shown (only after login)."""
        return self.account_services_heading.is_visible()

    def shows_internal_error(self) -> bool:
        """True when the server failed, in any of these three forms:

        1. the last loaded page returned HTTP status 500 or higher;
        2. the page is not a normal ParaBank page at all (no #rightPanel),
           e.g. a raw server error page;
        3. ParaBank's own error message is shown. Confirmed on the live site
           (Transfer Funds, empty amount): "An internal error has occurred and has been logged."
        """
        if self.last_status is not None and self.last_status >= 500:
            return True
        if self.right_panel.count() == 0:
            return True
        return self.right_panel.get_by_text("An internal error has occurred").is_visible()

    def page_text(self, limit: int = 300) -> str:
        """Visible text of the whole page, shortened; used as evidence in failure messages."""
        return self.page.locator("body").inner_text().strip()[:limit]
