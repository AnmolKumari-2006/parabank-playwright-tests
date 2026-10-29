"""E2E - Login (1 positive, 2 negative). Each test starts with a freshly registered, logged-out user."""
import pytest
from playwright.sync_api import Page, expect
from pages.login_page import LoginPage

pytestmark = pytest.mark.e2e


def test_E2E_LOG_01_login_with_valid_credentials(page: Page, registered_user):
    """Positive: a registered customer can log in."""
    login = LoginPage(page).open()
    login.login(registered_user.username, registered_user.password)

    expect(login.welcome_text).to_have_text(f"Welcome {registered_user.first_name} {registered_user.last_name}")
    expect(login.account_services_heading).to_be_visible()


def test_E2E_LOG_02_login_with_wrong_password(page: Page, registered_user):
    """Negative: a wrong password is rejected."""
    login = LoginPage(page).open()
    login.login(registered_user.username, "Wrong@123")

    expect(login.error_message).to_have_text("The username and password could not be verified.")
    assert not login.is_logged_in(), "Logged in with a wrong password"


def test_E2E_LOG_03_login_with_empty_fields(page: Page):
    """Negative: empty username and password are rejected."""
    login = LoginPage(page).open()
    login.login("", "")

    expect(login.error_message).to_have_text("Please enter a username and password.")
    assert not login.is_logged_in(), "Logged in with empty username and password"
