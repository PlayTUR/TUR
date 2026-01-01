# TUR Deployment Guide

This guide explains how to set up the **The Unnamed Rhythm Game (TUR)** backend and website locally or on a server.

## 1. Prerequisites
- **Python 3.9+**
- **pip** (Python Package Manager)

## 2. Quick Start (All-in-One)
The `server/` folder now contains BOTH the backend logic and the frontend website.

1.  **Copy the folder to your VPS**:
    ```bash
    scp -r server/ user@your-vps:/path/to/tur-server
    ```

2.  **On the Server**:
    ```bash
    cd tur-server
    pip install fastapi uvicorn bcrypt httpx aiofiles
    
    # Set Environment Variables
    export TUR_ADMIN_KEY="your_secret_key"
    
    # Run
    python3 main.py
    ```

3.  **Access**:
    *   **Website**: `http://YOUR_SERVER_IP:8080`
    *   **Post News**: Send POST to `/api/v2/news/webhook` with header `Authorization: TUR_ADMIN_KEY` and body `{"content": "...", "author": "..."}`.

## 3. Advanced (Nginx Proxy)
If you want to run on port 80/443 with SSL:
*   Run `main.py` on 8080 (as above).
*   Configure Nginx to proxy_pass to `http://127.0.0.1:8080`.

## 4. Admin Access
1.  **Register** an account on your live site.
2.  **Promote yourself** via SSH on the server:
    ```bash
    curl -X POST http://localhost:8080/api/v2/admin/promote \
         -H "Content-Type: application/json" \
         -d '{"admin_key": "DKkc5k^Eu#V1K8q$wRYxlSJ!aVb84AgL3I96K6ROkZr7EqA9%M%#ojZ!Sl&V$Yfbryg19iSBNGL3", "username": "YOUR_USERNAME"}'
    ```
3.  **Access Panel**: Go to your Profile -> `[ACCESS ROOT TERMINAL]`.

## 5. Troubleshooting
*   **"Internal Server Error"**: You might be missing `aiofiles`. Run `pip install aiofiles`.
