@echo off
REM Build script for TUR (Windows)

echo === Building TUR ===

REM Check for venv
if exist venv\Scripts\activate.bat (
    echo Using virtual environment...
    call venv\Scripts\activate.bat
)

REM Check for pyinstaller
where pyinstaller >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Error: PyInstaller not found!
    echo Please install it via: pip install pyinstaller
    echo Or create a venv and install dependencies there.
    pause
    exit /b 1
)

REM Clean previous builds
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul

REM Build
echo Compiling...
pyinstaller TUR.spec

echo.
echo === Build Complete ===
echo Executable: dist\TUR\TUR.exe
echo.
echo NOTE: Users will need yt-dlp for song downloads:
echo   pip install yt-dlp
pause
