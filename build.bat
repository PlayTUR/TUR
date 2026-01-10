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
echo === Post-Build Cleanup ===
echo Extracting assets from internal...

if exist "dist\TUR\internal\songs" (
    echo   Moving songs...
    if exist "dist\TUR\songs" rmdir /s /q "dist\TUR\songs"
    move "dist\TUR\internal\songs" "dist\TUR\" >nul
)

if exist "dist\TUR\internal\story_music" (
    echo   Moving story_music...
    if exist "dist\TUR\story_music" rmdir /s /q "dist\TUR\story_music"
    move "dist\TUR\internal\story_music" "dist\TUR\" >nul
)

if exist "dist\TUR\internal\mainmenu_music" (
    echo   Moving mainmenu_music...
    if exist "dist\TUR\mainmenu_music" rmdir /s /q "dist\TUR\mainmenu_music"
    move "dist\TUR\internal\mainmenu_music" "dist\TUR\" >nul
)

if exist "dist\TUR\internal\themes" (
    echo   Moving themes...
    if exist "dist\TUR\themes" rmdir /s /q "dist\TUR\themes"
    move "dist\TUR\internal\themes" "dist\TUR\" >nul
)

if exist "dist\TUR\internal\sfx" (
    echo   Moving sfx...
    if exist "dist\TUR\sfx" rmdir /s /q "dist\TUR\sfx"
    move "dist\TUR\internal\sfx" "dist\TUR\" >nul
)

echo.
echo === Build Complete ===
echo Executable: dist\TUR\TUR.exe
echo Game Root:  dist\TUR\
echo.
echo NOTE: Users will need yt-dlp for song downloads:
echo   pip install yt-dlp
pause
