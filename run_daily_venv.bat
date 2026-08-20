@echo off
setlocal

set "APP_DIR=%~dp0"
set "APP_DIR=%APP_DIR:~0,-1%"
set "VENV_DIR=%APP_DIR%\.venv"
set "MAIN_SCRIPT=%APP_DIR%\frontend\main.py"
set "PYTHON_EXE=%VENV_DIR%\Scripts\python.exe"

echo ============================================================
echo    Automation Studio - Run
echo ============================================================
echo.

:: Check if venv exists and is valid
if exist "%PYTHON_EXE%" (
    "%PYTHON_EXE%" --version >nul 2>&1
    if not errorlevel 1 (
        echo [OK] Using virtual environment: %VENV_DIR%
        goto :run_app
    )
    echo [WARNING] Virtual environment rusak atau tidak valid.
    echo [INFO] Jalankan run_first.bat untuk memperbaiki.
    pause
    exit /b 1
)

echo [ERROR] Virtual environment belum ada.
echo [INFO] Jalankan run_first.bat terlebih dahulu untuk setup.
pause
exit /b 1

:run_app
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
