import pygame
import os
import json

# Screen
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
FPS = 120

# Common Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
TERM_GREEN = (0, 255, 100)
TERM_ORANGE = (255, 150, 0)
TERM_WHITE = (220, 220, 255)
TERM_RED = (255, 50, 50)
TERM_AMBER = (255, 150, 0)

# Colors (Themes)
THEMES = {
    "TERMINAL": {
        "bg": (10, 20, 10),
        "primary": (0, 255, 100),
        "secondary": (255, 180, 0),
        "text": (220, 220, 255),
        "grid": (0, 50, 0),
        "error": (255, 50, 50)
    },
    "CYBERPUNK": {
        "bg": (20, 10, 30),
        "primary": (255, 0, 150),
        "secondary": (0, 200, 255),
        "text": (255, 255, 200),
        "grid": (50, 0, 50),
        "error": (255, 50, 50)
    },
    "AMBER": {
        "bg": (20, 15, 5),
        "primary": (255, 200, 0),
        "secondary": (255, 100, 0),
        "text": (255, 230, 200),
        "grid": (50, 30, 0),
        "error": (255, 50, 50)
    },
    "MIDNIGHT": {
        "bg": (5, 5, 15),
        "primary": (100, 100, 255),
        "secondary": (180, 100, 255),
        "text": (200, 200, 255),
        "grid": (15, 15, 40),
        "error": (255, 100, 100)
    },
    "RETRO_BLUE": {
        "bg": (10, 10, 30),
        "primary": (100, 150, 255),
        "secondary": (50, 255, 255),
        "text": (220, 220, 255),
        "grid": (20, 20, 60),
        "error": (255, 50, 50)
    },
    "SYNTHWAVE": {
        "bg": (15, 5, 25),
        "primary": (255, 50, 200),
        "secondary": (50, 200, 255),
        "text": (255, 200, 255),
        "grid": (40, 10, 60),
        "error": (255, 100, 100)
    },
    "NEON": {
        "bg": (5, 5, 10),
        "primary": (0, 255, 200),
        "secondary": (255, 0, 255),
        "text": (255, 255, 255),
        "grid": (20, 20, 30),
        "error": (255, 50, 50)
    },
    "OCEAN": {
        "bg": (5, 15, 25),
        "primary": (50, 200, 255),
        "secondary": (100, 255, 200),
        "text": (200, 230, 255),
        "grid": (10, 30, 50),
        "error": (255, 100, 100)
    },
    "SUNSET": {
        "bg": (25, 10, 10),
        "primary": (255, 150, 50),
        "secondary": (255, 80, 100),
        "text": (255, 230, 200),
        "grid": (50, 20, 20),
        "error": (255, 255, 100)
    },
    "FOREST": {
        "bg": (10, 20, 10),
        "primary": (100, 200, 50),
        "secondary": (200, 150, 50),
        "text": (220, 255, 200),
        "grid": (20, 40, 20),
        "error": (255, 100, 50)
    },
    "BLOOD": {
        "bg": (20, 5, 5),
        "primary": (255, 50, 50),
        "secondary": (180, 0, 0),
        "text": (255, 200, 200),
        "grid": (50, 10, 10),
        "error": (255, 255, 0)
    }
}

def load_custom_themes():
    """Load custom themes from themes folder"""
    themes_dir = "themes"
    if os.path.exists(themes_dir):
        for f in os.listdir(themes_dir):
            if f.endswith('.json'):
                try:
                    with open(os.path.join(themes_dir, f)) as fp:
                        data = json.load(fp)
                        name = data.get('name', f[:-5]).upper()
                        THEMES[name] = {k: tuple(v) if isinstance(v, list) else v 
                                        for k, v in data.items() if k != 'name'}
                except:
                    pass

# Try loading custom themes on import
load_custom_themes()

# Legacy Constants
BG_Dark = THEMES["TERMINAL"]["bg"]
TERM_GREEN = THEMES["TERMINAL"]["primary"]
TERM_AMBER = THEMES["TERMINAL"]["secondary"]
TERM_RED = THEMES["TERMINAL"]["error"]
TERM_BLUE = (50, 150, 255)
TERM_WHITE = THEMES["TERMINAL"]["text"]
GLOW_GREEN = (0, 255, 100, 50)

# Difficulty Settings
DIFFICULTIES = ["EASY", "MEDIUM", "HARD", "EXTREME", "FUCK YOU"]
DIFF_SETTINGS = {
    "EASY": {"density": 0.5, "speed": 400},
    "MEDIUM": {"density": 0.75, "speed": 600},
    "HARD": {"density": 1.0, "speed": 850},
    "EXTREME": {"density": 1.2, "speed": 1100},
    "FUCK YOU": {"density": 1.5, "speed": 1500}
}

# Editor / Map Events
EVENT_CAMERA_ZOOM = "cam_zoom"   # {time, value, duration}
EVENT_CAMERA_SHAKE = "cam_shake" # {time, intensity, duration}
EVENT_NOTE_GLOW = "glow"         # {time, color, duration}
EVENT_SPEED_CHANGE = "speed"     # {time, multiplier}

# TUI Config
FONT_SIZE = 20
LANE_WIDTH_CHARS = 10
LANE_START_X_CHARS = 10
CHAR_WIDTH = 12
CHAR_HEIGHT = 20

# Multiplayer
DEFAULT_PORT = 9999

# Server Config (Mock)
# In a production environment, ADMIN_ACCESS would be determined by 
# verifying a signed token against this server URL.
SERVER_URL = "https://api.turtherhythm.com" 
ADMIN_USERS = ["Wyind"] # Server-side whitelist (Mock)

def VERIFY_ADMIN_TOKEN(token):
    """
    Mock function to simulate server-side admin verification.
    In reality, this would make a requests.post() to SERVER_URL/verify
    """
    # Simulate verify logic
    import hashlib
    # Dummy check: if token matches known admin hash
    return False # Default to secure
