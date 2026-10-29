"""Page object for Transfer Funds (transfer.htm). Requires login."""
from playwright.sync_api import Page, Locator
from pages.base_page import BasePage


class TransferPage(BasePage):
    URL = "transfer.htm"

    def __init__(self, page: Page):
        super().__init__(page)
        rp = self.right_panel
        self.amount_input: Locator = rp.locator("#amount")
        self.from_account_select: Locator = rp.locator("#fromAccountId")
        self.to_account_select: Locator = rp.locator("#toAccountId")
        self.transfer_button: Locator = rp.locator("input[value='Transfer']")
        # The result appears on the same page, without loading a new one
        self.result_panel: Locator = rp.locator("#showResult")
        self.error_panel: Locator = rp.locator("#showError")
        # Values repeated in the success message (confirmed on the live site)
        self.amount_result: Locator = rp.locator("#amountResult")
        self.from_account_result: Locator = rp.locator("#fromAccountIdResult")
        self.to_account_result: Locator = rp.locator("#toAccountIdResult")
        self.outcome: Locator = rp.locator("#showResult, #showError").locator("visible=true")

    def wait_until_loaded(self):
        """The account lists are filled in after the page loads; wait for an option."""
        self.from_account_select.locator("option").first.wait_for(state="attached")
        self.to_account_select.locator("option").first.wait_for(state="attached")
        return self

    def open(self):
        super().open()
        return self.wait_until_loaded()

    def fill_form(self, amount: str, from_account: str | None = None, to_account: str | None = None):
        """Fill in the form. Accounts keep their default selection when None."""
        self.amount_input.fill(amount)
        if from_account is not None:
            self.from_account_select.select_option(label=from_account)
        if to_account is not None:
            self.to_account_select.select_option(label=to_account)

    def submit(self) -> str:
        """Click TRANSFER and wait for ParaBank's answer.

        Returns "result" when the success panel is shown, "error" when the
        error panel is shown. If neither appears, the wait times out and the
        test fails, so a missing answer is never hidden.
        """
        self.transfer_button.click()
        self.outcome.first.wait_for(state="visible")
        return "result" if self.result_panel.is_visible() else "error"

    def transfer(self, amount: str, from_account: str | None = None, to_account: str | None = None) -> str:
        self.open()
        self.fill_form(amount, from_account, to_account)
        return self.submit()
