@echo off
setlocal
set "ROOT=%~dp0"
set "BUNDLED_EXE=%ROOT%fdctl_runtime\fdctl_runtime.exe"
if not exist "%BUNDLED_EXE%" set "BUNDLED_EXE=%ROOT%dist\FORENSICS_DISCORD\fdctl_runtime\fdctl_runtime.exe"
if not exist "%BUNDLED_EXE%" set "BUNDLED_EXE=%ROOT%build\pyinstaller\release-dist\fdctl_runtime\fdctl_runtime.exe"
set "USE_SOURCE=0"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

if /I "%~1"=="menu" (
    title FORENSICS_DISCORD Investigator
    chcp 65001>nul
    cls
)

if exist "%ROOT%backend\src" (
    set "PYTHONPATH=%ROOT%backend\src;%PYTHONPATH%"
    set "USE_SOURCE=1"
)

if "%USE_SOURCE%"=="0" if exist "%BUNDLED_EXE%" (
    "%BUNDLED_EXE%" %*
    if /I "%~1"=="menu" exit /b 0
    exit /b %errorlevel%
)

set "PYTHON_EXE=%ROOT%.venv\Scripts\python.exe"
if exist "%PYTHON_EXE%" (
    "%PYTHON_EXE%" -V >nul 2>&1
    if errorlevel 1 set "PYTHON_EXE="
)
if defined PYTHON_EXE (
    "%PYTHON_EXE%" -m fdctl %*
) else (
    python -m fdctl %*
)

if /I "%~1"=="menu" exit /b 0

endlocal
