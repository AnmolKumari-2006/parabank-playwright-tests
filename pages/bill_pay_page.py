"""Page object for Bill Pay / Bill Payment Service (billpay.htm). Requires login."""
from playwright.sync_api import Page, Locator
from pages.base_page import BasePage


class BillPayPage(BasePage):
    URL = "billpay.htm"

    # Form fields, located by their "name" attribute
    FIELD_NAMES = {
        "payee_name": "payee.name",
        "street": "payee.address.street",
        "city": "payee.address.city",
        "state": "payee.address.state",
        "zip_code": "payee.address.zipCode",
        "phone": "payee.phoneNumber",
        "account": "payee.accountNumber",
        "verify_account": "verifyAccount",
        "amount": "amount",
    }

    def __init__(self, page: Page):
        super().__init__(page)
        rp = self.right_panel
        self.from_account_select: Locator = rp.locator("[name='fromAccountId']")
        self.send_button: Locator = rp.locator("input[value='Send Payment']")
        self.result_panel: Locator = rp.locator("#billpayResult")
        self.error_panel: Locator = rp.locator("#billpayError")
        self.validation_errors: Locator = rp.locator(".error").locator("visible=true")
        # Shown when Account # and Verify Account # differ (element seen on the live page)
        self.verify_account_mismatch_error: Locator = rp.locator("#validationModel-verifyAccount-mismatch")
        self.outcome: Locator = rp.locator("#billpayResult, #billpayError, .error").locator("visible=true")

    def field(self, key: str) -> Locator:
        return self.right_panel.locator(f"[name='{self.FIELD_NAMES[key]}']")

    def wait_until_loaded(self):
        self.from_account_select.locator("option").first.wait_for(state="attached")
        return self

    def open(self):
        super().open()
        return self.wait_until_loaded()

    def fill_form(self, values: dict, from_account: str | None = None):
        """values: field key -> text, e.g. {"payee_name": "...", "amount": "25.00"}.
        Keys that are missing are left empty."""
        for key, text in values.items():
            self.field(key).fill(text)
        if from_account is not None:
            self.from_account_select.select_option(label=from_account)

    def submit(self) -> str:
        """Click SEND PAYMENT and wait for ParaBank's answer.

        Returns "result", "error" (error panel) or "validation" (field errors).
        If nothing appears the wait times out, so a missing answer fails the test.
        """
        self.send_button.click()
        self.outcome.first.wait_for(state="visible")
        if self.result_panel.is_visible():
            return "result"
        if self.error_panel.is_visible():
            return "error"
        return "validation"

    def visible_error_texts(self) -> list[str]:
        return [t.strip() for t in self.validation_errors.all_inner_texts() if t.strip()]
