#!/bin/bash
# TUR Deployment Script - Upload game build to VPS
# Usage: ./deploy.sh

set -e

# Configuration
VPS_USER="${VPS_USER:-root}"
VPS_HOST="154.53.35.148"
VPS_PATH="/root/TURSS/server"
BUILD_DIR="dist"

echo "=== TUR DEPLOYMENT SCRIPT ==="

# Check if build exists
if [ ! -d "$BUILD_DIR" ]; then
    echo "[ERROR] Build directory '$BUILD_DIR' not found!"
    echo "Run 'pyinstaller TUR.spec' first to create the build."
    exit 1
fi

# Create zip of the build
echo "[1/4] Packaging build..."
cd $BUILD_DIR
zip -r TUR-Windows.zip TUR/ -x "*.pyc" -x "__pycache__/*"
cd ..

# Upload to VPS
echo "[2/4] Uploading to VPS..."
scp $BUILD_DIR/TUR-Windows.zip $VPS_USER@$VPS_HOST:$VPS_PATH/static/download/

# Upload server code (optional - uncomment if needed)
# echo "[3/4] Updating server code..."
# scp -r server/* $VPS_USER@$VPS_HOST:$VPS_PATH/

# Upload website (optional - uncomment if needed)
# echo "[4/4] Updating website..."
# scp -r website/* $VPS_USER@$VPS_HOST:$VPS_PATH/static/

echo ""
echo "=== DEPLOYMENT COMPLETE ==="
echo "Download URL: http://$VPS_HOST:8080/download/TUR-Windows.zip"
echo ""
echo "To restart the server, run:"
echo "  ssh $VPS_USER@$VPS_HOST 'cd $VPS_PATH && pkill -f main.py; python3 main.py &'"
