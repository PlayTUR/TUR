@echo off
REM Build script for TUR (Windows)

echo === Building TUR ===

REM Check for pyinstaller
where pyinstaller >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

REM Clean previous builds
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul

REM Build
echo Compiling...
pyinstaller TUR.spec

echo.
echo === Build Complete ===
echo Executable: dist\TUR.exe
echo.
echo NOTE: Users will need yt-dlp for song downloads:
echo   pip install yt-dlp
pause
