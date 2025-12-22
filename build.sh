#!/bin/bash
# Build script for TUR

echo "=== Building TUR ==="

# Check for pyinstaller
if ! command -v pyinstaller &> /dev/null; then
    echo "Installing PyInstaller..."
    pip install pyinstaller
fi

# Clean previous builds
rm -rf build dist

# Build
echo "Compiling..."
pyinstaller TUR.spec

echo ""
echo "=== Build Complete ==="
echo "Executable: dist/TUR"
echo ""
echo "NOTE: Users will need yt-dlp for song downloads:"
echo "  pip install yt-dlp"
