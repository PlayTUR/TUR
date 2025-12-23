import json
import os
import pygame

STATS_FILE = "settings.json"

DEFAULT_SETTINGS = {
    "name": "ANON",
    "volume": 0.8,
    "music_volume": 0.7,
    "sfx_volume": 1.0,
    "speed": 600,
    "keybinds": [pygame.K_s, pygame.K_d, pygame.K_k, pygame.K_l],
    "resolution": [1024, 768],
    "fullscreen": False,
    "vsync": True,
    "crt_filter": True,
    "upscroll": False,
    "audio_offset": 0,
    "note_shape": "BAR",
    "note_col_1": [50, 255, 50],
    "note_col_2": [255, 180, 50],
    "theme": "TERMINAL",
    "setup_complete": False,
<<<<<<< HEAD
    "joy_binds": [0, 1, 2, 3],
    "joy_triggers": [4, 5],
    "joy_deadzone": 0.2,
    "screen_shake": 1.0,
    # New settings
    "hit_sounds": True,
    "miss_sounds": True,
    "combo_sounds": True,
    "visual_effects": True,
    "last_tab": 0,
    "bg_dim": 0.5,
    "show_fps": 0, # 0=OFF, 1=SIMPLE, 2=DETAILED
    "show_hold_ends": True,
    # Auth
    "account_type": "GUEST", # GUEST or REGISTERED
    "last_name_change": 0, # Timestamp
    "is_admin": False, # Admin Panel Access
    "discord_client_id": "123456789012345678",
    "user_id": "00000000",
    "auto_recreate_beatmaps": False,
    "language": "EN",
    "vim_mode": False
=======
    "joy_binds": [0, 1, 2, 3], # Default buttons (A, B, X, Y)
    "joy_triggers": [4, 5],    # Default LB, RB
    "fullscreen": False,
    # New settings
    "hit_sounds": True,        # Play hit sounds
    "bg_dim": 0.5,             # Background dim (0-1)
    "show_fps": False,         # Show FPS counter
    "note_skin": "DEFAULT",    # Note skin style
    "miss_sounds": True,       # Play miss sounds
    "combo_sounds": True,      # Play combo milestone sounds
    "visual_effects": True,    # Particle effects on hit
>>>>>>> 0dc16cc (use code wyind in the fortnite item shop)
}

class SettingsManager:
    def __init__(self):
        self.settings = DEFAULT_SETTINGS.copy()
        self.load()

    def load(self):
        if os.path.exists(STATS_FILE):
            try:
                with open(STATS_FILE, 'r') as f:
                    data = json.load(f)
                    # Merge data into defaults to ensure new keys exist
                    for k, v in data.items():
                        self.settings[k] = v
            except Exception as e:
                print(f"Failed to load settings: {e}")
        
        # Ensure User ID exists
        if "user_id" not in self.settings or self.settings["user_id"] == "00000000":
            import random
            # Generate random 8-digit ID
            new_id = str(random.randint(10000000, 99999999))
            self.settings["user_id"] = new_id
            self.save()

    def save(self):
        try:
            with open(STATS_FILE, 'w') as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"Failed to save settings: {e}")

    def get(self, key):
        return self.settings.get(key, DEFAULT_SETTINGS.get(key))

    def set(self, key, value):
        self.settings[key] = value
        self.save()
