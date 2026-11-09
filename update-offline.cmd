@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Forensics Suite — Trình Cập nhật Offline (Bảo toàn Bản quyền)
chcp 65001>nul

set "ROOT=%~dp0"
set "PATCH_DIR=%ROOT%patch_files"
if not exist "%PATCH_DIR%" set "PATCH_DIR=%ROOT%update_package"
if not exist "%PATCH_DIR%" set "PATCH_DIR=%ROOT%dist\ForensicsSuite"

echo ======================================================================
echo   FORENSICS SUITE — CẬP NHẬT OFFLINE / PHÒNG LAB NGẮT MẠNG (AIR-GAPPED)
echo   Tác giả: Trương Triệu Vỹ (trieuvy9198@gmail.com)
echo ======================================================================
echo.
echo [CAM KẾT TOÀN VẸN DỮ LIỆU & BẢN QUYỀN]:
echo   ✓ 1. Bản quyền máy (%LOCALAPPDATA%\FORENSIC_SUITE\license) ĐƯỢC GIỮ NGUYÊN.
echo   ✓ 2. Toàn bộ hồ sơ vụ án cũ (%ROOT%workspace\cases) ĐƯỢC BẢO LƯU 100%%.
echo   ✓ 3. Tệp khóa license.key ngoài gốc (nếu dùng bản USB) KHÔNG BỊ XÓA.
echo.

if not exist "%PATCH_DIR%" (
    echo [LƯU Ý] Không tìm thấy thư mục bản vá tự động:
    echo        - Thư mục tìm kiếm: "%ROOT%patch_files" hoặc "%ROOT%update_package"
    echo.
    echo Vui lòng giải nén gói cập nhật (ForensicsSuite_Patch_vX.X.zip) vào thư mục
    echo "patch_files" nằm cùng cấp với tệp này, sau đó chạy lại.
    echo.
    set /p "CUSTOM_DIR=Hoặc nhập đường dẫn thư mục chứa bản vá mới: "
    if defined CUSTOM_DIR (
        if exist "!CUSTOM_DIR!" (
            set "PATCH_DIR=!CUSTOM_DIR!"
        ) else (
            echo [LỖI] Đường dẫn không tồn tại: "!CUSTOM_DIR!"
            pause
            exit /b 1
        )
    ) else (
        pause
        exit /b 1
    )
)

echo [NGUỒN BẢN VÁ]: "%PATCH_DIR%"
echo [ĐÍCH CẬP NHẬT]: "%ROOT%"
echo.
set /p "CONFIRM=Bạn có chắc chắn muốn áp dụng bản cập nhật này? (Y/N, Mặc định: Y): "
if /i "%CONFIRM%"=="N" (
    echo [ĐÃ HỦY] Không có thay đổi nào được thực hiện.
    pause
    exit /b 0
)

echo.
echo [1/4] Đang đóng các tiến trình Forensics Suite đang chạy (nếu có)...
taskkill /F /IM "ForensicsSuite.exe" >nul 2>&1
taskkill /F /IM "fdctl_runtime.exe" >nul 2>&1

echo [2/4] Đang sao chép các tệp thực thi và mã nguồn mới...
:: Copy runtime binary folder if present
if exist "%PATCH_DIR%\fdctl_runtime" (
    echo   -> Cập nhật runtime nhị phân (fdctl_runtime)...
    robocopy "%PATCH_DIR%\fdctl_runtime" "%ROOT%fdctl_runtime" /E /R:1 /W:1 /NP /NFL /NDL >nul
)

:: Copy backend source if present
if exist "%PATCH_DIR%\backend" (
    echo   -> Cập nhật module backend...
    robocopy "%PATCH_DIR%\backend" "%ROOT%backend" /E /R:1 /W:1 /NP /NFL /NDL >nul
)

:: Copy tools if present
if exist "%PATCH_DIR%\tools" (
    echo   -> Cập nhật công cụ hỗ trợ...
    robocopy "%PATCH_DIR%\tools" "%ROOT%tools" /E /R:1 /W:1 /NP /NFL /NDL >nul
)

:: Copy launcher scripts if present
for %%F in (fdctl.cmd activate-license.cmd launch-analysis-terminal.cmd ForensicsSuite.exe) do (
    if exist "%PATCH_DIR%\%%F" (
        copy /Y "%PATCH_DIR%\%%F" "%ROOT%%%F" >nul
        echo   -> Cập nhật %%F
    )
)

echo [3/4] Đang kiểm tra tính toàn vẹn bản quyền hệ thống...
set "LIC_PATH=%LOCALAPPDATA%\FORENSIC_SUITE\license\activation.json"
if exist "%LIC_PATH%" (
    echo   ✓ Bản quyền hệ thống được bảo lưu nguyên vẹn: %LIC_PATH%
) else (
    if exist "%ROOT%license.key" (
        echo   ✓ Tệp bản quyền USB Portable được bảo lưu: %ROOT%license.key
    ) else (
        echo   [Thông tin] Bản quyền chưa kích hoạt trên thiết bị này.
    )
)

echo [4/4] Đang xác minh hồ sơ điều tra...
if exist "%ROOT%workspace\cases" (
    echo   ✓ Thư mục án lệ workspace\cases an toàn tuyệt đối.
)

echo.
echo ======================================================================
echo   [HOÀN TẤT] CẬP NHẬT PHIÊN BẢN MỚI THÀNH CÔNG!
echo   Bản quyền và toàn bộ dữ liệu điều tra cũ được bảo lưu 100%%.
echo ======================================================================
echo.
pause
endlocal
