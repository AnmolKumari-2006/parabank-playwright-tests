"""Shared pytest fixtures and hooks for the whole project."""
import time
from pathlib import Path
from typing import Iterator
import allure
import pytest
from playwright.sync_api import Page, Playwright, Browser, APIRequestContext
from utils.data_factory import new_user, User
from utils.api_client import ParaBankApi
from utils.app_settings import read_balance_settings
from pages.register_page import RegisterPage
from pages.accounts_overview_page import AccountsOverviewPage
from pages.open_account_page import OpenAccountPage


# ================================================================ command-line options
def pytest_addoption(parser):
    parser.addoption(
        "--bug-build", action="store_true",
        help="Label this run as a run against the ParaBank build with the deliberate bug "
             "(Bill Pay does not deduct the amount from the account). Reports and files are kept separate.")
    parser.addoption(
        "--demo", action="store_true",
        help="Run all tests of a browser in ONE window, for watching or a live demo. "
             "Cookies are cleared before every test so tests stay independent. "
             "Video and trace files are not recorded in this mode.")


DEMO_ZOOM = 0.7   # page size in --demo mode, so a whole form fits on screen


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args, pytestconfig, browser_name):
    """With --demo, the browser itself draws pages at DEMO_ZOOM (70%) from the start.
    This is set before any test runs, so Playwright knows the real position of every
    button. (Zooming by hand during a run moves the buttons and makes clicks miss.)

    Only Chromium has a safe switch for this (maximized window + device scale
    factor); Firefox and WebKit stay at 100%.
    Normal runs (without --demo) are never changed.
    """
    if not pytestconfig.getoption("--demo"):
        return browser_type_launch_args
    if browser_name == "chromium":
        args = list(browser_type_launch_args.get("args", [])) + [
            "--start-maximized", f"--force-device-scale-factor={DEMO_ZOOM}"]
        return {**browser_type_launch_args, "args": args}
    return browser_type_launch_args


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Same window size for every test, so screenshots are comparable."""
    return {**browser_context_args, "viewport": {"width": 1366, "height": 768}}


@pytest.fixture(scope="session")
def _demo_page(browser, browser_context_args):
    """One window shared by every test of this browser, used only with --demo."""
    if browser.browser_type.name == "chromium":
        demo_args = {k: v for k, v in browser_context_args.items() if k != "viewport"}
        context = browser.new_context(**demo_args, no_viewport=True)
    else:
        context = browser.new_context(**browser_context_args)
    shared = context.new_page()
    yield shared
    context.close()


@pytest.fixture
def page(request, pytestconfig):
    """Normal run: a new window per test (pytest-playwright's default behaviour).
    With --demo: the same window for all tests, reset before each test."""
    if pytestconfig.getoption("--demo"):
        shared = request.getfixturevalue("_demo_page")
        shared.context.clear_cookies()      # logs out, so no test inherits another test's session
        shared.unroute_all()                # removes network mocks left by an earlier test
        shared.goto("about:blank")
        new_page = shared
    else:
        new_page = request.getfixturevalue("context").new_page()
    yield new_page


# ================================================================ UI test data and states
def registration_failed(register: RegisterPage) -> str:
    """Evidence for a fixture whose registration did not log the user in."""
    return (f"Fixture could not register a fresh user. HTTP status: {register.last_status}. "
            f"Field errors: {register.visible_errors()}. Page shows: {register.page_text()!r}")


@pytest.fixture
def user_data() -> User:
    """A new, unique, NOT yet registered user for one test."""
    return new_user()


@pytest.fixture
def registered_user(page: Page) -> User:
    """Registers a fresh user through the UI and logs out again."""
    user = new_user()
    register = RegisterPage(page)
    register.register(user)
    assert register.is_logged_in(), registration_failed(register)
    register.logout()
    return user


@pytest.fixture
def logged_in_user(page: Page) -> User:
    """Registers a fresh user; the page stays logged in.
    The new customer has one CHECKING account with the site's Init. Balance."""
    user = new_user()
    register = RegisterPage(page)
    register.register(user)
    assert register.is_logged_in(), registration_failed(register)
    return user


@pytest.fixture
def two_accounts(page: Page, logged_in_user: User) -> dict:
    """Fresh logged-in user with a second CHECKING account.
    Balances depend on the site's current Admin settings, so tests compare
    before/after values instead of fixed numbers."""
    first = AccountsOverviewPage(page).open().accounts()[0]["number"]
    second = OpenAccountPage(page).open().open_new_account("CHECKING", from_account=first)
    return {"user": logged_in_user, "first": first, "second": second}


@pytest.fixture
def page_errors(page: Page) -> Iterator[list[str]]:
    """Collects uncaught JavaScript errors on the page (used by the mocking tests)."""
    errors: list[str] = []

    def handle(error):
        errors.append(str(error))

    page.on("pageerror", handle)
    yield errors
    page.remove_listener("pageerror", handle)


# ================================================================ API tests (no browser per test)
@pytest.fixture(scope="session")
def _api_browser(playwright: Playwright) -> Iterator[Browser]:
    """One headless Chromium, used only to register users for the API tests
    (ParaBank has no register endpoint). API tests themselves use no browser."""
    browser = playwright.chromium.launch()
    yield browser
    browser.close()


@pytest.fixture
def api_user(_api_browser: Browser, base_url: str) -> User:
    """A fresh customer registered through the UI, for one API test."""
    user = new_user()
    context = _api_browser.new_context(base_url=base_url)
    try:
        page = context.new_page()
        register = RegisterPage(page)
        register.register(user)
        assert register.is_logged_in(), registration_failed(register)
    finally:
        context.close()
    return user


@pytest.fixture
def api_request(playwright: Playwright, base_url: str) -> Iterator[APIRequestContext]:
    """HTTP client with no browser and no login cookies."""
    request = playwright.request.new_context(base_url=base_url)
    yield request
    request.dispose()


@pytest.fixture
def api(api_request: APIRequestContext) -> ParaBankApi:
    """ParaBank REST API client."""
    return ParaBankApi(api_request)


@pytest.fixture
def balance_settings(api_request: APIRequestContext) -> dict:
    """Current Init. Balance and Min. Balance, read from the Admin Page right before the test."""
    return read_balance_settings(api_request)


# ================================================================ deliberate bug in the ParaBank code
# For the requirement "add one bug to your site on purpose and show the test failing".
# The bug is introduced in ParaBank's own Java code (BillPayController: the payment is
# reported as successful but the amount is never withdrawn, so the balance does not change),
# the app is rebuilt and run locally, and the tests are run against it with --bug-build. That option does not
# change any test; it only labels this run and keeps its report and files separate.

# ================================================================ Allure report
FEATURES = {"REG": "Register", "LOG": "Login", "TRF": "Transfer Funds", "BIL": "Bill Pay",
            "API": "REST API", "MOCK": "Network Mocking"}


def describe_test(item) -> dict:
    """Test ID, feature, kind, browser and description, taken from the test name
    (e.g. test_E2E_TRF_02_...) and its docstring."""
    name = item.originalname or item.name
    parts = name.split("_")                      # ['test', 'E2E', 'TRF', '02', ...]
    if parts[1] in ("API", "MOCK"):
        test_id, feature = f"{parts[1]}_{parts[2]}", FEATURES[parts[1]]
    else:
        test_id, feature = "_".join(parts[1:4]), FEATURES.get(parts[2], parts[2])
    first = " ".join((item.function.__doc__ or "").split())
    kind, _, text = first.partition(":")
    if not text or parts[1] == "MOCK":            # no "Kind:" prefix (mocking docstrings)
        kind, text = ("Mocking" if parts[1] == "MOCK" else ""), first
    text = text.strip()
    params = getattr(item, "callspec", None)
    browser = params.params.get("browser_name", "") if params else ""
    data_set = "-".join(p for p in (params.id.split("-") if params else [])
                        if p not in ("chromium", "firefox", "webkit"))
    return {"id": test_id + (f" [{data_set}]" if data_set else ""), "feature": feature,
            "kind": kind.strip(), "browser": browser, "description": text[:1].upper() + text[1:]}


BROWSER_NAMES = {"chromium": "Chromium", "firefox": "Firefox", "webkit": "WebKit"}


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    """Organises the Allure report:
    Suites tab:    browser > feature > Positive / Negative / ... > test
    Behaviors tab: feature > testing type > test
    and gives every test a readable title."""
    info = describe_test(item)
    browser = BROWSER_NAMES.get(info["browser"], "API (no browser)")
    shown = f" ({info['browser']})" if info["browser"] else ""
    allure.dynamic.title(f"{info['id']}{shown}: {info['description']}")
    allure.dynamic.parent_suite(browser)
    allure.dynamic.suite(info["feature"])
    allure.dynamic.sub_suite(info["kind"] or "Other")
    allure.dynamic.feature(info["feature"])
    allure.dynamic.story(info["kind"] or "Other")
    allure.dynamic.tag(info["browser"] or "API")
    yield


_RESULTS: dict[str, dict] = {}
_BROWSER_VERSIONS: dict[str, str] = {}
_START = time.time()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Records each test's real outcome for the test suite report. No screenshots
    are put in the report (Playwright saves failure screenshots as files in
    test-results/). The test result is never changed."""
    outcome = yield
    report = outcome.get_result()
    entry = _RESULTS.setdefault(item.nodeid, {
        **describe_test(item), "outcome": "passed", "message": "", "start": call.start, "duration": 0.0,
        "path": f"{Path(item.fspath).parent.name}/{item.originalname or item.name}"})
    entry["duration"] += report.duration
    page = item.funcargs.get("page")
    if page is not None and report.when == "setup":
        try:                                      # real browser version, shown in the report header
            _BROWSER_VERSIONS[entry["browser"]] = page.context.browser.version
        except Exception:
            pass
    if report.when == "call":
        entry["outcome"] = report.outcome
        if report.failed or report.skipped:
            entry["message"] = first_line(report)
    elif report.failed:                           # setup or teardown problem
        entry["outcome"] = "error"
        entry["message"] = f"{report.when} failed: {first_line(report)}"
    elif report.skipped and report.when == "setup":
        entry["outcome"] = "skipped"
        entry["message"] = first_line(report)


def first_line(report) -> str:
    """The assertion or skip reason as pytest reports it, on one line."""
    if report.skipped and isinstance(report.longrepr, tuple):
        text = str(report.longrepr[2]).removeprefix("Skipped: ")
    else:
        crash = getattr(report.longrepr, "reprcrash", None)
        text = crash.message if crash else str(report.longrepr)
    text = text.split("Call log:")[0]            # drop Playwright's internal call log
    return " ".join(text.split())[:300]


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    """Keeps the files of the bug run apart from the normal run, so both can be submitted:
    failure screenshots/videos/traces go to test-results-bug-build/."""
    if config.getoption("--bug-build"):
        config.option.output = "test-results-bug-build"


def pytest_sessionfinish(session, exitstatus):
    """Writes the Katalon-style test suite report and the Allure environment file.
    Normal run:  reports/test_suite_report.html
    Bug run:     reports/test_suite_report_bug_build.html"""
    config = session.config
    if not _RESULTS or config.getoption("collectonly"):
        return
    injected = config.getoption("--bug-build")
    rows = list(_RESULTS.values())
    out = Path("reports")
    name = "test_suite_report_bug_build.html" if injected else "test_suite_report.html"

    from utils.suite_report import write_suite_report
    suite_page = write_suite_report(rows, {
        "start": _START, "end": time.time(), "base_url": config.getoption("base_url"),
        "browsers": dict(_BROWSER_VERSIONS), "injected": injected}, out / name)

    results_dir = Path(config.getoption("allure_report_dir") or "allure-results")
    if results_dir.exists():
        (results_dir / "environment.properties").write_text(
            f"Site={config.getoption('base_url')}\nBrowsers=Chromium, Firefox, WebKit\n"
            f"TestCases=18 (12 end-to-end, 4 API, 2 network mocking)\n"
            f"BuildWithDeliberateBug={'YES - Bill Pay does not deduct the amount' if injected else 'no'}\n",
            encoding="utf-8")

    terminal = config.pluginmanager.get_plugin("terminalreporter")
    if terminal is not None:
        terminal.write_line(f"Test suite report: {suite_page.resolve()}")
        if injected:
            terminal.write_line("NOTE: run against the ParaBank build with the deliberate Bill Pay bug: E2E_BIL_01 is expected to fail.")