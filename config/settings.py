"""Central project settings.

Balance rules (Init. Balance, Min. Balance) are NOT fixed here: the public site is
shared and they were changed by someone during the project (515.50 -> 500).
They are read from the Admin Page at run time, see utils/app_settings.py.
"""

# REST API base path, relative to the --base-url in pytest.ini
API_BASE_PATH = "services/bank"
