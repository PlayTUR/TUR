import pygame
import sys
from scene_manager import SceneManager
from settings_manager import SettingsManager
from network_manager import NetworkManager
from audio_manager import AudioManager
from beatmap_generator import BeatmapGenerator
from tui_renderer import TUIRenderer, CRTShader
from scenes.menu_scenes import TitleScene
from config import *

import sys
from font_loader import ensure_font

# Ensure assets
ensure_font()

class Game:
    def __init__(self):
        pygame.init()
        self.settings = SettingsManager()
        
        # Apply Screen Size
        # Could read from settings, but config.py has constants for now.
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("TERMINAL BEAT V2.0")
        self.clock = pygame.time.Clock()
        
        self.audio = AudioManager()
        self.generator = BeatmapGenerator()
        self.renderer = TUIRenderer()
        self.network = NetworkManager(port=9999)
        self.scene_manager = SceneManager(self)
        
        # Audio Init
        vol = self.settings.get("volume")
        pygame.mixer.music.set_volume(vol)
        
        # Boot
        self.play_menu_bgm()
        self.scene_manager.switch_to(TitleScene)

    def play_menu_bgm(self):
        # ... existing bgm logic ...
        import os
        bgm_path = "assets/menu.mp3"
        if os.path.exists(bgm_path):
            try:
                pygame.mixer.music.load(bgm_path)
                pygame.mixer.music.play(-1)
                pygame.mixer.music.set_volume(self.settings.get("volume"))
            except Exception as e:
                print(e)

    def run(self):
        while True:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.settings.save()
                    self.network.close()
                    sys.exit()
                self.scene_manager.handle_input(event)
            
            self.scene_manager.update()
            
            self.screen.fill(BLACK)
            self.scene_manager.draw(self.screen)
            self.renderer.crt.apply(self.screen)
            pygame.display.flip()
            
            self.clock.tick(FPS)

if __name__ == "__main__":
    game = Game()
    game.run()
