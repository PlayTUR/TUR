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
echo "=== Build Complete ==="
echo "Executable: dist/TUR/TUR"
echo ""
echo "NOTE: Users will need yt-dlp for song downloads:"
echo "  pip install yt-dlp"
