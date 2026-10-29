"""Network mocking - Accounts Overview loads the customer's accounts with a
background request (observed: GET .../services_proxy/bank/customers/{id}/accounts).
These tests replace that server answer with fake data and check that the page
does not break. Each test also proves that the mock was really used."""
import json
import re
import pytest
from playwright.sync_api import Page, Route, expect
from pages.accounts_overview_page import AccountsOverviewPage

pytestmark = pytest.mark.mocking

ACCOUNTS_REQUEST = "**/bank/customers/*/accounts"


def mock_accounts(page: Page, status: int, body: str) -> list[str]:
    """Answer the accounts request with the given fake response; returns the list
    of intercepted URLs so a test can prove the mock was hit."""
    hits: list[str] = []

    def fake_response(route: Route):
        hits.append(route.request.url)
        route.fulfill(status=status, content_type="application/json", body=body)

    page.route(ACCOUNTS_REQUEST, fake_response)
    return hits


def test_MOCK_01_accounts_overview_with_empty_account_list(page: Page, logged_in_user, page_errors):
    """Server returns an empty list: the page stays usable and shows no accounts."""
    hits = mock_accounts(page, 200, json.dumps([]))

    page.goto(AccountsOverviewPage.URL)
    page.wait_for_load_state("networkidle")
    overview = AccountsOverviewPage(page)

    assert hits, "The accounts request was not intercepted, so the mock was not used"
    expect(overview.right_panel).to_contain_text("Accounts Overview", use_inner_text=True)
    expect(overview.account_services_heading).to_be_visible()
    assert overview.account_links.count() == 0, "Accounts were shown although the server returned none"
    assert page_errors == [], f"Uncaught JavaScript errors: {page_errors}"


def test_MOCK_02_accounts_overview_when_server_returns_error(page: Page, logged_in_user, page_errors):
    """Server returns HTTP 500: the page stays usable and tells the user something went wrong."""
    hits = mock_accounts(page, 500, json.dumps({"error": "Internal Server Error"}))

    page.goto(AccountsOverviewPage.URL)
    page.wait_for_load_state("networkidle")
    overview = AccountsOverviewPage(page)

    assert hits, "The accounts request was not intercepted, so the mock was not used"
    expect(overview.account_services_heading).to_be_visible()
    assert page_errors == [], f"Uncaught JavaScript errors: {page_errors}"
    visible_error = overview.right_panel.get_by_text(re.compile("error", re.I)).locator("visible=true")
    assert visible_error.count() > 0, (
        "No error message is visible to the user after the server error. "
        f"Page shows: {overview.page_text()!r}")
