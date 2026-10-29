@echo off
REM Run 2: all tests against the ParaBank build WITH the deliberate bug (it must be running on http://localhost:8080/parabank/).
call venv\Scripts\activate
pytest -v --tb=no -rfs --bug-build
call npx allure generate allure-results --clean -o allure-report-bug-build
echo.
echo Reports: reports\test_suite_report_bug_build.html  and  allure-report-bug-build\index.html
pause