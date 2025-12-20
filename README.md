================================================================================
  ████████╗██╗   ██╗██████╗ 
  ╚══██╔══╝██║   ██║██╔══██╗
     ██║   ██║   ██║██████╔╝
     ██║   ██║   ██║██╔══██╗
     ██║   ╚██████╔╝██║  ██║
     ╚═╝    ╚═════╝ ╚═╝  ╚═╝
                                
  TERMINAL ULTRA RHYTHM
  A minimalist 4-key rhythm game for your terminal
================================================================================

TABLE OF CONTENTS
-----------------
1. About
2. Features
3. Installation
4. Usage
5. Controls
6. Gameplay
7. Configuration
8. System Requirements
9. Building from Source
10. Contributing
11. License
12. Credits

================================================================================
1. ABOUT
================================================================================

TUR is a terminal-based rhythm game that strips rhythm gaming down to its core
essence. No flashy graphics, no distractions - just you, your keyboard, and 
perfect timing. Experience the pure joy of hitting notes in sync with the beat,
all within your favorite terminal emulator.

Perfect for:
- Terminal enthusiasts who want their gaming retro
- Rhythm game veterans looking for a new challenge
- Developers who appreciate minimalist design
- Anyone wanting a quick rhythm fix without leaving the command line

================================================================================
2. FEATURES
================================================================================

✓ Pure ASCII/Unicode graphics
✓ 4-key rhythm gameplay with customizable keybinds
✓ Multiple difficulty levels
✓ Score tracking and combo system
✓ Multiple tracks/songs
✓ Lightweight and fast (< 10MB)
✓ Cross-platform (Windows, macOS, Linux)
✓ No dependencies required
✓ Offline play
✓ Configurable settings

================================================================================
3. INSTALLATION
================================================================================

OPTION A: Run from Source (Current)
------------------------------------
1. Clone the repository:
   git clone https://github.com/yourusername/tur.git
   cd tur

2. Install dependencies:
   pip install -r requirements.txt

3. Run:
   python tur.py

OPTION B: Install via pip
--------------------------
Coming soon!

OPTION C: Download Pre-built Executable
----------------------------------------
Coming soon! Standalone executables will be available for:
   - Windows: tur-windows.exe
   - macOS: tur-macos
   - Linux: tur-linux

================================================================================
4. USAGE
================================================================================

Basic usage:
  python tur.py

Start with specific song:
  python tur.py --song <song_name>

List available songs:
  python tur.py --list

Configure settings:
  python tur.py --config

Show help:
  python tur.py --help

================================================================================
5. CONTROLS
================================================================================

DEFAULT KEYBINDS:
  S - Lane 1 (Left)
  D - Lane 2
  K - Lane 3
  L - Lane 4 (Right)

MENU NAVIGATION:
  Arrow Keys / WASD - Navigate menus
  Enter - Select
  ESC - Back/Pause
  Q - Quit

GAMEPLAY:
  Space - Pause
  R - Restart song
  ESC - Return to menu

All keybinds are fully customizable in the config menu!

================================================================================
6. GAMEPLAY
================================================================================

HOW TO PLAY:
------------
Notes fall from the top of the screen in four lanes. Press the corresponding
key when the note reaches the target zone at the bottom. Timing is everything!

SCORING:
--------
  PERFECT  - Exact timing, full points + combo multiplier
  GREAT    - Good timing, most points + combo continues
  OK       - Acceptable timing, some points + combo continues
  MISS     - No points, combo breaks

COMBO SYSTEM:
-------------
Hit consecutive notes without missing to build your combo multiplier:
  x10 combo  - 1.5x score
  x20 combo  - 2.0x score
  x50 combo  - 2.5x score
  x100 combo - 3.0x score (MAX)

DIFFICULTY LEVELS:
------------------
  EASY   - Slower notes, wider timing window
  NORMAL - Standard speed and timing
  HARD   - Faster notes, tighter timing
  EXPERT - Maximum speed, pixel-perfect timing required

================================================================================
7. CONFIGURATION
================================================================================

Configuration file location:
  Windows: %APPDATA%/tur/config.toml
  macOS:   ~/.config/tur/config.toml
  Linux:   ~/.config/tur/config.toml

Example config.toml:
--------------------
[keybinds]
lane1 = "S"
lane2 = "D"
lane3 = "K"
lane4 = "L"

[gameplay]
scroll_speed = 1.0
note_speed_multiplier = 1.0
visual_offset = 0  # milliseconds

[display]
show_fps = false
color_scheme = "green"  # green, blue, cyan, amber

[audio]
volume = 0.8
sfx_enabled = true

================================================================================
8. SYSTEM REQUIREMENTS
================================================================================

MINIMUM:
  OS: Windows 7/macOS 10.12/Linux (any modern distro)
  Python: 3.7 or higher
  Memory: 50 MB RAM
  Storage: 10 MB available space
  Display: Terminal emulator with Unicode support
  Other: Keyboard

RECOMMENDED:
  Python: 3.9 or higher
  Terminal with 256-color support
  Terminal size: 80x24 or larger
  Audio support (for sound effects)

SUPPORTED TERMINALS:
  Windows: Windows Terminal, ConEmu, Cmder, PowerShell
  macOS: Terminal.app, iTerm2, Alacritty
  Linux: GNOME Terminal, Konsole, Alacritty, Kitty

PYTHON DEPENDENCIES:
  See requirements.txt for full list of dependencies

================================================================================
9. BUILDING FROM SOURCE
================================================================================

Prerequisites:
  - Python 3.7 or higher
  - pip (Python package manager)

Steps:
  1. Clone the repository:
     git clone https://github.com/yourusername/tur.git
     cd tur

  2. Create a virtual environment (recommended):
     python -m venv venv
     source venv/bin/activate  # On Windows: venv\Scripts\activate

  3. Install dependencies:
     pip install -r requirements.txt

  4. Run:
     python tur.py

CREATING EXECUTABLE (Optional):
  You can create a standalone executable using PyInstaller:
  
  1. Install PyInstaller:
     pip install pyinstaller

  2. Build executable:
     pyinstaller --onefile --console tur.py

  3. Find your executable in the dist/ folder

================================================================================
10. CONTRIBUTING
================================================================================

We welcome contributions! Here's how you can help:

REPORTING BUGS:
  Open an issue with:
  - Description of the bug
  - Steps to reproduce
  - Expected vs actual behavior
  - System information (OS, terminal)

FEATURE REQUESTS:
  Open an issue describing:
  - The feature you'd like
  - Why it would be useful
  - How it might work

PULL REQUESTS:
  1. Fork the repository
  2. Create a feature branch
  3. Make your changes
  4. Test thoroughly
  5. Submit a pull request

ADDING SONGS:
  See SONGS.md for information on creating custom charts

CODE STYLE:
  [Your code style guidelines]

================================================================================
11. LICENSE
================================================================================

[Your chosen license - e.g., MIT, GPL, Apache 2.0]

See LICENSE file for full details.

================================================================================
12. CREDITS
================================================================================

Created by: [Your Name/Handle]
GitHub: https://github.com/yourusername/tur
Itch.io: https://yourusername.itch.io/tur

Special thanks to:
  - [Contributors]
  - [Libraries/tools used]
  - The terminal gaming community

================================================================================

SUPPORT & COMMUNITY
-------------------
  Issues: https://github.com/yourusername/tur/issues
  Discussions: https://github.com/yourusername/tur/discussions
  Discord: [Your Discord server]
  Twitter: [Your Twitter]

================================================================================

Made with ♥ for terminal lovers everywhere

Press any key to start...
