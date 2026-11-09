@echo off
setlocal
set "ROOT=%~dp0"
set "FDCTL_CMD=%ROOT%fdctl.cmd"

title Forensics Suite GUI
chcp 65001>nul

if not exist "%FDCTL_CMD%" (
    echo [launch-gui] Khong tim thay tap tin: "%FDCTL_CMD%"
    pause
    exit /b 1
)

cd /d "%ROOT%"
call "%FDCTL_CMD%" --gui %*
endlocal
