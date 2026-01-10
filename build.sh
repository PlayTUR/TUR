#!/bin/bash
# Build script for TUR

echo "=== Building TUR ==="

# Check for venv
if [ -d "venv" ]; then
    echo "Using virtual environment..."
    source venv/bin/activate
fi

# Check for pyinstaller
if ! command -v pyinstaller &> /dev/null; then
    echo "Error: PyInstaller not found!"
    echo "Please install it via: pip install pyinstaller"
    echo "Or create a venv and install dependencies there."
    exit 1
fi

# Clean previous builds
rm -rf build dist

# Build
echo "Compiling..."
pyinstaller TUR.spec

echo ""
echo "=== Post-Build Cleanup ==="
echo "Extracting assets from _internal..."

# Helper function to move folders out of internal
move_asset() {
    if [ -d "dist/TUR/internal/$1" ]; then
        echo "  Moving $1..."
        if [ -d "dist/TUR/$1" ]; then
            # If destination exists (empty stub), remove it first
            rm -rf "dist/TUR/$1"
        fi
        mv "dist/TUR/internal/$1" "dist/TUR/"
    else
        echo "  Warning: $1 not found in internal"
    fi
}

move_asset "songs"
move_asset "story_music"
move_asset "mainmenu_music"
move_asset "themes"
move_asset "sfx"

echo "=== Build Complete ==="
echo "Executable: dist/TUR/TUR"
echo "Game Root:  dist/TUR/"
echo ""
echo "NOTE: Users will need yt-dlp for song downloads:"
echo "  pip install yt-dlp"
