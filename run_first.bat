@echo off
setlocal enabledelayedexpansion

:: ============================================================
:: Automation Studio - Setup & Run
:: ============================================================

set "APP_DIR=%~dp0"
set "APP_DIR=%APP_DIR:~0,-1%"
set "VENV_DIR=%APP_DIR%\.venv"
set "REQ_FILE=%APP_DIR%\requirements.txt"
set "MAIN_SCRIPT=%APP_DIR%\frontend\main.py"
set "PYTHON_MIN_VERSION=3.10"

echo ============================================================
echo    Automation Studio - Setup ^& Run
echo ============================================================
echo.

:: 1. Check Python
echo [1/4] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python tidak ditemukan.
    echo.
    echo Silakan install Python %PYTHON_MIN_VERSION% atau lebih baru dari:
    echo https://www.python.org/downloads/windows/
    echo.
    echo Catatan: Centang "Add Python to PATH" saat install.
    pause
    exit /b 1
)

:: Get Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VER=%%i
echo [OK] Python ditemukan: %PYTHON_VER%

:: Get Python executable path
for /f "tokens=*" %%i in ('where python') do set PYTHON_EXE_PATH=%%i
echo [OK] Python path: %PYTHON_EXE_PATH%

:: 2. Check/create virtual environment
echo.
echo [2/4] Checking virtual environment...
if exist "%VENV_DIR%\Scripts\python.exe" (
    "%VENV_DIR%\Scripts\python.exe" --version >nul 2>&1
    if not errorlevel 1 (
        echo [OK] Virtual environment sudah ada dan valid.
        goto :activate_venv
    )
    echo [WARNING] Virtual environment rusak, membuat ulang...
    rmdir /s /q "%VENV_DIR%"
)

echo [INFO] Membuat virtual environment baru...
"%PYTHON_EXE_PATH%" -m venv "%VENV_DIR%"
if errorlevel 1 (
    echo [ERROR] Gagal membuat virtual environment.
    pause
    exit /b 1
)
echo [OK] Virtual environment berhasil dibuat.

:activate_venv
set "PYTHON_EXE=%VENV_DIR%\Scripts\python.exe"
if not exist "%PYTHON_EXE%" (
    echo [ERROR] Python executable di venv tidak ditemukan: %PYTHON_EXE%
    pause
    exit /b 1
)

:: 3. Install/update dependencies
echo.
echo [3/4] Checking dependencies...
if not exist "%REQ_FILE%" (
    echo [WARNING] File requirements.txt tidak ditemukan: %REQ_FILE%
    echo [WARNING] Melewati instalasi dependencies.
    goto :run_app
)

echo [INFO] Installing dependencies dari requirements.txt...
echo [INFO] Ini mungkin memakan beberapa menit pada pertama kali...
"%PYTHON_EXE%" -m pip install -r "%REQ_FILE%"
if errorlevel 1 (
    echo [ERROR] Gagal install beberapa dependencies.
    echo Coba jalankan manual:
    echo   "%PYTHON_EXE%" -m pip install -r "%REQ_FILE%"
    pause
    exit /b 1
)
echo [OK] Semua dependencies terinstall.

:: 4. Check Tesseract OCR (optional but recommended)
echo.
echo [4/4] Checking optional dependencies...
where tesseract >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Tesseract OCR tidak ditemukan di PATH.
    echo [WARNING] Fitur OCR/Image Detection mungkin tidak berfungsi.
    echo [INFO] Download Tesseract dari: https://github.com/UB-Mannheim/tesseract/wiki
) else (
    echo [OK] Tesseract OCR ditemukan.
)

:: Optional: Install Playwright browsers
echo.
echo [INFO] Checking Playwright browsers...
"%PYTHON_EXE%" -m playwright install --with-deps chromium 2>nul
if errorlevel 1 (
    echo [WARNING] Gagal install Playwright Chromium browser.
    echo [WARNING] Aplikasi tetap bisa jalan jika menggunakan mode "connect" ke browser sistem.
) else (
    echo [OK] Playwright Chromium browser terinstall.
)

:: ============================================================
:: Run Application
:: ============================================================
:run_app
echo.
echo ============================================================
echo    Starting Automation Studio...
echo ============================================================
echo.

cd /d "%APP_DIR%"
"%PYTHON_EXE%" "%MAIN_SCRIPT%"

set "EXIT_CODE=%ERRORLEVEL%"

echo.
if %EXIT_CODE% neq 0 (
    echo [ERROR] Aplikasi keluar dengan kode error: %EXIT_CODE%
) else (
    echo [OK] Aplikasi ditutup dengan normal.
)

pause
exit /b %EXIT_CODE%
