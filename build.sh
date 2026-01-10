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

# Rename to specific OS build
if [ -d "dist/TUR" ]; then
    rm -rf dist/TUR-Linux
    mv dist/TUR dist/TUR-Linux
fi

echo ""
echo "=== Post-Build Cleanup ==="
echo "Extracting assets from _internal..."

# Helper function to move folders out of internal
move_asset() {
    if [ -d "dist/TUR-Linux/_internal/$1" ]; then
        echo "  Moving $1..."
        if [ -d "dist/TUR-Linux/$1" ]; then
            # If destination exists (empty stub), remove it first
            rm -rf "dist/TUR-Linux/$1"
        fi
        mv "dist/TUR-Linux/_internal/$1" "dist/TUR-Linux/"
    else
        echo "  Warning: $1 not found in _internal"
    fi
}

move_asset "songs"
move_asset "story_music"
move_asset "mainmenu_music"
move_asset "themes"
move_asset "sfx"

echo "=== Build Complete ==="
echo "Executable: dist/TUR-Linux/TUR"
echo "Game Root:  dist/TUR-Linux/"
echo ""

# Create ZIP archive
echo "=== Creating ZIP Archive ==="
cd dist
if command -v zip &> /dev/null; then
    rm -f TUR-Linux.zip
    zip -r TUR-Linux.zip TUR-Linux
    echo "Created: dist/TUR-Linux.zip"
else
    echo "Warning: 'zip' command not found, skipping archive creation"
fi
cd ..

echo ""
echo "NOTE: Users will need yt-dlp for song downloads:"
echo "  pip install yt-dlp"
