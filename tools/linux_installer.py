#!/usr/bin/env python3
import os
import sys

def create_desktop_file():
    """
    Creates a .desktop file in ~/.local/share/applications for system integration.
    """
    if sys.platform != "linux":
        print("This script is intended for Linux integration.")
        return

    home = os.path.expanduser("~")
    apps_dir = os.path.join(home, ".local/share/applications")
    if not os.path.exists(apps_dir):
        os.makedirs(apps_dir)

    # Detect current directory (assuming it's the install dir)
    install_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    # Executable path
    # If running as source, it's python3 main.py
    # If binary, it would be the binary filename
    exec_path = f"python3 {os.path.join(install_dir, 'main.py')}"
    icon_path = os.path.join(install_dir, "assets", "icon.png") # Assuming an icon exists or will exist

    desktop_content = f"""[Desktop Entry]
Type=Application
Name=TUR [The Rhythm]
Comment=High-performance 8-bit Rhythm Game
Icon={icon_path}
Exec={exec_path}
Terminal=false
Categories=Game;
Path={install_dir}
"""
    
    desktop_file = os.path.join(apps_dir, "tur.desktop")
    with open(desktop_file, "w") as f:
        f.write(desktop_content)
    
    os.chmod(desktop_file, 0o755)
    print(f"✓ Created Desktop Integration: {desktop_file}")
    print(f"Install Location: {install_dir}")

if __name__ == "__main__":
    create_desktop_file()
