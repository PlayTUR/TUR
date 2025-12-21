import pygame
from core.scene_manager import Scene
from core.config import *
from core.updater import Updater
import sys

class UpdateScene(Scene):
    def on_enter(self, params=None):
        self.updater = Updater()
        self.progress = 0
        self.state = "CHECKING" 
        self.status_msg = "CONNECTING TO ITCH.IO..."
        self.generator = None

    def update(self):
        if self.state == "CHECKING":
            # Just simulate a delay
            self.progress += 2
            if self.progress >= 100:
                available = self.updater.check_for_updates()
                if available:
                    self.state = "DOWNLOADING"
                    self.status_msg = "DOWNLOADING PATCH FROM ITCH.IO..."
                    self.generator = self.updater.perform_update()
                    self.progress = 0
                else:
                    self.state = "COMPLETE"
                    self.status_msg = "SYSTEM IS UP TO DATE."
                    
        elif self.state == "DOWNLOADING":
            try:
                # Advance generator
                self.progress = next(self.generator)
            except StopIteration:
                self.state = "INSTALLING"
                self.status_msg = "APPLYING PATCH..."
                self.progress = 0
                
        elif self.state == "INSTALLING":
            self.progress += 5
            if self.progress >= 100:
                self.state = "RESTARTING"
                self.status_msg = "REBOOTING..."
                
        elif self.state == "RESTARTING":
            # Trigger restart
            self.updater.restart_game()

    def draw(self, surface):
        self.game.renderer.draw_text(surface, "SYSTEM UPDATE", 100, 100, TERM_GREEN, self.game.renderer.big_font)
        
        self.game.renderer.draw_text(surface, self.status_msg, 100, 300, TERM_WHITE)
        
        # Draw Bar
        self.game.renderer.draw_progress(surface, self.progress, 100)
        self.game.renderer.draw_text(surface, f"{self.progress}%", 900, 720, TERM_AMBER)

    def handle_input(self, event):
        pass
