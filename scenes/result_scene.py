import pygame
from scene_manager import Scene
from config import *

class ResultScene(Scene):
    def on_enter(self, params):
        self.params = params
        self.rank = self.calculate_rank()
        
    def calculate_rank(self):
        total = self.params['perfects'] + self.params['goods'] + self.params['misses'] # + bads if we tracked them fully
        if total == 0: return "F"
        
        # Simple weighted accuracy
        # 300 * total is max score basically? simplified
        max_score = total * 300
        real_score = self.params['score']
        
        # In mania 1,000,000 is limit usually, but we use raw score.
        # Let's use accuracy percentage
        acc = 0
        if max_score > 0:
            acc = real_score / max_score
            
        if acc >= 0.95: return "S"
        if acc >= 0.90: return "A"
        if acc >= 0.80: return "B"
        if acc >= 0.70: return "C"
        if acc >= 0.60: return "D"
        return "F"

    def draw(self, surface):
        self.game.renderer.draw_text(surface, "MISSION DEBRIEF", 100, 50, TERM_GREEN, self.game.renderer.big_font)
        
        self.game.renderer.draw_text(surface, f"SONG: {self.params['song']}", 100, 150, TERM_WHITE)
        self.game.renderer.draw_text(surface, f"DIFFICULTY: {self.params['difficulty']}", 100, 180, TERM_WHITE)
        
        # Big Rank
        color = TERM_GREEN if self.rank in ["S", "A"] else (TERM_RED if self.rank == "F" else TERM_AMBER)
        self.game.renderer.draw_text(surface, f"RANK: {self.rank}", 400, 250, color, self.game.renderer.big_font)
        
        self.game.renderer.draw_text(surface, f"SCORE: {self.params['score']}", 100, 350, TERM_WHITE)
        self.game.renderer.draw_text(surface, f"MAX COMBO: {self.params['max_combo']}", 100, 380, TERM_WHITE)
        
        self.game.renderer.draw_text(surface, f"PERFECT: {self.params['perfects']}", 100, 450, (100, 255, 255))
        self.game.renderer.draw_text(surface, f"GOOD: {self.params['goods']}", 100, 480, (100, 255, 100))
        self.game.renderer.draw_text(surface, f"MISS: {self.params['misses']}", 100, 510, (255, 50, 50))
        
        self.game.renderer.draw_text(surface, "PRESS ENTER TO CONTINUE", 100, 650, (100, 100, 100))

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                from scenes.menu_scenes import SongSelectScene
                self.game.scene_manager.switch_to(SongSelectScene)
