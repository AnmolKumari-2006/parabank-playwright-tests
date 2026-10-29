@echo off
REM Run 1: all tests against the ORIGINAL ParaBank (it must be running on http://localhost:8080/parabank/).
call venv\Scripts\activate
pytest -v --tb=no -rfs
call npx allure generate allure-results --clean -o allure-report-normal
echo.
echo Reports: reports\test_suite_report.html  and  allure-report-normal\index.html
pause
