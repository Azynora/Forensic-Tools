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

set "RUNNER=%TEMP%\fdctl_menu_runner_%RANDOM%%RANDOM%.cmd"
> "%RUNNER%" (
    echo @echo off
    echo setlocal EnableExtensions
    echo cd /d "%ROOT%"
    echo call "%FDCTL_CMD%" menu %%*
    echo set "FDCTL_EXIT=%%ERRORLEVEL%%"
    echo if "%%FDCTL_EXIT%%"=="0" ^(
        echo   echo.
        echo   echo [OK] Investigation workflow completed.
        echo   echo [OK] Terminal report files are stored inside the saved case under workspace\cases\^^<case-id^^>\08_Report
        echo   echo [OK] Open Muc_luc_bao_cao.md or case_snapshot.json in the saved case for the canonical report output.
        echo   echo [OK] No background investigation task is still running in this terminal.
        echo   timeout /t 2 ^>nul
        echo   exit /b 0
        echo ^)
    echo echo.
    echo echo [ERROR] Workflow stopped with exit code %%FDCTL_EXIT%%.
    echo echo [ERROR] This terminal is being kept open so you can review the error output.
    echo pause
    echo exit /b %%FDCTL_EXIT%%
)

start "FORENSICS_DISCORD Terminal" /d "%ROOT%" cmd.exe /c ""%RUNNER%" %*"

exit /b 0
