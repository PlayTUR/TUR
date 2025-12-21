import pygame
from core.scene_manager import Scene
from core.config import *

class ResultScene(Scene):
    def on_enter(self, params):
        self.params = params
        self.failed = params.get('failed', False)
        self.score = params.get('score', 0)
        self.max_combo = params.get('max_combo', 0)
        self.perfects = params.get('perfects', 0)
        self.goods = params.get('goods', 0)
        self.bads = params.get('bads', 0)
        self.misses = params.get('misses', 0)
        self.song_name = params.get('song', 'Unknown')
        
        self.accuracy = self.calculate_accuracy()
        self.grade = self.calculate_grade()
        
        # Menu Options
        self.menu_items = ["REPLAY", "QUIT TO MENU"]
        self.selected_index = 0

    def calculate_accuracy(self):
        total_hits = self.perfects + self.goods + self.bads + self.misses
        if total_hits == 0: return 0.0
        weighted = (self.perfects * 100 + self.goods * 75 + self.bads * 50)
        return (weighted / (total_hits * 100)) * 100

    def calculate_grade(self):
        if self.failed: return "F"
        acc = self.accuracy
        if acc >= 99.0: return "S"
        if acc >= 95.0: return "A"
        if acc >= 85.0: return "B"
        if acc >= 75.0: return "C"
        if acc >= 60.0: return "D"
        return "F"

    def draw(self, surface):
        theme = self.game.renderer.get_theme()
        surface.fill(theme["bg"])
        
        header = "RECOVERY_REPORT" if not self.failed else "FAILURE_ANALYSIS"
        self.game.renderer.draw_text(surface, header, 100, 50, theme["primary"], self.game.renderer.big_font)
        
        # Song Info
        self.game.renderer.draw_text(surface, f"FILE: {self.song_name}", 100, 120, theme["text"])
        
        # Grade (Huge)
        grade_col = theme["secondary"] if self.grade != "F" else (255, 50, 50)
        self.game.renderer.draw_text(surface, f"GRADE: {self.grade}", 600, 150, grade_col, self.game.renderer.big_font)
        
        # Stats List
        stats_x = 100
        stats_y = 200
        spacing = 40
        
        stats = [
            (f"SCORE: {self.score}", theme["text"]),
            (f"MAX COMBO: {self.max_combo}", theme["secondary"]),
            (f"ACCURACY: {self.accuracy:.2f}%", theme["primary"]),
            ("", (0,0,0)), # Spacer
            (f"PERFECT: {self.perfects}", (0, 255, 100)),
            (f"GOOD: {self.goods}", (255, 200, 0)),
            (f"BAD: {self.bads}", (255, 100, 0)),
            (f"MISSES: {self.misses}", (255, 50, 50))
        ]
        
        for i, (txt, col) in enumerate(stats):
            if txt:
                self.game.renderer.draw_text(surface, txt, stats_x, stats_y + i * spacing, col)

        # Interaction
        menu_y = 600
        for i, item in enumerate(self.menu_items):
            col = theme["primary"] if i == self.selected_index else (150, 150, 150)
            prefix = "> " if i == self.selected_index else "  "
            self.game.renderer.draw_text(surface, f"{prefix}{item}", 100, menu_y + i * 50, col)

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_index = (self.selected_index - 1) % len(self.menu_items)
            elif event.key == pygame.K_DOWN:
                self.selected_index = (self.selected_index + 1) % len(self.menu_items)
            elif event.key == pygame.K_RETURN:
                self.play_sfx("accept")
                choice = self.menu_items[self.selected_index]
                if choice == "REPLAY":
                    from scenes.game_scene import GameScene
                    self.game.scene_manager.switch_to(GameScene, {
                        'song': self.song_name,
                        'difficulty': self.params.get('difficulty', 'MEDIUM')
                    })
                else:
                    from scenes.menu_scenes import SongSelectScene
                    self.game.scene_manager.switch_to(SongSelectScene)
            elif event.key == pygame.K_ESCAPE:
                from scenes.menu_scenes import SongSelectScene
                self.game.scene_manager.switch_to(SongSelectScene)
