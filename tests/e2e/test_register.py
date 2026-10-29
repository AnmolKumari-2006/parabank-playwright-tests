"""E2E - Register (1 positive, 2 negative)."""
import pytest
from playwright.sync_api import Page, expect
from pages.register_page import RegisterPage
from utils.data_loader import load_json

pytestmark = pytest.mark.e2e


def test_E2E_REG_01_register_with_valid_details(page: Page, user_data):
    """Positive: a new customer can open an online account."""
    register = RegisterPage(page)
    register.register(user_data)

    expect(register.page_title).to_have_text(f"Welcome {user_data.username}")
    expect(register.success_message).to_have_text("Your account was created successfully. You are now logged in.")
    expect(register.account_services_heading).to_be_visible()


def test_E2E_REG_02_register_with_all_fields_empty(page: Page):
    """Negative: an empty form shows a message for every required field."""
    register = RegisterPage(page).open()
    register.submit()

    expected = {row["field"]: row["expected_error"] for row in load_json("register_required_fields.json")}
    assert register.visible_errors() == expected
    assert not register.is_logged_in(), "An account was created from an empty form"


def test_E2E_REG_03_register_with_letters_in_numeric_fields(page: Page, user_data):
    """Negative: letters in ZIP Code, Phone # and SSN must be rejected."""
    user_data.zip_code = user_data.phone = user_data.ssn = "abc"
    register = RegisterPage(page)
    register.register(user_data)

    errors = register.visible_errors()
    missing = {"zip_code", "phone", "ssn"} - errors.keys()
    assert not missing, (
        f"No validation error for: {sorted(missing)}. Account created: {register.is_logged_in()}. "
        f"Page shows: {register.page_text(200)!r}")
    assert not register.is_logged_in(), "An account was created with letters in ZIP Code, Phone # and SSN"
