import sys
import os
import subprocess
import platform

def get_clipboard():
    """Fetches text from the system clipboard (Windows/Linux)."""
    try:
        if platform.system() == "Windows":
            # Use PowerShell for clean clipboard reading
            cmd = ['powershell', '-command', 'Get-Clipboard']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=1)
            return result.stdout.strip()
        else:
            # Linux: Try xclip then xsel
            try:
                result = subprocess.run(['xclip', '-selection', 'clipboard', '-o'], capture_output=True, text=True, timeout=1)
                if result.returncode == 0: return result.stdout.strip()
            except: pass
            
            try:
                result = subprocess.run(['xsel', '--clipboard', '--output'], capture_output=True, text=True, timeout=1)
                if result.returncode == 0: return result.stdout.strip()
            except: pass
    except:
        pass
    return ""

def get_app_root():
    """
    Returns the directory where the application is installed.
    """
    if getattr(sys, 'frozen', False):
        # Running as binary (PyInstaller)
        return os.path.dirname(sys.executable)
    # Running as source
    return os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

def resource_path(relative_path):
    """
    Get absolute path to internal bundled resource (read-only).
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def find_resource(filename, hint_dirs=None):
    """
    Finds a file by deep-searching:
    1. Internal bundled assets (resource_path)
    2. Local installation folder (get_app_root)
    3. Recursive fallback
    """
    if not filename:
        return None

    # --- 1. Internal Bundled Check (Priority for Binaries) ---
    res_p = resource_path(filename)
    if os.path.exists(res_p):
        return res_p

    # --- 2. Direct path check (External) ---
    if os.path.exists(filename):
        return filename
        
    # --- 3. Check hint directories relative to binary/script root ---
    root = get_app_root()
    search_dirs = hint_dirs or []
    search_dirs += ["songs", "mainmenu_music", "."]
    
    base_name = os.path.splitext(os.path.basename(filename))[0]
    exts = [".mp3", ".wav", ".ogg", ".flac"]
    
    for d in search_dirs:
        # Try relative to CWD
        p = os.path.join(d, filename)
        if os.path.exists(p): return p
        
        # Fuzzy extension check (CWD)
        for e in exts:
            pf = os.path.join(d, base_name + e)
            if os.path.exists(pf): return pf

        # Try relative to App Root
        p_root = os.path.join(root, d, os.path.basename(filename))
        if os.path.exists(p_root): return p_root
        
        # Fuzzy extension check (Root)
        for e in exts:
            prf = os.path.join(root, d, base_name + e)
            if os.path.exists(prf): return prf
                
    # --- 4. Recursive search (Local fallback) ---
    print(f"DEBUG: Deep searching external folders for {filename}...")
    for s_root, dirs, files in os.walk(root, topdown=True):
        if any(x in s_root for x in ["venv", ".git", "__pycache__"]):
            continue
        # Direct Match
        if os.path.basename(filename) in files:
            return os.path.join(s_root, os.path.basename(filename))
        # Fuzzy Match
        for f in files:
            if os.path.splitext(f)[0] == base_name and os.path.splitext(f)[1].lower() in exts:
                return os.path.join(s_root, f)
            
    return None
