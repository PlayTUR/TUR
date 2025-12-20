import curses
import pygame
import os
import time
from curses_renderer import CursesRenderer
from scene_manager import SceneManager
from scenes.menu_scenes import TitleScene
from settings_manager import SettingsManager
from audio_manager import AudioManager
from beatmap_generator import BeatmapGenerator
from network_manager import NetworkManager
from score_manager import ScoreManager
from config import *
import sys

# Main TUI Entry Point
class GameTUI:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.renderer = CursesRenderer(stdscr)
        self.settings = SettingsManager()
        self.audio = AudioManager()
        self.score_manager = ScoreManager()
        self.generator = BeatmapGenerator()
        self.network = NetworkManager()
        self.scene_manager = SceneManager(self)
        
        # Audio Init (Headless)
        pygame.init() # Needed for mixer?
        pygame.mixer.init()
        vol = self.settings.get("volume")
        pygame.mixer.music.set_volume(vol)
        
        self.running = True

    def run(self):
        # Boot
        self.scene_manager.switch_to(TitleScene)
        self.last_time = time.time()
        
        # Make stdscr non-blocking
        self.stdscr.nodelay(True)
        curses.curs_set(0) # Hide cursor
        
        while self.running:
            start = time.time()
            dt = start - self.last_time
            self.last_time = start
            
            # Update Dimensions
            self.renderer.update_dimensions()
            
            # Input
            key = self.stdscr.getch()
            if key != -1:
                self.handle_input(key)
                
            # Update
            self.scene_manager.update()
            
            # Draw
            self.renderer.clear()
            self.scene_manager.draw(None) # Surface is None
            self.renderer.present()
            
            # Cap FPS (30 for terminal is plenty)
            elapsed = time.time() - start
            if elapsed < 0.033:
                time.sleep(0.033 - elapsed)

    def handle_input(self, key):
        # Map Curses keys to Pygame-like events for Scenes?
        # Scenes expect Pygame events. We must mock them.
        
        # Create a Mock Event
        class MockEvent:
            def __init__(self, key_code):
                self.type = pygame.KEYDOWN
                self.key = key_code
                self.unicode = chr(key_code) if 32 <= key_code <= 126 else ""

        # Mapping
        pygame_key = None
        if key == 10 or key == 13: pygame_key = pygame.K_RETURN
        elif key == 27: pygame_key = pygame.K_ESCAPE
        elif key == curses.KEY_UP: pygame_key = pygame.K_UP
        elif key == curses.KEY_DOWN: pygame_key = pygame.K_DOWN
        elif key == curses.KEY_LEFT: pygame_key = pygame.K_LEFT
        elif key == curses.KEY_RIGHT: pygame_key = pygame.K_RIGHT
        elif key == ord('s'): pygame_key = pygame.K_s
        elif key == ord('d'): pygame_key = pygame.K_d
        elif key == ord('k'): pygame_key = pygame.K_k
        elif key == ord('l'): pygame_key = pygame.K_l
        # ... add more as needed
        else:
             # Basic char mapping
             if 32 <= key <= 126:
                 # How to map 'q' to K_q?
                 # ord('q') is 113. pygame.K_q is 113. 
                 pygame_key = key
        
        if pygame_key:
            evt = MockEvent(pygame_key)
            self.scene_manager.handle_input(evt)

    def play_menu_bgm(self):
         # Simplified BGM for TUI
         pass

def main(stdscr):
    game = GameTUI(stdscr)
    game.run()

if __name__ == "__main__":
    curses.wrapper(main)
