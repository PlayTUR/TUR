import json
import os
import pygame

STATS_FILE = "settings.json"

# Discord Rich Presence Client ID for TUR
# This ID is registered with Discord and allows RPC to work for all players
DISCORD_CLIENT_ID = "1453128602110529678"

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
    "joy_binds": [0, 1, 2, 3],
    "joy_triggers": [4, 5],
    "joy_deadzone": 0.2,
    "screen_shake": 1.0,
    "hit_sounds": True,
    "miss_sounds": True,
    "combo_sounds": True,
    "visual_effects": True,
    "post_effects": True,
    "last_tab": 0,
    "bg_dim": 0.5,
    "show_fps": 0,
    "show_hold_ends": True,
    "account_type": "GUEST",
    "last_name_change": 0,
    "is_admin": False,
    "discord_client_id": DISCORD_CLIENT_ID,
    "user_id": "00000000",
    "auto_recreate_beatmaps": False,
    "language": "EN",
    "vim_mode": False,
    "note_skin": "DEFAULT",
    "update_source": "github",
}

class SettingsManager:
    def __init__(self):
        self.settings = DEFAULT_SETTINGS.copy()
        self.load()

    def load(self):
        # First, try to load bundled default_settings.json (for fresh installs)
        # This ensures the Discord client ID is always correct
        try:
            from core.utils import resource_path
            bundled_defaults = resource_path("default_settings.json")
            if os.path.exists(bundled_defaults):
                with open(bundled_defaults, 'r') as f:
                    bundled = json.load(f)
                    for k, v in bundled.items():
                        if k not in self.settings or k == "discord_client_id":
                            self.settings[k] = v
        except Exception as e:
            pass  # Use hardcoded defaults
        
        # Then load user settings on top
        if os.path.exists(STATS_FILE):
            try:
                with open(STATS_FILE, 'r') as f:
                    data = json.load(f)
                    # Merge data into defaults to ensure new keys exist
                    for k, v in data.items():
                        self.settings[k] = v
            except Exception as e:
                print(f"Failed to load settings: {e}")
        
        # Always ensure Discord client ID is the correct one (not a placeholder)
        if self.settings.get("discord_client_id") == "123456789012345678":
            self.settings["discord_client_id"] = DISCORD_CLIENT_ID
        
        # Ensure User ID exists
        if "user_id" not in self.settings or self.settings["user_id"] == "00000000":
            import random
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
