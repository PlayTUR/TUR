#!/bin/bash
# Cross-compile TUR for Windows using Docker
# Requires: docker

IMAGE="cdrx/pyinstaller-windows:python3"

echo "=== Building TUR for Windows (Docker) ==="

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo "Error: Docker not found. Please install Docker."
    exit 1
fi

# Clean previous build artifacts
rm -rf build dist/TUR-Windows

# Run Docker Build
# We install deps and run pyinstaller inside the container
echo "Starting container..."
docker run --rm -v "$(pwd):/src" \
    --entrypoint /bin/sh \
    $IMAGE -c "python -m pip install --upgrade pip && pip install -r requirements.txt && pyinstaller --clean --noconfirm TUR.spec"

if [ $? -ne 0 ]; then
    echo "Build failed!"
    exit 1
fi

echo ""
echo "=== Post-Build Cleanup ==="

# Rename dist/TUR to dist/TUR-Windows to separate from Linux build
if [ -d "dist/TUR" ]; then
    if [ -d "dist/TUR-Windows" ]; then
        rm -rf "dist/TUR-Windows"
    fi
    mv "dist/TUR" "dist/TUR-Windows"
    echo "Moved build to dist/TUR-Windows"
else
    echo "Error: dist/TUR not found after build!"
    exit 1
fi

# Asset Extraction (Same logic as build.sh)
TARGET_DIR="dist/TUR-Windows"
echo "Extracting assets from _internal..."

move_asset() {
    if [ -d "$TARGET_DIR/_internal/$1" ]; then
        echo "  Moving $1..."
        if [ -d "$TARGET_DIR/$1" ]; then
            rm -rf "$TARGET_DIR/$1"
        fi
        mv "$TARGET_DIR/_internal/$1" "$TARGET_DIR/"
    fi
}

move_asset "songs"
move_asset "story_music"
move_asset "mainmenu_music"
move_asset "themes"
move_asset "sfx"

# Create a zip for convenience
echo "Creating ZIP archive..."
cd dist
if command -v zip &> /dev/null; then
    rm -f TUR-Windows.zip
    zip -r TUR-Windows.zip TUR-Windows > /dev/null
    echo "Created: dist/TUR-Windows.zip"
else
    echo "Warning: 'zip' not found, skipping archive"
fi
cd ..

echo ""
echo "=== Windows Build Complete ==="
echo "Folder:  dist/TUR-Windows/"
echo "Archive: dist/TUR-Windows.zip"
echo ""
