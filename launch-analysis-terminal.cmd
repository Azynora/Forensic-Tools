@echo off
setlocal EnableExtensions
set "ROOT=%~dp0"
set "FDCTL_CMD=%ROOT%fdctl.cmd"
set "COPYRIGHT_OWNER=Truong Trieu Vy"
set "COPYRIGHT_EMAIL=trieuvy9198@gmail.com"

if not exist "%FDCTL_CMD%" (
    echo [launch-analysis-terminal] Missing launcher: "%FDCTL_CMD%"
    exit /b 1
)

cd /d "%ROOT%"
call "%FDCTL_CMD%" menu %*
set "FDCTL_EXIT=%ERRORLEVEL%"

if "%FDCTL_EXIT%"=="0" (
    echo.
    echo [OK] Investigation workflow completed.
    echo [OK] Terminal report files are stored inside the saved case under workspace\cases\^<case-id^>\08_Report
    echo [OK] Open Muc_luc_bao_cao.md or case_snapshot.json in the saved case for the canonical report output.
    echo [OK] No background investigation task is still running in this terminal.
    exit /b 0
)

echo.
echo [ERROR] Workflow stopped with exit code %FDCTL_EXIT%.
echo [ERROR] This terminal is being kept open so you can review the error output.
pause
exit /b %FDCTL_EXIT%
