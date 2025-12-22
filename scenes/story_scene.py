"""
Story Scene - Campaign Briefing with Animated ASCII
"""

import pygame
from core.scene_manager import Scene
from core.config import *
from core.story_generator import StoryGenerator


class StoryScene(Scene):
    def on_enter(self, params=None):
        if params is None:
            params = {}
        
        self.campaign = params.get('campaign')
        if not self.campaign:
            try:
                gen = StoryGenerator()
                self.campaign = gen.generate_campaign()
            except Exception as e:
                print(f"Story error: {e}")
                self.campaign = {'title': 'OPERATION', 'chapters': []}
        
        self.current_idx = params.get('index', 0)
        self.chapters = self.campaign.get('chapters', [])
        
        if self.current_idx >= len(self.chapters):
            self.state = "COMPLETE"
        else:
            self.state = "BRIEFING"
            self.chapter = self.chapters[self.current_idx]
            
            # Typing animation state
            self.briefing_lines = self.chapter.get('briefing', [])
            self.current_line = 0
            self.char_index = 0
            self.typing_speed = 2  # chars per update
            self.line_complete = False
        
        self.blink_timer = 0

    def update(self):
        self.blink_timer = (self.blink_timer + 1) % 60
        
        # Typing animation
        if self.state == "BRIEFING" and self.current_line < len(self.briefing_lines):
            if not self.line_complete:
                self.char_index += self.typing_speed
                if self.char_index >= len(self.briefing_lines[self.current_line]):
                    self.char_index = len(self.briefing_lines[self.current_line])
                    self.line_complete = True

    def draw(self, surface):
        r = self.game.renderer
        theme = r.get_theme()
        surface.fill(theme["bg"])
        
        if self.state == "COMPLETE":
            self._draw_complete(surface, r, theme)
        else:
            self._draw_briefing(surface, r, theme)

    def _draw_complete(self, surface, r, theme):
        r.draw_panel(surface, 200, 150, 600, 350, "CAMPAIGN_COMPLETE")
        
        # Victory ASCII
        victory_art = [
            "  ╔═══════════════════════╗",
            "  ║   MISSION SUCCESS     ║",
            "  ║     ★ ★ ★ ★ ★        ║",
            "  ║  THE NETWORK IS SAFE  ║",
            "  ╚═══════════════════════╝"
        ]
        
        y = 200
        for line in victory_art:
            r.draw_text(surface, line, 300, y, theme["primary"])
            y += 25
        
        r.draw_text(surface, "All chapters completed.", 350, 400, theme["secondary"])
        r.draw_text(surface, "[ENTER] Return to Menu", 360, 460, (100, 100, 100))

    def _draw_briefing(self, surface, r, theme):
        # Header
        r.draw_text(surface, f"◉ {self.campaign['title']} ◉", 50, 25, theme["primary"], r.big_font)
        
        # Chapter info
        ch_text = f"CHAPTER {self.current_idx + 1}/{len(self.chapters)}: {self.chapter.get('title', '')}"
        r.draw_text(surface, ch_text, 50, 70, theme["secondary"])
        
        if self.chapter.get('subtitle'):
            r.draw_text(surface, self.chapter['subtitle'], 50, 95, (120, 120, 120))
        
        # ASCII Art panel (animated pulse)
        art = self.chapter.get('art', [])
        if art:
            art_x = 650
            art_y = 130
            
            # Pulse effect
            pulse = 1.0 if (self.blink_timer // 15) % 2 == 0 else 0.8
            art_color = tuple(int(c * pulse) for c in theme["primary"])
            
            r.draw_panel(surface, art_x - 20, art_y - 20, 320, len(art) * 22 + 40, "VISUAL")
            
            for i, line in enumerate(art):
                r.draw_text(surface, line, art_x, art_y + i * 22, art_color)
        
        # Dialogue panel - wider for text
        r.draw_panel(surface, 40, 130, 560, 310, "TRANSMISSION")
        
        y = 155
        max_y = 420  # Don't exceed panel bottom
        for i, line in enumerate(self.briefing_lines):
            if y > max_y:
                break
            if i < self.current_line:
                display = line
            elif i == self.current_line:
                display = line[:self.char_index]
            else:
                continue
            
            # Color by speaker
            color = theme["text"]
            if line.startswith("CIPHER:"):
                color = theme["primary"]
            elif line.startswith("NEXUS:"):
                color = (100, 200, 255)
            elif line.startswith("VORTEX:"):
                color = theme["error"]
            elif line.startswith("AGENT:"):
                color = theme["secondary"]
            
            # Word wrap - tighter width
            wrapped = r.wrap_text(display, 42)
            for wline in wrapped:
                if y > max_y:
                    break
                r.draw_text(surface, wline, 55, y, color)
                y += 22
            y += 4
        
        # Typing cursor
        if self.current_line < len(self.briefing_lines) and self.blink_timer < 30:
            r.draw_text(surface, "█", 60 + len(self.briefing_lines[self.current_line][:self.char_index]) * 10, y - 32, theme["text"])
        
        # Objective
        r.draw_panel(surface, 40, 470, 580, 80, "OBJECTIVE")
        obj = self.chapter.get('objective', 'Complete the mission.')
        r.draw_text(surface, obj, 60, 495, theme["text"])
        
        # Difficulty badge
        diff = self.chapter.get('difficulty', 'MEDIUM')
        diff_color = theme["error"] if diff in ["HARD", "EXTREME"] else theme["secondary"]
        r.draw_text(surface, f"DIFFICULTY: {diff}", 650, 500, diff_color)
        
        # Controls
        r.draw_text(surface, "[SPACE] Skip Text  [ENTER] Start  [N] Skip Chapter  [ESC] Back", 50, 700, (80, 80, 80))

    def handle_input(self, event):
        if event.type != pygame.KEYDOWN:
            return
        
        if event.key == pygame.K_ESCAPE:
            self.play_sfx("back")
            from scenes.menu_scenes import TitleScene
            self.game.scene_manager.switch_to(TitleScene)
        
        elif event.key == pygame.K_SPACE:
            # Skip to next line or complete current line
            if self.state == "BRIEFING":
                if not self.line_complete:
                    self.char_index = len(self.briefing_lines[self.current_line])
                    self.line_complete = True
                elif self.current_line < len(self.briefing_lines) - 1:
                    self.current_line += 1
                    self.char_index = 0
                    self.line_complete = False
        
        elif event.key == pygame.K_RETURN:
            if self.state == "COMPLETE":
                from scenes.menu_scenes import TitleScene
                self.game.scene_manager.switch_to(TitleScene)
            else:
                self.play_sfx("accept")
                from scenes.game_scene import GameScene
                self.game.scene_manager.switch_to(GameScene, {
                    'song': self.chapter.get('song', ''),
                    'difficulty': self.chapter.get('difficulty', 'MEDIUM'),
                    'mode': 'story',
                    'next_scene_class': StoryScene,
                    'next_scene_params': {
                        'campaign': self.campaign,
                        'index': self.current_idx + 1
                    }
                })
        
        elif event.key == pygame.K_n:
            # Skip chapter
            if self.state == "BRIEFING":
                self.play_sfx("blip")
                self.current_idx += 1
                if self.current_idx >= len(self.chapters):
                    self.state = "COMPLETE"
                else:
                    self.chapter = self.chapters[self.current_idx]
                    self.briefing_lines = self.chapter.get('briefing', [])
                    self.current_line = 0
                    self.char_index = 0
                    self.line_complete = False
