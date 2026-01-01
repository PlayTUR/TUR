# -*- mode: python ; coding: utf-8 -*-
# TUR PyInstaller Spec File
# Build with: pyinstaller TUR.spec

import os

block_cipher = None

# Include ALL directories and files, excluding only:
# - beatmap_cache (generated at runtime)
# - song_creation (development only)
# - .git, .github (version control)
# - build.bat, build.sh (build scripts)
# - *.spec, *.py at root (source files - main.py is the entry point)

datas = [
    # Core game directories
    ('assets', 'assets'),
    ('core', 'core'),
    ('scenes', 'scenes'),
    ('sfx', 'sfx'),
    ('story_music', 'story_music'),
    ('mainmenu_music', 'mainmenu_music'),
    ('tools', 'tools'),
    ('songs', 'songs'),  # Empty songs folder for user content
    
    # Config and legal files
    ('default_settings.json', '.'),
    ('bans.json', '.'),
    ('eula.txt', '.'),
]

# Add optional files/folders if they exist
optional_items = [
    ('themes', 'themes'),
    ('.build_version', '.'),
    ('yt-dlp', '.'),  # YouTube downloader binary
]

for src, dst in optional_items:
    if os.path.exists(src):
        datas.append((src, dst))

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=['pygame', 'json', 'wave', 'struct', 'pypresence', 'websockets'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='TUR',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico' if os.path.exists('assets/icon.ico') else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='TUR',
)
