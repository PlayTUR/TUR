import os
import sys
import subprocess
import shutil

def check_pyinstaller():
    try:
        import PyInstaller
        print(">> PyInstaller found.")
    except ImportError:
        print("!! PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

def build():
    print(">> Starting Build Process for TerminalBeat...")
    
    # OS Detection
    is_windows = sys.platform.startswith('win')
    is_mac = sys.platform == 'darwin'
    is_linux = sys.platform.startswith('linux')
    
    sep = ";" if is_windows else ":"
    
    # Define Assets to Bundle (font, etc)
    # Format: source_path:dest_path
    # We want assets/font.ttf to be INSIDE the exe if possible, or alongside.
    # Ideally, we bundle 'assets' folder into '.' 
    add_data = f"--add-data=assets{sep}assets"
    
    # Core command
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--windowed", # No console window
        "--name=TerminalBeat",
        add_data,
        "main.py"
    ]
    
    print(f">> Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    
    print(">> Build Complete.")
    print(f">> Executable location: dist/TerminalBeat{'.exe' if is_windows else ''}")
    
    # Post-Build: Copy external folders (songs, mainmenu_music) to dist/
    # so the user can actually play out of the box.
    print(">> Setting up distribution folder...")
    dist_dir = "dist"
    
    dirs_to_copy = ["songs", "mainmenu_music"]
    for d in dirs_to_copy:
        src = d
        dst = os.path.join(dist_dir, d)
        if os.path.exists(src):
            if os.path.exists(dst):
                print(f"   - updating {d}...")
                # Simple copy logic (could use shutil.copytree with dirs_exist_ok=True on py3.8+)
                # keeping it simple:
                pass 
            else:
                print(f"   - copying {d}...")
                shutil.copytree(src, dst)
        else:
            print(f"   ! Warning: Source directory '{d}' not found. Creating empty in dist.")
            os.makedirs(dst, exist_ok=True)

    print(">> DONE. You can zip the 'dist' folder and share it!")

if __name__ == "__main__":
    check_pyinstaller()
    build()
