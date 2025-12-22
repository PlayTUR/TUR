"""
Result Scene - Game Over/Victory Screen
Handles score display and story continuation.
"""

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
        self.difficulty = params.get('difficulty', 'MEDIUM')
        
        # Story mode parameters
        self.mode = params.get('mode', 'single')
        self.next_scene_class = params.get('next_scene_class')
        self.next_scene_params = params.get('next_scene_params')
        
        self.accuracy = self.calculate_accuracy()
        self.grade = self.calculate_grade()
        
        # Dynamic menu based on mode
        if self.mode == 'story':
            if self.failed:
                self.menu_items = ["RETRY MISSION", "ABORT CAMPAIGN"]
            else:
                self.menu_items = ["CONTINUE", "REPLAY", "ABORT CAMPAIGN"]
        else:
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
        r = self.game.renderer
        theme = r.get_theme()
        surface.fill(theme["bg"])
        
        # Header
        if self.mode == 'story':
            header = "MISSION COMPLETE" if not self.failed else "MISSION FAILED"
        else:
            header = "OPERATION COMPLETE" if not self.failed else "OPERATION FAILED"
        
        header_color = theme["primary"] if not self.failed else theme["error"]
        r.draw_text(surface, f"◉ {header} ◉", 300, 50, header_color, r.big_font)
        
        # Song info (truncated)
        song_display = self.song_name[-40:] if len(self.song_name) > 40 else self.song_name
        r.draw_text(surface, f"TARGET: {song_display}", 100, 120, theme["text"])
        
        # Grade panel
        r.draw_panel(surface, 600, 130, 300, 150, "RATING")
        grade_color = theme["secondary"] if self.grade != "F" else theme["error"]
        
        # Center grade
        grade_w = r.big_font.size(self.grade)[0]
        r.draw_text(surface, self.grade, 600 + (300 - grade_w) // 2, 170, grade_color, r.big_font)
        
        # Center accuracy
        acc_text = f"{self.accuracy:.1f}%"
        acc_w = r.font.size(acc_text)[0]
        r.draw_text(surface, acc_text, 600 + (300 - acc_w) // 2, 230, (150, 150, 150))
        
        # Stats panel
        r.draw_panel(surface, 80, 180, 450, 280, "STATISTICS")
        
        stats = [
            (f"SCORE: {self.score:,}", theme["text"]),
            (f"MAX COMBO: {self.max_combo}x", theme["secondary"]),
            ("", None),
            (f"PERFECT: {self.perfects}", (100, 255, 100)),
            (f"GOOD: {self.goods}", (255, 200, 50)),
            (f"BAD: {self.bads}", (255, 100, 50)),
            (f"MISS: {self.misses}", (255, 50, 50))
        ]
        
        y = 200
        for txt, col in stats:
            if txt and col:
                r.draw_text(surface, txt, 100, y, col)
            y += 35
        
        # Menu
        menu_y = 520
        for i, item in enumerate(self.menu_items):
            r.draw_button(surface, item, 300, menu_y + i * 45, i == self.selected_index, 400)
        
        # Mode indicator
        if self.mode == 'story':
            r.draw_text(surface, "STORY MODE", 50, 700, theme["secondary"])

    def handle_input(self, event):
        if event.type != pygame.KEYDOWN:
            return
        
        if event.key == pygame.K_UP:
            self.selected_index = (self.selected_index - 1) % len(self.menu_items)
            self.play_sfx("blip")
        elif event.key == pygame.K_DOWN:
            self.selected_index = (self.selected_index + 1) % len(self.menu_items)
            self.play_sfx("blip")
        elif event.key == pygame.K_RETURN:
            self.play_sfx("accept")
            self._handle_selection()
        elif event.key == pygame.K_ESCAPE:
            self._go_to_menu()

    def _handle_selection(self):
        choice = self.menu_items[self.selected_index]
        
        if choice == "CONTINUE":
            # Continue story to next chapter
            if self.next_scene_class and self.next_scene_params:
                self.game.scene_manager.switch_to(self.next_scene_class, self.next_scene_params)
            else:
                # Fallback to story scene
                from scenes.story_scene import StoryScene
                self.game.scene_manager.switch_to(StoryScene)
        
        elif choice in ["REPLAY", "RETRY MISSION"]:
            from scenes.game_scene import GameScene
            self.game.scene_manager.switch_to(GameScene, {
                'song': self.song_name,
                'difficulty': self.difficulty,
                'mode': self.mode,
                'next_scene_class': self.next_scene_class,
                'next_scene_params': self.next_scene_params
            })
        
        elif choice in ["QUIT TO MENU", "ABORT CAMPAIGN"]:
            self._go_to_menu()

    def _go_to_menu(self):
        if self.mode == 'story':
            from scenes.menu_scenes import TitleScene
            self.game.scene_manager.switch_to(TitleScene)
        else:
            from scenes.menu_scenes import SongSelectScene
            self.game.scene_manager.switch_to(SongSelectScene)
