"""Page object for the Register page (register.htm)."""
from playwright.sync_api import Page, Locator
from pages.base_page import BasePage
from utils.data_factory import User


class RegisterPage(BasePage):
    URL = "register.htm"

    # Form field ids on ParaBank. Keys match the User fields in utils/data_factory.py
    # and the "field" values in test_data/register_required_fields.json.
    FIELD_IDS = {
        "first_name": "customer.firstName",
        "last_name": "customer.lastName",
        "street": "customer.address.street",
        "city": "customer.address.city",
        "state": "customer.address.state",
        "zip_code": "customer.address.zipCode",
        "phone": "customer.phoneNumber",
        "ssn": "customer.ssn",
        "username": "customer.username",
        "password": "customer.password",
        "confirm": "repeatedPassword",
    }

    def __init__(self, page: Page):
        super().__init__(page)
        self.register_button: Locator = page.locator("input[type='submit'][value='Register']")
        self.success_message: Locator = self.right_panel.locator("p").first

    # ---------- locators ----------
    def field(self, name: str) -> Locator:
        # ids contain dots, so an attribute selector is used instead of "#id"
        return self.page.locator(f"[id='{self.FIELD_IDS[name]}']")

    def error_for(self, name: str) -> Locator:
        # ParaBank shows each field's error in an element with id "<field id>.errors"
        return self.page.locator(f"[id='{self.FIELD_IDS[name]}.errors']")

    # ---------- actions ----------
    def fill_form(self, user: User, confirm: str | None = None, skip: tuple[str, ...] = ()):
        """Fill every field from the user.

        confirm: value for Confirm; defaults to the user's password.
        skip:    field names to leave empty, e.g. ("phone",).
        """
        values = user.as_dict()
        values["confirm"] = user.password if confirm is None else confirm
        for name in self.FIELD_IDS:
            if name not in skip:
                self.field(name).fill(values[name])

    def submit(self):
        # REGISTER posts the form and ParaBank loads a new page with the result.
        # Wait for that navigation, otherwise the old page would be read.
        self.click_and_wait_for_page(self.register_button)

    def register(self, user: User):
        """Open the page, fill in all fields and submit."""
        self.open()
        self.fill_form(user)
        self.submit()

    # ---------- reads ----------
    def visible_errors(self) -> dict[str, str]:
        """Field name -> error text, for every field that shows an error."""
        errors = {}
        for name in self.FIELD_IDS:
            loc = self.error_for(name)
            if loc.count() and loc.is_visible() and loc.inner_text().strip():
                errors[name] = loc.inner_text().strip()
        return errors
