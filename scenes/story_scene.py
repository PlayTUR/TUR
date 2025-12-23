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
            self.victory_lines = self.campaign.get('victory_text', [
                "MISSION COMPLETE.",
                "THE NETWORK IS SECURE."
            ])
        else:
            self.state = "BRIEFING"
            self.chapter = self.chapters[self.current_idx]
<<<<<<< HEAD
            
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
=======
        
        # Animation state
        self.briefing_line = 0
        self.char_index = 0
        self.line_timer = 0
        self.typing_speed = 2  # chars per frame
        self.line_delay = 30   # frames between lines

    def update(self):
        # Animate briefing text
        if self.state == "BRIEFING" and hasattr(self, 'chapter'):
            briefing = self.chapter.get('briefing', [])
            if self.briefing_line < len(briefing):
                current_text = briefing[self.briefing_line]
                if self.char_index < len(current_text):
                    self.char_index += self.typing_speed
                else:
                    self.line_timer += 1
                    if self.line_timer >= self.line_delay:
                        self.briefing_line += 1
                        self.char_index = 0
                        self.line_timer = 0

    def draw(self, surface):
        theme = self.game.renderer.get_theme()
        surface.fill(theme["bg"])
        
        if self.state == "COMPLETE":
            self._draw_victory(surface, theme)
            return
        
        self._draw_briefing(surface, theme)

    def _draw_victory(self, surface, theme):
        """Draw campaign complete screen"""
        # Title
        self.game.renderer.draw_text(surface, "◉ OPERATION COMPLETE ◉", 
                                      280, 80, theme["primary"], self.game.renderer.big_font)
        
        # Victory box
        box_x, box_y = 100, 180
        box_w, box_h = 820, 350
        pygame.draw.rect(surface, theme["grid"], (box_x, box_y, box_w, box_h), 2)
        pygame.draw.rect(surface, theme["grid"], (box_x, box_y-30, box_w, 30))
        self.game.renderer.draw_text(surface, "TRANSMISSION_LOG", box_x+10, box_y-25, theme["text"])
        
        # Victory text
        y = box_y + 40
        for line in self.victory_lines:
            color = theme["secondary"] if ":" in line else theme["text"]
            if line.startswith("NEXUS"):
                color = (100, 200, 255)
            elif line.startswith("CIPHER"):
                color = theme["primary"]
            self.game.renderer.draw_text(surface, f"> {line}", box_x + 30, y, color)
            y += 40
        
        # Stats hint
        self.game.renderer.draw_text(surface, "You have completed all chapters.", 
                                      box_x + 30, box_y + box_h - 60, (150, 150, 150))
        
        self.game.renderer.draw_text(surface, "[ESC] RETURN TO MENU", 350, 600, theme["secondary"])

    def _draw_briefing(self, surface, theme):
        """Draw chapter briefing screen"""
        # Header
        self.game.renderer.draw_text(surface, f"◉ {self.campaign['title']} ◉", 
                                      50, 30, theme["primary"], self.game.renderer.big_font)
        self.game.renderer.draw_text(surface, 
                                      f"CHAPTER {self.current_idx + 1} / {len(self.chapters)}: {self.chapter['title']}", 
                                      50, 80, theme["secondary"])
        
        if self.chapter.get('subtitle'):
            self.game.renderer.draw_text(surface, self.chapter['subtitle'], 
                                          50, 110, (150, 150, 150))
        
        # Mission briefing box
        box_x, box_y = 40, 150
        box_w, box_h = 600, 320
        pygame.draw.rect(surface, theme["grid"], (box_x, box_y, box_w, box_h), 2)
        pygame.draw.rect(surface, theme["grid"], (box_x, box_y-30, box_w, 30))
        self.game.renderer.draw_text(surface, "MISSION_BRIEFING", box_x+10, box_y-25, theme["text"])
        
        # Briefing lines with typing effect
        briefing = self.chapter.get('briefing', [self.chapter.get('text', '')])
        y = box_y + 25
        
        for i, line in enumerate(briefing):
            if i < self.briefing_line:
                # Completed line
                display_text = line
            elif i == self.briefing_line:
                # Currently typing line
                display_text = line[:self.char_index]
            else:
                # Not yet shown
                continue
            
            # Color based on speaker
            color = theme["text"]
            if line.startswith("CIPHER:"):
                color = theme["primary"]
            elif line.startswith("NEXUS:"):
                color = (100, 200, 255)
            elif line.startswith("VORTEX:"):
                color = theme["error"]
            
            # Word wrap for long lines using renderer helper
            wrapped = self.game.renderer.wrap_text(display_text, 52)
            for wrap_line in wrapped:
                self.game.renderer.draw_text(surface, wrap_line, box_x + 20, y, color)
                y += 26
            y += 4  # Extra space between speakers
        
        # ASCII Art panel
        art = self.chapter.get('art', [])
        if art:
            art_x = 680
            art_y = 160
            pygame.draw.rect(surface, theme["grid"], (art_x - 15, art_y - 15, 280, len(art) * 18 + 30), 1)
            for i, line in enumerate(art):
                self.game.renderer.draw_text(surface, line, art_x, art_y + i * 18, 
                                              theme["primary"], self.game.renderer.font)
        
        # Objective with word wrapping
        obj_y = box_y + box_h + 20
        self.game.renderer.draw_text(surface, "OBJECTIVE:", 50, obj_y, theme["secondary"])
        obj_text = self.chapter.get('objective', 'Unknown')
        self.game.renderer.draw_wrapped_text(surface, obj_text, 170, obj_y, 60, theme["text"])
        
        # Difficulty badge
        diff = self.chapter['difficulty']
        diff_colors = {
            "EASY": (100, 255, 100),
            "MEDIUM": (255, 200, 0),
            "HARD": (255, 100, 50),
            "EXTREME": (255, 50, 50),
        }
        diff_color = diff_colors.get(diff, theme["text"])
        self.game.renderer.draw_text(surface, f"DIFFICULTY: {diff}", 50, obj_y + 35, diff_color)
        
        # Song path (display friendly name)
        song_display = self.chapter.get('song', 'Unknown')
        if '/' in song_display:
            song_display = song_display.split('/')[-1]
        self.game.renderer.draw_text(surface, f"TRACK: {song_display}", 300, obj_y + 35, (120, 120, 120))
        
        # Controls
        self.game.renderer.draw_text(surface, "[ENTER] COMMENCE OPERATION", 50, 620, theme["primary"])
        self.game.renderer.draw_text(surface, "[ESC] ABORT MISSION", 450, 620, (150, 100, 100))
        
        # Skip hint if not all text shown
        briefing = self.chapter.get('briefing', [])
        if self.briefing_line < len(briefing):
            self.game.renderer.draw_text(surface, "[SPACE] SKIP", 750, 620, (80, 80, 80))
>>>>>>> 0dc16cc (use code wyind in the fortnite item shop)

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
<<<<<<< HEAD
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
=======
                
            elif event.key == pygame.K_SPACE:
                # Skip typing animation
                if self.state == "BRIEFING":
                    briefing = self.chapter.get('briefing', [])
                    self.briefing_line = len(briefing)
                    self.char_index = 100
                
            elif event.key == pygame.K_RETURN:
                if self.state == "BRIEFING":
                    self.play_sfx("accept")
                    
                    next_params = {
                        'campaign': self.campaign,
                        'index': self.current_idx + 1
                    }
                    
                    params = {
                        'song': self.chapter['song'],
                        'difficulty': self.chapter['difficulty'],
                        'mode': 'story',
                        'next_scene_class': StoryScene,
                        'next_scene_params': next_params
                    }
                    
                    self.game.scene_manager.switch_to(GameScene, params)
                    
                elif self.state == "COMPLETE":
                    from scenes.menu_scenes import TitleScene
                    self.game.scene_manager.switch_to(TitleScene)
>>>>>>> 0dc16cc (use code wyind in the fortnite item shop)
