"""Page object for Accounts Overview (overview.htm). Requires login."""
from decimal import Decimal
from playwright.sync_api import Page, Locator
from pages.base_page import BasePage
from utils.money import parse_money


class AccountsOverviewPage(BasePage):
    URL = "overview.htm"

    def __init__(self, page: Page):
        super().__init__(page)
        self.table: Locator = self.right_panel.locator("#accountTable")
        # Account rows are the rows whose first cell contains an account link
        self.account_links: Locator = self.table.locator("tbody tr td:first-child a")

    def wait_until_loaded(self):
        """The account list may be filled in after the page loads; wait for the first account."""
        self.account_links.first.wait_for(state="visible")
        return self

    def open(self):
        super().open()
        return self.wait_until_loaded()

    def accounts(self) -> list[dict]:
        """One dict per account: number, balance, available (Decimals)."""
        result = []
        for link in self.account_links.all():
            cells = link.locator("xpath=ancestor::tr[1]/td")
            result.append({
                "number": link.inner_text().strip(),
                "balance": parse_money(cells.nth(1).inner_text()),
                "available": parse_money(cells.nth(2).inner_text()),
            })
        return result

    def total(self) -> Decimal:
        total_row = self.table.locator("tr", has_text="Total")
        return parse_money(total_row.locator("td").nth(1).inner_text())
