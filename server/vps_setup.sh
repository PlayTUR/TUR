#!/bin/bash
# TUR VPS Setup: Wayland + VNC + Firewall
# Run this on your VPS

echo "--- 1. Updating System & Installing Dependencies ---"
sudo apt update
sudo apt install -y labwc wayvnc foot xwayland ufw

echo "--- 2. Configuring Firewall ---"
# Essential ports
sudo ufw allow 22/tcp     # SSH (Crucial!)
sudo ufw allow 80/tcp     # Game API
sudo ufw allow 5900/tcp   # VNC
echo "y" | sudo ufw enable

echo "--- 3. Creating Startup Script ---"
# Check for VNC password
if [ -z "$VNC_PASS" ]; then
    read -sp "Enter a VNC password (8 chars max): " VNC_PASS
    echo ""
fi

cat << EOF > start_vnc.sh
#!/bin/bash
# Kill old sessions
pkill -f wayvnc
pkill -f labwc

# Headless Wayland Config
export WLR_BACKEND=headless
export WLR_LIBINPUT_NO_DEVICES=1
export XDG_RUNTIME_DIR=/tmp/runtime-root
mkdir -p \$XDG_RUNTIME_DIR
chmod 700 \$XDG_RUNTIME_DIR

echo "Starting Label (Compositor)..."
labwc &
sleep 2

echo "Starting wayvnc on port 5900..."
# Using the provided password
wayvnc --password "$VNC_PASS" 0.0.0.0 5900 &
echo "--- SETUP COMPLETE ---"
echo "You can now connect via RealVNC to this IP on port 5900."
echo "Login: Just use the password you entered."
EOF

chmod +x start_vnc.sh
echo "All set. Run './start_vnc.sh' to begin the session."
