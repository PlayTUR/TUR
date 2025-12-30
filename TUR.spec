# -*- mode: python ; coding: utf-8 -*-
# TUR PyInstaller Spec File
# Build with: pyinstaller TUR.spec

import os

block_cipher = None

# Collect all data files
datas = [
    ('sfx', 'sfx'),
    ('songs', 'songs'),
    ('story_music', 'story_music'),
    ('assets', 'assets'),
    ('mainmenu_music', 'mainmenu_music'),
    ('core', 'core'),
    ('scenes', 'scenes'),
]

# Add optional directories if they exist (EXCLUDE beatmap_cache and song_creation)
optional_dirs = ['themes', 'tools']
for folder in optional_dirs:
    if os.path.exists(folder):
        datas.append((folder, folder))

# Add build version file if it exists (for auto-updater)
if os.path.exists('.build_version'):
    datas.append(('.build_version', '.'))

# Add default settings file with Discord RPC ID
# This provides the default Discord client ID for all users
if os.path.exists('default_settings.json'):
    datas.append(('default_settings.json', '.'))

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=['pygame', 'json', 'wave', 'struct', 'pypresence'],
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='TUR',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to True for debug output
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico' if os.path.exists('assets/icon.ico') else None,
)
