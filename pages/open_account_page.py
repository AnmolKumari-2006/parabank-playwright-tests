"""Page object for Open New Account (openaccount.htm). Requires login."""
from playwright.sync_api import Page, Locator
from pages.base_page import BasePage


class OpenAccountPage(BasePage):
    URL = "openaccount.htm"

    def __init__(self, page: Page):
        super().__init__(page)
        rp = self.right_panel
        self.type_select: Locator = rp.locator("#type")
        self.from_account_select: Locator = rp.locator("#fromAccountId")
        self.open_button: Locator = rp.locator("input[value='Open New Account']")
        # Shown after a successful opening
        self.result_panel: Locator = rp.locator("#openAccountResult")
        self.new_account_link: Locator = rp.locator("#newAccountId")
        self.error_panel: Locator = rp.locator("#openAccountError")

    def wait_until_loaded(self):
        """The From-account list is filled in after the page loads; wait for an option."""
        self.from_account_select.locator("option").first.wait_for(state="attached")
        return self

    def open(self):
        super().open()
        return self.wait_until_loaded()

    def open_new_account(self, account_type: str, from_account: str | None = None) -> str:
        """Open an account of the given type (CHECKING or SAVINGS).

        from_account: source account number; the default selection is kept if None.
        Returns the new account number shown by ParaBank.
        """
        self.type_select.select_option(label=account_type)
        if from_account is not None:
            self.from_account_select.select_option(label=from_account)
        self.open_button.click()
        self.new_account_link.wait_for(state="visible")
        return self.new_account_link.inner_text().strip()
