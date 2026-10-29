"""API - CRUD tests on the ParaBank REST API (services/bank).

ParaBank's OpenAPI file lists 27 endpoints and none uses the DELETE method,
so Delete cannot be tested. The four tests are Create, Read, Read of a missing
account (200 vs 4xx), and Update. Each test uses a freshly registered customer
and a request context without a browser and without login cookies.

Expected balances come from the site's current Admin settings (read-only),
because the shared public site's settings can be changed by anyone.
"""
from decimal import Decimal
import pytest
from utils.data_factory import fake

pytestmark = pytest.mark.api


def customer_id_of(api, user) -> int:
    r = api.login(user.username, user.password)
    assert r.status == 200, f"Login API failed with {r.status}: {r.text()[:200]}"
    return r.json()["id"]


def money(value) -> Decimal:
    return Decimal(str(value))


def test_API_01_create_account(api, api_user, balance_settings):
    """Create: POST /createAccount opens a SAVINGS account funded with the
    minimum deposit, which moves from the source account."""
    cid = customer_id_of(api, api_user)
    first = api.customer_accounts(cid).json()[0]
    deposit = balance_settings["minimum_balance"]

    r = api.create_account(cid, "SAVINGS", from_account_id=first["id"])

    assert r.status == 200, f"Expected 200, got {r.status}: {r.text()[:200]}"
    new = r.json()
    assert new["customerId"] == cid
    assert new["type"] == "SAVINGS"
    assert new["id"] != first["id"]
    listed = [a["id"] for a in api.customer_accounts(cid).json()]
    assert new["id"] in listed, "The new account is not listed for the customer"
    # Read both accounts again instead of trusting the create response
    new_balance = money(api.account(new["id"]).json()["balance"])
    first_balance = money(api.account(first["id"]).json()["balance"])
    assert new_balance == deposit, (
        f"New account holds {new_balance}, expected the minimum deposit {deposit}. "
        f"(Balance in the create response was {new['balance']}.)")
    assert first_balance == money(first["balance"]) - deposit, (
        f"Source account went from {first['balance']} to {first_balance}, expected a decrease of {deposit}")


def test_API_02_read_existing_account(api, api_user, balance_settings):
    """Read: GET /accounts/{id} returns 200 and the correct details."""
    cid = customer_id_of(api, api_user)
    first_id = api.customer_accounts(cid).json()[0]["id"]

    r = api.account(first_id)

    assert r.status == 200, f"Expected 200, got {r.status}: {r.text()[:200]}"
    account = r.json()
    assert account["id"] == first_id
    assert account["customerId"] == cid
    assert account["type"] == "CHECKING"
    assert money(account["balance"]) == balance_settings["initial_balance"], (
        f"Balance {account['balance']}, expected the current Init. Balance {balance_settings['initial_balance']}")


def test_API_03_read_missing_account(api):
    """Read (missing): GET /accounts/{id} for an id that does not exist returns a
    client error (4xx), not 200 and not a server error (5xx)."""
    r = api.account(999999999)

    assert 400 <= r.status < 500, f"Expected a 4xx client error, got {r.status}: {r.text()[:200]}"


def test_API_04_update_customer_address(api, api_user):
    """Update: POST /customers/update/{id} changes the address, and GET shows the change."""
    cid = customer_id_of(api, api_user)
    new_street, new_city = fake.street_address(), fake.city()

    r = api.update_customer(cid, api_user, street=new_street, city=new_city)

    assert r.status == 200, f"Expected 200, got {r.status}: {r.text()[:200]}"
    address = api.customer(cid).json()["address"]
    assert address["street"] == new_street
    assert address["city"] == new_city
