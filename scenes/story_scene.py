"""
Story Scene - Campaign Briefing with Animated ASCII
Enhanced with frame-based animations, glitch effects, and dynamic visuals.
"""

import pygame
import random
import math
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
                self.campaign = {'title': 'OPERATION PHANTOM', 'chapters': []}
        
        self.current_idx = params.get('index', 0)
        self.chapters = self.campaign.get('chapters', [])
        
        if self.current_idx >= len(self.chapters):
            self.state = "COMPLETE"
            self.victory_lines = self.campaign.get('victory_text', [
                "NEXUS: VORTEX signal... terminated. All systems returning to normal.",
                "CIPHER: You did it, agent. The world will never know how close we came.",
                "NEXUS: Agent NULL... thank you. For everything.",
                "CIPHER: Take some rest. You've earned it.",
                "CIPHER: Until the next operation... CIPHER out.",
            ])
        else:
            self.state = "BRIEFING"
            self.chapter = self.chapters[self.current_idx]
            self.briefing_lines = self.chapter.get('briefing', [])
        
        # Animation state
        self.current_line = 0
        self.char_index = 0
        self.typing_speed = 2
        self.line_complete = False
        self.blink_timer = 0
        self.frame_timer = 0
        self.glitch_timer = 0
        self.scan_line_y = 0
        
        # Particle effects
        self.particles = []
        
        # Play ambient music
        try:
            if self.state == "BRIEFING":
                song = self.chapter.get('song', '')
                if song:
                    self.game.audio.load_song(song)
                    self.game.audio.set_volume(self.game.settings.get("volume") * 0.5)
                    self.game.audio.play()
        except Exception as e:
            print(f"Story music error: {e}")

    def update(self):
        self.blink_timer = (self.blink_timer + 1) % 60
        self.frame_timer = (self.frame_timer + 1) % 120
        self.glitch_timer = (self.glitch_timer + 1) % 300
        self.scan_line_y = (self.scan_line_y + 2) % 200
        
        # Update particles
        self._update_particles()
        
        # Typing animation
        if self.state == "BRIEFING" and self.current_line < len(self.briefing_lines):
            if not self.line_complete:
                self.char_index += self.typing_speed
                if self.char_index >= len(self.briefing_lines[self.current_line]):
                    self.char_index = len(self.briefing_lines[self.current_line])
                    self.line_complete = True

    def _update_particles(self):
        # Spawn particles
        if random.random() < 0.1:
            self.particles.append({
                'x': random.randint(650, 950),
                'y': random.randint(130, 350),
                'char': random.choice(['░', '▒', '▓', '·', '•']),
                'vx': random.uniform(-0.5, 0.5),
                'vy': random.uniform(-1, -0.2),
                'life': random.randint(30, 60),
                'alpha': 255
            })
        
        # Update particles
        alive = []
        for p in self.particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['life'] -= 1
            p['alpha'] = int(255 * (p['life'] / 60))
            if p['life'] > 0:
                alive.append(p)
        self.particles = alive[:50]  # Cap particles

    def draw(self, surface):
        r = self.game.renderer
        theme = r.get_theme()
        surface.fill(theme["bg"])
        
        if self.state == "COMPLETE":
            self._draw_victory(surface, r, theme)
        else:
            self._draw_briefing(surface, r, theme)

    def _draw_victory(self, surface, r, theme):
        """Draw campaign complete screen with animated effects"""
        # Animated victory ASCII
        victory_frames = [
            [
                "  ╔═══════════════════════════╗",
                "  ║     ◉ MISSION SUCCESS ◉   ║",
                "  ║      ★  ★  ★  ★  ★        ║",
                "  ║   THE NETWORK IS SECURE   ║",
                "  ║      VORTEX: TERMINATED   ║",
                "  ╚═══════════════════════════╝"
            ],
            [
                "  ╔═══════════════════════════╗",
                "  ║     ◉ MISSION SUCCESS ◉   ║",
                "  ║       ★  ★  ★  ★  ★       ║",
                "  ║   THE NETWORK IS SECURE   ║",
                "  ║      VORTEX: TERMINATED   ║",
                "  ╚═══════════════════════════╝"
            ]
        ]
        
        frame_idx = (self.frame_timer // 30) % len(victory_frames)
        art = victory_frames[frame_idx]
        
        # Rainbow pulse effect
        hue = (self.frame_timer * 3) % 360
        pulse_color = self._hsv_to_rgb(hue, 0.7, 1.0)
        
        y = 150
        for line in art:
            r.draw_text(surface, line, 280, y, pulse_color)
            y += 30
        
        # Victory text panel
        r.draw_panel(surface, 100, 350, 820, 220, "FINAL_TRANSMISSION")
        
        y = 380
        for i, line in enumerate(self.victory_lines):
            if i <= self.current_line:
                color = theme["text"]
                if "NEXUS" in line:
                    color = (100, 200, 255)
                elif "CIPHER" in line:
                    color = theme["primary"]
                r.draw_text(surface, f"> {line}", 120, y, color)
                y += 35
        
        r.draw_text(surface, "[ENTER] Return to Menu", 380, 620, theme["secondary"])

    def _draw_briefing(self, surface, r, theme):
        """Draw chapter briefing with animated ASCII"""
        # Header with glitch effect
        title = f"◉ {self.campaign['title']} ◉"
        if self.glitch_timer < 10:
            title = self._glitch_text(title)
        r.draw_text(surface, title, 50, 25, theme["primary"], r.big_font)
        
        # Chapter info
        ch_text = f"CHAPTER {self.current_idx + 1}/{len(self.chapters)}: {self.chapter.get('title', '')}"
        r.draw_text(surface, ch_text, 50, 70, theme["secondary"])
        
        if self.chapter.get('subtitle'):
            r.draw_text(surface, self.chapter['subtitle'], 50, 95, (120, 120, 120))
        
        # Animated ASCII Art panel
        self._draw_animated_art(surface, r, theme)
        
        # Draw particles
        for p in self.particles:
            alpha = max(0, min(255, p['alpha']))
            col = (*theme["primary"][:3],)
            r.draw_text(surface, p['char'], int(p['x']), int(p['y']), col)
        
        # Dialogue panel
        r.draw_panel(surface, 40, 130, 580, 330, "TRANSMISSION")
        
        y = 155
        max_y = 440
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
            color = self._get_speaker_color(line, theme)
            
            # Word wrap
            wrapped = r.wrap_text(display, 44)
            for wline in wrapped:
                if y > max_y:
                    break
                r.draw_text(surface, wline, 55, y, color)
                y += 24
            y += 6
        
        # Typing cursor
        if self.current_line < len(self.briefing_lines) and self.blink_timer < 30:
            cursor_x = 55 + min(len(self.briefing_lines[self.current_line][:self.char_index]) * 9, 500)
            r.draw_text(surface, "█", cursor_x, y - 30, theme["text"])
        
        # Objective panel
        r.draw_panel(surface, 40, 490, 580, 90, "OBJECTIVE")
        obj = self.chapter.get('objective', 'Complete the mission.')
        r.draw_text(surface, obj, 60, 520, theme["text"])
        
        # Difficulty badge
        diff = self.chapter.get('difficulty', 'MEDIUM')
        diff_colors = {
            "EASY": (100, 255, 100),
            "MEDIUM": (255, 200, 0),
            "HARD": (255, 100, 50),
            "EXTREME": (255, 50, 50),
            "FUCK YOU": (255, 0, 100),
        }
        diff_color = diff_colors.get(diff, theme["secondary"])
        r.draw_text(surface, f"DIFFICULTY: {diff}", 60, 555, diff_color)
        
        # Controls
        r.draw_text(surface, "[SPACE] Skip  [ENTER] Start  [N] Skip Chapter  [ESC] Back", 50, 700, (80, 80, 80))

    def _draw_animated_art(self, surface, r, theme):
        """Draw ASCII art with animation effects"""
        art_frames = self.chapter.get('art_frames', [self.chapter.get('art', [])])
        if not art_frames or not art_frames[0]:
            return
        
        # Select current frame
        frame_idx = (self.frame_timer // 20) % len(art_frames)
        art = art_frames[frame_idx] if frame_idx < len(art_frames) else art_frames[0]
        
        art_x = 660
        art_y = 140
        
        # Panel with scan line effect
        panel_h = len(art) * 22 + 50
        r.draw_panel(surface, art_x - 20, art_y - 20, 340, panel_h, "VISUAL_FEED")
        
        # Draw scan line
        scan_y = art_y + (self.scan_line_y % panel_h)
        pygame.draw.line(surface, (*theme["primary"], 100), 
                        (art_x - 15, scan_y), (art_x + 315, scan_y), 2)
        
        for i, line in enumerate(art):
            line_y = art_y + i * 22
            
            # Glitch effect on random lines
            if self.glitch_timer < 5 and random.random() < 0.3:
                line = self._glitch_text(line)
            
            # Pulse effect
            pulse = 0.7 + 0.3 * math.sin(self.frame_timer * 0.1 + i * 0.5)
            art_color = tuple(int(c * pulse) for c in theme["primary"])
            
            r.draw_text(surface, line, art_x, line_y, art_color)

    def _glitch_text(self, text):
        """Add glitch effect to text"""
        glitch_chars = "░▒▓█▀▄╔╗╚╝║═◉●○"
        result = list(text)
        for _ in range(random.randint(1, 3)):
            if result:
                idx = random.randint(0, len(result) - 1)
                result[idx] = random.choice(glitch_chars)
        return ''.join(result)

    def _get_speaker_color(self, line, theme):
        """Get color based on speaker"""
        if line.startswith("CIPHER:"):
            return theme["primary"]
        elif line.startswith("NEXUS:"):
            return (100, 200, 255)
        elif line.startswith("VORTEX:"):
            return theme["error"]
        elif line.startswith("ECHO:"):
            return (200, 100, 255)  # Purple for ECHO
        elif line.startswith("AGENT:") or line.startswith("PHANTOM:"):
            return theme["secondary"]
        return theme["text"]

    def _hsv_to_rgb(self, h, s, v):
        """Convert HSV to RGB"""
        h = h / 360.0
        if s == 0.0:
            return (int(v * 255), int(v * 255), int(v * 255))
        i = int(h * 6.0)
        f = (h * 6.0) - i
        p = v * (1.0 - s)
        q = v * (1.0 - s * f)
        t = v * (1.0 - s * (1.0 - f))
        i = i % 6
        if i == 0:
            return (int(v * 255), int(t * 255), int(p * 255))
        if i == 1:
            return (int(q * 255), int(v * 255), int(p * 255))
        if i == 2:
            return (int(p * 255), int(v * 255), int(t * 255))
        if i == 3:
            return (int(p * 255), int(q * 255), int(v * 255))
        if i == 4:
            return (int(t * 255), int(p * 255), int(v * 255))
        if i == 5:
            return (int(v * 255), int(p * 255), int(q * 255))
        return (255, 255, 255)

    def handle_input(self, event):
        if event.type != pygame.KEYDOWN:
            return
        
        if event.key == pygame.K_ESCAPE:
            self.play_sfx("back")
            self.game.audio.stop()
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
            elif self.state == "COMPLETE":
                if self.current_line < len(self.victory_lines) - 1:
                    self.current_line += 1
        
        elif event.key == pygame.K_RETURN:
            if self.state == "COMPLETE":
                self.game.audio.stop()
                from scenes.menu_scenes import TitleScene
                self.game.scene_manager.switch_to(TitleScene)
            else:
                self.play_sfx("accept")
                self.game.audio.stop()
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
                    self.current_line = 0
                else:
                    self.chapter = self.chapters[self.current_idx]
                    self.briefing_lines = self.chapter.get('briefing', [])
                    self.current_line = 0
                    self.char_index = 0
                    self.line_complete = False
