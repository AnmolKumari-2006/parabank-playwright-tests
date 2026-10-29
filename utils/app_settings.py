"""Reads ParaBank's current Application Settings from the Admin Page (READ ONLY).

The public site is shared, and anyone can change these settings. Observed during
this project: Init. Balance changed from 515.50 to 500. Tests therefore read the
values at run time instead of using fixed numbers. Nothing on the page is clicked
or submitted; the page is only downloaded and two input values are read.
"""
import re
from decimal import Decimal
from playwright.sync_api import APIRequestContext


def read_balance_settings(request: APIRequestContext) -> dict[str, Decimal]:
    html = request.get("admin.htm").text()
    values = {}
    for key, input_id in (("initial_balance", "initialBalance"), ("minimum_balance", "minimumBalance")):
        match = re.search(rf'id="{input_id}"[^>]*value="([^"]*)"', html) or \
                re.search(rf'value="([^"]*)"[^>]*id="{input_id}"', html)
        assert match, f"Could not read {input_id} from the Admin Page"
        values[key] = Decimal(match.group(1))
    return values
