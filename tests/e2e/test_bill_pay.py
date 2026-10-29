"""E2E - Bill Pay (1 positive, 2 negative). Each test starts with a fresh,
logged-in customer with one account (observed balance 515.50 USD)."""
from decimal import Decimal
import pytest
from playwright.sync_api import Page, expect
from pages.bill_pay_page import BillPayPage
from pages.accounts_overview_page import AccountsOverviewPage
from utils.data_factory import fake
from utils.data_loader import load_json

pytestmark = pytest.mark.e2e


def payee(amount: str, account: str = "12345", verify: str | None = None) -> dict:
    """Valid fake payee details; verify defaults to the same account number."""
    return {
        "payee_name": fake.name(), "street": fake.street_address(), "city": fake.city(),
        "state": fake.state_abbr(), "zip_code": fake.numerify("#####"),
        "phone": fake.numerify("##########"), "account": account,
        "verify_account": account if verify is None else verify, "amount": amount,
    }


def balance(page: Page) -> Decimal:
    return AccountsOverviewPage(page).open().accounts()[0]["balance"]


def test_E2E_BIL_01_pay_bill_with_valid_details(page: Page, logged_in_user):
    """Positive: a 25.00 payment completes and the balance drops by 25.00."""
    before = balance(page)
    details = payee("25.00")

    bill_pay = BillPayPage(page).open()
    bill_pay.fill_form(details)
    outcome = bill_pay.submit()

    assert outcome == "result", f"Payment did not complete. Page shows: {bill_pay.page_text()!r}"
    expect(bill_pay.result_panel).to_contain_text("Bill Payment Complete")
    expect(bill_pay.result_panel).to_contain_text(details["payee_name"])
    expect(bill_pay.result_panel).to_contain_text("$25.00")
    assert balance(page) == before - Decimal("25.00")


def test_E2E_BIL_02_pay_bill_with_all_fields_empty(page: Page, logged_in_user):
    """Negative: an empty form shows the required-field messages and pays nothing."""
    before = balance(page)

    bill_pay = BillPayPage(page).open()
    outcome = bill_pay.submit()

    assert outcome == "validation", f"Expected field errors. Page shows: {bill_pay.page_text()!r}"
    expected = [row["expected_error"] for row in load_json("billpay_required_fields.json")]
    assert bill_pay.visible_error_texts() == expected
    assert balance(page) == before, "Balance changed although the form was empty"


def test_E2E_BIL_03_account_and_verify_account_do_not_match(page: Page, logged_in_user):
    """Negative: different Account # and Verify Account # must be refused."""
    before = balance(page)

    bill_pay = BillPayPage(page).open()
    bill_pay.fill_form(payee("25.00", account="12345", verify="54321"))
    outcome = bill_pay.submit()

    assert outcome == "validation", f"Expected a mismatch error. Page shows: {bill_pay.page_text()!r}"
    expect(bill_pay.verify_account_mismatch_error).to_be_visible()
    assert balance(page) == before, "Balance changed although the account numbers did not match"
