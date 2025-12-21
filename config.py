import pygame

# Screen
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
FPS = 120

# Colors (Matrix / Retro Terminal Palette)
BLACK = (5, 5, 10)
BG_Dark = (10, 20, 10)
TERM_GREEN = (0, 255, 100)
TERM_AMBER = (255, 180, 0)
TERM_RED = (255, 50, 50)
TERM_BLUE = (50, 150, 255)
TERM_WHITE = (220, 220, 255)
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
