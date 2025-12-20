import json
import os
import pygame

STATS_FILE = "settings.json"

DEFAULT_SETTINGS = {
    "name": "GUEST",
    "volume": 0.5,
    "speed": 600, # Pixels per second
    "keybinds": [pygame.K_s, pygame.K_d, pygame.K_k, pygame.K_l],
    "resolution": [1024, 768],
    "upscroll": False,
    "audio_offset": 0 # ms
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
                    self.settings.update(data)
            except Exception as e:
                print(f"Failed to load settings: {e}")

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
