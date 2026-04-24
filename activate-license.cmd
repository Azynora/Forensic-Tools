@echo off
setlocal
set "ROOT=%~dp0"
set "FDCTL_CMD=%ROOT%fdctl.cmd"

if not exist "%FDCTL_CMD%" (
    echo [activate-license] Missing launcher: "%FDCTL_CMD%"
    exit /b 1
)

chcp 65001>nul
title FORENSICS_DISCORD License Activation
echo [FORENSICS_DISCORD] Official bundle activation
echo [FORENSICS_DISCORD] Paste the key issued by Truong Trieu Vy when prompted.
echo.
call "%FDCTL_CMD%" license activate --prompt
echo.
pause
endlocal
