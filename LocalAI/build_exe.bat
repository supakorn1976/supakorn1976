@echo off
rem Build LocalAI.exe with PyInstaller (run this on Windows with Python 3.9+ installed)
chcp 65001 >nul
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python not found. Install it from https://www.python.org/downloads/
    echo         and tick "Add python.exe to PATH" during setup.
    pause
    exit /b 1
)

echo Installing / updating PyInstaller...
python -m pip install --upgrade pyinstaller || goto :fail

echo Building LocalAI.exe ...
python -m PyInstaller --noconfirm --clean --onefile --windowed --name LocalAI LocalAI.py || goto :fail

echo.
echo Done:  %~dp0dist\LocalAI.exe
pause
exit /b 0

:fail
echo.
echo [ERROR] Build failed - see the messages above.
pause
exit /b 1
