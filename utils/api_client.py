"""Small helper for the ParaBank REST API, built on Playwright's APIRequestContext.

Every method returns the raw APIResponse, so each test checks the status and
body itself. Paths come from ParaBank's OpenAPI file (services/bank/openapi.yaml).
ParaBank has no DELETE endpoint, so there is no delete method here.

Endpoints that change the shared public site for everyone (cleanDB,
initializeDB, setParameter, shutdown/startupJmsListener) are never used.
"""
import json
import allure
import pytest
from playwright.sync_api import APIRequestContext, APIResponse
from config.settings import API_BASE_PATH

JSON = {"Accept": "application/json"}
ACCOUNT_TYPES = {"CHECKING": 0, "SAVINGS": 1}   # values ParaBank expects for newAccountType


class ParaBankApi:
    def __init__(self, request: APIRequestContext):
        self.request = request

    def _url(self, path: str) -> str:
        return f"{API_BASE_PATH}/{path}"

    @staticmethod
    def _checked(response: APIResponse) -> APIResponse:
        """Attach the server's answer to the Allure report, and skip the test if
        Cloudflare, not ParaBank, answered the request."""
        body = response.text()
        try:
            shown = json.dumps(json.loads(body), indent=2)
        except ValueError:
            shown = body
        endpoint = response.url.split("/services/bank/")[-1]
        allure.attach(f"HTTP {response.status}  {response.url}\n\n{shown}",
                      f"Response {response.status}: {endpoint}", allure.attachment_type.TEXT)
        if response.status == 403 and "cloudflare" in body.lower():
            pytest.skip("Blocked by Cloudflare (HTTP 403): the request never reached ParaBank.")
        return response

    # ---------- Read ----------
    def login(self, username: str, password: str) -> APIResponse:
        return self._checked(self.request.get(self._url(f"login/{username}/{password}"), headers=JSON))

    def customer(self, customer_id: int) -> APIResponse:
        return self._checked(self.request.get(self._url(f"customers/{customer_id}"), headers=JSON))

    def customer_accounts(self, customer_id: int) -> APIResponse:
        return self._checked(self.request.get(self._url(f"customers/{customer_id}/accounts"), headers=JSON))

    def account(self, account_id: int) -> APIResponse:
        return self._checked(self.request.get(self._url(f"accounts/{account_id}"), headers=JSON))

    # ---------- Create ----------
    def create_account(self, customer_id: int, account_type: str, from_account_id: int) -> APIResponse:
        return self._checked(self.request.post(
            self._url("createAccount"),
            params={"customerId": customer_id,
                    "newAccountType": ACCOUNT_TYPES[account_type],
                    "fromAccountId": from_account_id},
            headers=JSON))

    # ---------- Update ----------
    def update_customer(self, customer_id: int, user, **changes) -> APIResponse:
        """Sends the full profile of `user`, with `changes` applied (e.g. city="New City")."""
        fields = {
            "firstName": user.first_name, "lastName": user.last_name,
            "street": user.street, "city": user.city, "state": user.state,
            "zipCode": user.zip_code, "phoneNumber": user.phone, "ssn": user.ssn,
            "username": user.username, "password": user.password,
        }
        fields.update(changes)
        return self._checked(self.request.post(self._url(f"customers/update/{customer_id}"),
                                               params=fields, headers=JSON))
