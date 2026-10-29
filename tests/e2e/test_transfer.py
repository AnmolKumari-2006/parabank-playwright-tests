"""E2E - Transfer Funds (1 positive, 2 negative). Each test starts with a fresh,
logged-in customer who has two accounts (observed: 415.50 USD and 100.00 USD)."""
from decimal import Decimal
import pytest
from playwright.sync_api import Page, expect
from pages.transfer_page import TransferPage
from pages.accounts_overview_page import AccountsOverviewPage

pytestmark = pytest.mark.e2e


def balances(page: Page) -> dict:
    return {a["number"]: a["balance"] for a in AccountsOverviewPage(page).open().accounts()}


def test_E2E_TRF_01_transfer_valid_amount_between_own_accounts(page: Page, two_accounts):
    """Positive: 50.00 moves from the first account to the second."""
    first, second = two_accounts["first"], two_accounts["second"]
    before = balances(page)

    transfer = TransferPage(page)
    outcome = transfer.transfer("50.00", from_account=first, to_account=second)

    assert outcome == "result", f"Transfer did not complete. Page shows: {transfer.page_text()!r}"
    expect(transfer.result_panel).to_contain_text("Transfer Complete!")
    expect(transfer.amount_result).to_have_text("$50.00")
    expect(transfer.from_account_result).to_have_text(first)
    expect(transfer.to_account_result).to_have_text(second)
    after = balances(page)
    assert after[first] == before[first] - Decimal("50.00")
    assert after[second] == before[second] + Decimal("50.00")


def test_E2E_TRF_02_transfer_with_empty_amount(page: Page, two_accounts):
    """Negative: an empty amount must give a validation message, not a server error."""
    first, second = two_accounts["first"], two_accounts["second"]
    before = balances(page)

    transfer = TransferPage(page).open()
    transfer.fill_form("", from_account=first, to_account=second)
    outcome = transfer.submit()

    assert outcome != "result", "A transfer was completed without an amount"
    assert not transfer.shows_internal_error(), (
        f"Server error instead of a validation message. Page shows: {transfer.page_text()!r}")
    assert balances(page) == before, "Balances changed although no amount was entered"


def test_E2E_TRF_03_transfer_more_than_available_balance(page: Page, two_accounts):
    """Negative: an amount 0.01 above the available balance must be refused."""
    first, second = two_accounts["first"], two_accounts["second"]
    before = balances(page)
    too_much = before[first] + Decimal("0.01")

    transfer = TransferPage(page)
    outcome = transfer.transfer(str(too_much), from_account=first, to_account=second)

    assert outcome != "result", (
        f"Transfer of {too_much} was completed although the balance is only {before[first]}. "
        f"Balances after: {balances(page)}")
    assert balances(page) == before, "Balances changed although the transfer should be refused"
