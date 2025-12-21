import pygame

# Screen
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
FPS = 120

# Colors (Themes)
THEMES = {
    "TERMINAL": {
        "bg": (10, 20, 10),
        "primary": (0, 255, 100),   # Green
        "secondary": (255, 180, 0), # Amber
        "text": (220, 220, 255),
        "grid": (0, 50, 0),
        "error": (255, 50, 50)
    },
    "CYBERPUNK": {
        "bg": (20, 10, 30),
        "primary": (255, 0, 150),   # Pink
        "secondary": (0, 200, 255), # Cyan
        "text": (255, 255, 200),
        "grid": (50, 0, 50),
        "error": (255, 50, 50)
    },
    "AMBER": {
        "bg": (20, 15, 5),
        "primary": (255, 200, 0),   # Gold
        "secondary": (255, 100, 0), # Orange
        "text": (255, 230, 200),
        "grid": (50, 30, 0),
        "error": (255, 50, 50)
    },
    "MATRIX": {
        "bg": (0, 0, 0),
        "primary": (0, 255, 50),
        "secondary": (0, 150, 20),
        "text": (200, 255, 200),
        "grid": (0, 30, 0),
        "error": (255, 50, 50)
    },
    "RETRO_BLUE": {
        "bg": (10, 10, 30),
        "primary": (100, 150, 255),
        "secondary": (50, 255, 255),
        "text": (220, 220, 255),
        "grid": (20, 20, 60),
        "error": (255, 50, 50)
    }
}

# Legacy Constants (Mapped to TERMINAL for safety / fallback)
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
    "EASY": {"density": 0.4, "speed": 400},
    "MEDIUM": {"density": 0.7, "speed": 600},
    "HARD": {"density": 1.0, "speed": 800},
    "EXTREME": {"density": 1.3, "speed": 1000},
    "FUCK YOU": {"density": 2.5, "speed": 1400} 
}

# TUI Config
FONT_SIZE = 20
LANE_WIDTH_CHARS = 10 # Width in characters
LANE_START_X_CHARS = 10
CHAR_WIDTH = 12 # Approximation, depends on font
CHAR_HEIGHT = 20

# Multiplayer
DEFAULT_PORT = 9999
