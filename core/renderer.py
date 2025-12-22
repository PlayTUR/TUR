import pygame
import os
import sys
from core.config import *

class PygameRenderer:
    # Renamed from CursesRenderer to reflect V8 engine
    def __init__(self, ref_w=1024, ref_h=768):
        self.ref_w = ref_w
        self.ref_h = ref_h
        
        # Resource Helper
        def resource_path(relative_path):
            """ Get absolute path to resource, works for dev and for PyInstaller """
            if hasattr(sys, '_MEIPASS'):
                return os.path.join(sys._MEIPASS, relative_path)
            return os.path.join(os.path.abspath("."), relative_path)
        
        # Fonts
        # Try finding a retro font, else monospace
        self.font_path = resource_path(os.path.join("assets", "font.ttf"))
        if os.path.exists(self.font_path):
             self.font = pygame.font.Font(self.font_path, 20)
             self.big_font = pygame.font.Font(self.font_path, 40)
        else:
             # Try common pixel fonts if available or standard monospace
             # 'pressstart2p', 'vt323', 'monospace', 'couriernew'
             self.font = pygame.font.SysFont("monospace", 20, bold=True)
             self.big_font = pygame.font.SysFont("monospace", 40, bold=True)
        
        # ASCII Font (Smaller for the logo)
        if os.path.exists(self.font_path):
             self.ascii_font = pygame.font.Font(self.font_path, 14)
        else:
             self.ascii_font = pygame.font.SysFont("monospace", 14, bold=True)
             
        # Cache key states
        self.key_states = [False] * 4
        
        # Visual Effects
        self.effects = []
        
        # Font Cache for CJK/Localization
        self.fonts = {
            "default": self.font,
            "big_default": self.big_font,
            "ascii": self.ascii_font
        }
        self.last_lang = None

    def _get_localized_fonts(self):
        """Get appropriate fonts for current language"""
        lang = "EN"
        if hasattr(self, 'game') and self.game:
            lang = self.game.settings.get("language")
        
        if lang == self.last_lang:
            return self.fonts["current_font"], self.fonts["current_big_font"]
        
        self.last_lang = lang
        
        # Default fallback
        f = self.fonts["default"]
        bf = self.fonts["big_default"]
        
        if lang == "JP":
            # Try to find a CJK font
            cjk_candidates = ["notosanscjkjp", "notosansgothic", "notosanscjksc", "takaoexgothic", "msgothic"]
            all_fonts = pygame.font.get_fonts()
            
            for candidate in cjk_candidates:
                if candidate in all_fonts:
                    try:
                        f = pygame.font.SysFont(candidate, 20, bold=True)
                        bf = pygame.font.SysFont(candidate, 40, bold=True)
                        break
                    except: continue
        
        self.fonts["current_font"] = f
        self.fonts["current_big_font"] = bf
        return f, bf

    def update_dimensions(self):
        # Window resize logic if needed, simplified for fixed res
        pass

    def clear(self):
        # Main loop handles fill
        pass

    def present(self):
        # Main loop handles flip
        pass

    def update_effects(self):
        # Update particles/text
        alive = []
        for e in self.effects:
            e['x'] += e.get('vx', 0)
            e['y'] += e.get('vy', 0)
            e['life'] -= 1
            if e['life'] > 0:
                alive.append(e)
        self.effects = alive

    def draw_text(self, surface, text, x, y, color=(255, 255, 255), font=None):
        if not font:
            f, bf = self._get_localized_fonts()
            font = f
            # If someone passed font=renderer.big_font, we should probably handle it?
            # But usually they pass renderer.big_font directly.
            # Let's check for equality to our cached defaults.
            # Actually, better to just check if it's big_default.
            
        if font == self.fonts["big_default"]:
             _, bf = self._get_localized_fonts()
             font = bf
        elif font == self.fonts["ascii"]:
             pass # ASCII font stays same
             
        if not surface: return
        surf = font.render(str(text), False, color)
        surface.blit(surf, (x, y))

    def get_theme(self):
        try:
            name = self.game.settings.get("theme")
        except (AttributeError, Exception):
            name = "TERMINAL"
        return THEMES.get(name, THEMES["TERMINAL"])

    # === Text Wrapping Helpers ===
    
    def wrap_text(self, text, max_chars=60):
        """Word-wrap text to max characters per line"""
        words = text.split(' ')
        lines = []
        current = ""
        for word in words:
            if len(current) + len(word) + 1 <= max_chars:
                current += (" " if current else "") + word
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines
    
    def draw_wrapped_text(self, surface, text, x, y, max_chars=60, color=None, line_height=25):
        """Draw text with automatic word wrapping. Returns final y position."""
        theme = self.get_theme()
        if color is None:
            color = theme["text"]
        lines = self.wrap_text(text, max_chars)
        for i, line in enumerate(lines):
            self.draw_text(surface, line, x, y + i * line_height, color)
        return y + len(lines) * line_height
    
    def draw_panel(self, surface, x, y, w, h, title=None):
        """Draw a themed window panel with optional title bar"""
        theme = self.get_theme()
        pygame.draw.rect(surface, theme["bg"], (x, y, w, h))
        pygame.draw.rect(surface, theme["grid"], (x, y, w, h), 2)
        if title:
            pygame.draw.rect(surface, theme["grid"], (x, y - 28, w, 28))
            self.draw_text(surface, title, x + 10, y - 23, theme["text"])
        return x, y
    
    def draw_button(self, surface, text, x, y, selected=False, width=200):
        """Draw a styled button/menu item"""
        theme = self.get_theme()
        h = 35
        if selected:
            pygame.draw.rect(surface, theme["grid"], (x, y, width, h))
            pygame.draw.rect(surface, theme["primary"], (x, y, width, h), 2)
            self.draw_text(surface, f"> {text}", x + 10, y + 8, theme["primary"])
        else:
            pygame.draw.rect(surface, theme["bg"], (x, y, width, h))
            pygame.draw.rect(surface, theme["grid"], (x, y, width, h), 1)
            self.draw_text(surface, f"  {text}", x + 10, y + 8, theme["text"])
        return h + 5
    
    def draw_input_field(self, surface, label, value, x, y, width=300, focused=False):
        """Draw a text input field"""
        theme = self.get_theme()
        self.draw_text(surface, label, x, y, theme["secondary"])
        border = theme["primary"] if focused else theme["grid"]
        pygame.draw.rect(surface, (20, 20, 20), (x, y + 25, width, 30))
        pygame.draw.rect(surface, border, (x, y + 25, width, 30), 2)
        display = value + ("_" if focused else "")
        self.draw_text(surface, display, x + 8, y + 31, theme["text"])
        return 60

    def draw_lanes(self, surface, upscroll=False, pulse=0.0):
        theme = self.get_theme()
        
        # Draw 4 Lanes
        center_x = self.ref_w // 2
        lane_w = 100 # Pixels
        start_x = center_x - (lane_w * 2)
        
        # Dynamic Background Pulse
        bg_col = list(theme["bg"])
        # Add pulse to primary component?
        # Let's just boost G if green, R if Red... simple boost to G for now as basic lighting
        if pulse > 0:
            bg_col[1] = min(255, int(bg_col[1] + 20 * pulse))
            
        pygame.draw.rect(surface, bg_col, (start_x, 0, lane_w * 4, self.ref_h))
        
        # Lane Dividers
        grid_col = theme["grid"]
        for i in range(5):
            x = start_x + i * lane_w
            pygame.draw.line(surface, grid_col, (x, 0), (x, self.ref_h), 2)
            
        # Receptor Line
        hit_y = int(self.ref_h * (0.15 if upscroll else 0.85))
        thick = 4 + int(2 * pulse)
        # Receptor color usually primary
        pygame.draw.line(surface, theme["primary"], (start_x, hit_y), (start_x + lane_w * 4, hit_y), thick)
        
        # Key receptors
        note_shape = self.game.settings.get("note_shape") or "BAR"
        for i in range(4):
            x = start_x + i * lane_w
            cx = x + lane_w // 2
            
            if note_shape == "CIRCLE":
                if self.key_states[i]:
                    self._draw_circle_receptor(surface, cx, hit_y, theme["primary"], True)
                else:
                    self._draw_circle_receptor(surface, cx, hit_y, grid_col, False)
            elif note_shape == "ARROW":
                if self.key_states[i]:
                    self._draw_arrow_receptor(surface, cx, hit_y, i, theme["primary"], True, upscroll)
                else:
                    self._draw_arrow_receptor(surface, cx, hit_y, i, grid_col, False, upscroll)
            else: # BAR
                h = 24
                rect = pygame.Rect(x + 10, hit_y - h//2, lane_w - 20, h)
                if self.key_states[i]:
                    pygame.draw.rect(surface, theme["primary"], rect)
                else:
                    pygame.draw.rect(surface, grid_col, rect, 2)

    def draw_progress(self, surface, current, total):
        theme = self.get_theme()
        if total <= 0: return
        pct = min(1.0, current / total)
        
        h = 10
        y = self.ref_h - h if not False else 0 # Bottom usually
        
        # Background
        pygame.draw.rect(surface, theme["bg"], (0, y, self.ref_w, h))
        # Fill
        pygame.draw.rect(surface, theme["primary"], (0, y, int(self.ref_w * pct), h))

    # (draw_notes kept mostly same, as it uses Settings for specific colors)
    # Actually wait, draw_notes uses note_col_1. 
    # Maybe switching theme should UPDATE note_col_1 in settings?
    # I'll handle that in SettingsScene.

    def draw_notes(self, surface, notes, song_time, scroll_speed, upscroll=False):
        theme = self.get_theme()
        
        center_x = self.ref_w // 2
        lane_w = 100
        start_x = center_x - (lane_w * 2)
        hit_y = int(self.ref_h * (0.15 if upscroll else 0.85))
        
        c1 = self.game.settings.get("note_col_1")
        c2 = self.game.settings.get("note_col_2")
        note_shape = self.game.settings.get("note_shape") or "BAR"
        show_ends = self.game.settings.get("show_hold_ends")
        
        max_dist = self.ref_h + 100
        
        for note in notes:
            t_diff = note['time'] - song_time
            length = note.get('length', 0)
            dist = t_diff * scroll_speed
            
            if upscroll:
                y = hit_y + dist
            else:
                y = hit_y - dist

            # Culling logic:
            # If hit, we still draw if it's a hold note and hasn't finished
            if note.get('hit'):
                if length > 0:
                    # If it's a hold, check if tail hasn't passed hit_y
                    if upscroll:
                        # In upscroll, tail is at y_tail = y + tail_pixels
                        # It passes when y_tail < hit_y
                        if (y + (length * scroll_speed)) < hit_y: continue
                    else:
                        # In downscroll, tail is at y_tail = y - tail_pixels
                        # It passes when y_tail > hit_y
                        if (y - (length * scroll_speed)) > hit_y: continue
                else:
                    continue # Regular note hit, disappear
            
            # For culling, use end time if it's a hold note
            end_t_diff = t_diff + length
            if end_t_diff < -0.3: continue # Only skip if the TAIL has passed
            
            if dist > max_dist: continue
                
            lane = note['lane']
            x = start_x + lane * lane_w
            cx = x + lane_w // 2
            
            color = c1 if lane in [1, 2] else c2
            dark_color = tuple(max(0, c - 60) for c in color)
            
            # Draw hold note body
            if length > 0:
                tail_pixels = int(length * scroll_speed)
                if upscroll:
                    tail_end = y + tail_pixels # Tail follows BELOW head
                else:
                    tail_end = y - tail_pixels # Tail follows ABOVE head
                
                # Determine body rect points
                if upscroll:
                    top_y = y
                    bottom_y = tail_end
                else:
                    top_y = tail_end
                    bottom_y = y
                
                # Styled Body Rendering
                if note_shape == "CIRCLE":
                    b_w = 20
                    body_rect = pygame.Rect(cx - b_w//2, int(min(y, tail_end)), b_w, int(abs(y - tail_end)))
                    pygame.draw.rect(surface, dark_color, body_rect)
                    pygame.draw.line(surface, color, (cx, int(y)), (cx, int(tail_end)), 4)
                elif note_shape == "ARROW":
                    b_w = 30
                    body_rect = pygame.Rect(cx - b_w//2, int(min(y, tail_end)), b_w, int(abs(y - tail_end)))
                    pygame.draw.rect(surface, dark_color, body_rect)
                    pygame.draw.rect(surface, color, body_rect, 2)
                    pygame.draw.line(surface, color, (cx, int(y)), (cx, int(tail_end)), 2)
                else: 
                    b_w = lane_w - 40
                    body_rect = pygame.Rect(cx - b_w//2, int(min(y, tail_end)), b_w, int(abs(y - tail_end)))
                    pygame.draw.rect(surface, dark_color, body_rect)
                    pygame.draw.rect(surface, color, body_rect, 2)
                    pygame.draw.line(surface, color, (cx, int(y)), (cx, int(tail_end)), 3)
                
                # End marker (TAIL) styling
                if show_ends:
                    if note_shape == "CIRCLE":
                        self._draw_circle_note(surface, cx, int(tail_end), color, False, size=15)
                    elif note_shape == "ARROW":
                        t_sz = 20
                        t_rect = pygame.Rect(cx - t_sz//2, int(tail_end) - 5, t_sz, 10)
                        pygame.draw.rect(surface, dark_color, t_rect)
                        pygame.draw.rect(surface, color, t_rect, 2)
                    else:
                        t_h = 10
                        t_rect = pygame.Rect(x + 15, int(tail_end) - t_h//2, lane_w - 30, t_h)
                        pygame.draw.rect(surface, dark_color, t_rect)
                        pygame.draw.rect(surface, color, t_rect, 1)
            
            # Draw note HEAD 
            # If hit_y is within the hold duration, stick the head to hit_y
            head_y = y
            is_active_hold = (length > 0 and t_diff <= 0 and end_t_diff > 0)
            if is_active_hold:
                head_y = hit_y
            
            # Draw the head (unless it's a hold that already fully passed hit_y)
            show_head = True
            if note.get('hit') and not is_active_hold:
                 show_head = False
            
            if show_head:
                if note_shape == "ARROW":
                    self._draw_arrow_note(surface, cx, int(head_y), lane, color, upscroll)
                elif note_shape == "CIRCLE":
                    self._draw_circle_note(surface, cx, int(head_y), color, length > 0)
                else:
                    self._draw_bar_note(surface, x, int(head_y), lane_w, color, length > 0)
    
    def _draw_bar_note(self, surface, x, y, lane_w, color, is_long=False):
        """Draw bar-style note (8-bit styled)"""
        rect = pygame.Rect(x + 5, y - 15, lane_w - 10, 30)
        pygame.draw.rect(surface, color, rect)
        pygame.draw.rect(surface, (255, 255, 255), rect, 2)
        # Center line
        pygame.draw.line(surface, (0, 0, 0), (x+5, y), (x+lane_w-5, y), 2)
        if is_long:
            pygame.draw.rect(surface, (255, 255, 255), 
                pygame.Rect(x + 30, y - 5, lane_w - 60, 10))
    
    def _draw_arrow_note(self, surface, cx, y, lane, color, upscroll):
        """Draw 8-bit arrow-style note pointing in lane direction"""
        size = 40  # Same visual size as bar
        half = size // 2
        
        # 8-bit style arrows using rectangles (pixelated look)
        # Lane 0: Left, Lane 1: Down, Lane 2: Up, Lane 3: Right
        dark_color = tuple(max(0, c - 60) for c in color)
        
        if lane == 0:  # Left arrow
            # Arrow body
            pygame.draw.rect(surface, color, (cx - 10, y - 8, 30, 16))
            # Arrow tip (triangular using rects)
            pygame.draw.rect(surface, color, (cx - 20, y - 4, 10, 8))
            pygame.draw.rect(surface, color, (cx - 30, y - 2, 10, 4))
            pygame.draw.rect(surface, (255, 255, 255), (cx - 30, y - 8, 50, 16), 2)
        elif lane == 1:  # Down arrow
            pygame.draw.rect(surface, color, (cx - 8, y - 20, 16, 30))
            pygame.draw.rect(surface, color, (cx - 16, y + 5, 32, 8))
            pygame.draw.rect(surface, color, (cx - 8, y + 13, 16, 6))
            pygame.draw.rect(surface, (255, 255, 255), (cx - 16, y - 20, 32, 40), 2)
        elif lane == 2:  # Up arrow
            pygame.draw.rect(surface, color, (cx - 8, y - 10, 16, 30))
            pygame.draw.rect(surface, color, (cx - 16, y - 13, 32, 8))
            pygame.draw.rect(surface, color, (cx - 8, y - 19, 16, 6))
            pygame.draw.rect(surface, (255, 255, 255), (cx - 16, y - 20, 32, 40), 2)
        else:  # Right arrow (lane 3)
            pygame.draw.rect(surface, color, (cx - 20, y - 8, 30, 16))
            pygame.draw.rect(surface, color, (cx + 10, y - 4, 10, 8))
            pygame.draw.rect(surface, color, (cx + 20, y - 2, 10, 4))
            pygame.draw.rect(surface, (255, 255, 255), (cx - 20, y - 8, 50, 16), 2)
    
    def _draw_circle_receptor(self, surface, cx, y, color, active):
        """Draw 8-bit circle-style receptor"""
        size = 32
        points = []
        import math
        for i in range(8):
            angle = i * math.pi / 4 - math.pi / 8
            px = cx + int(size * math.cos(angle))
            py = y + int(size * math.sin(angle))
            points.append((px, py))
        
        if active:
            pygame.draw.polygon(surface, color, points)
            pygame.draw.polygon(surface, (255, 255, 255), points, 2)
        else:
            pygame.draw.polygon(surface, color, points, 2)
            
    def _draw_arrow_receptor(self, surface, cx, y, lane, color, active, upscroll=False):
        """Draw 8-bit arrow-style receptor outline"""
        size = 40
        import math
        
        # Draw a hollow pixelated arrow
        # We'll use the same logic as _draw_arrow_note but as an outline
        if active:
            self._draw_arrow_note(surface, cx, y, lane, color, upscroll)
        else:
            # Hollow outline
            # Left: 0, Down: 1, Up: 2, Right: 3
            if lane == 0: # Left
                pts = [(cx+15, y-10), (cx-5, y-10), (cx-5, y-20), (cx-25, y), (cx-5, y+20), (cx-5, y+10), (cx+15, y+10)]
            elif lane == 1: # Down
                pts = [(cx-10, y-15), (cx-10, y+5), (cx-20, y+5), (cx, y+25), (cx+20, y+5), (cx+10, y+5), (cx+10, y-15)]
            elif lane == 2: # Up
                pts = [(cx-10, y+15), (cx-10, y-5), (cx-20, y-5), (cx, y-25), (cx+20, y-5), (cx+10, y-5), (cx+10, y+15)]
            else: # Right
                pts = [(cx-15, y-10), (cx+5, y-10), (cx+5, y-20), (cx+25, y), (cx+5, y+20), (cx+5, y+10), (cx-15, y+10)]
            
            pygame.draw.polygon(surface, color, pts, 2)

    def _draw_circle_note(self, surface, cx, y, color, is_long=False, size=28):
        """Draw 8-bit circle-style note (octagon for pixelated look)"""
        dark_color = tuple(max(0, c - 60) for c in color)
        
        # Draw as octagon (8-sided) for 8-bit feel
        points = []
        import math
        for i in range(8):
            angle = i * math.pi / 4 - math.pi / 8
            px = cx + int(size * math.cos(angle))
            py = y + int(size * math.sin(angle))
            points.append((px, py))
        
        pygame.draw.polygon(surface, color, points)
        pygame.draw.polygon(surface, (255, 255, 255), points, 2 if size < 20 else 3)
        
        # Inner octagon
        if size > 15:
            inner_points = []
            for i in range(8):
                angle = i * math.pi / 4 - math.pi / 8
                px = cx + int(size * 0.5 * math.cos(angle))
                py = y + int(size * 0.5 * math.sin(angle))
                inner_points.append((px, py))
            pygame.draw.polygon(surface, (0, 0, 0), inner_points, 2)
            
            if is_long:
                pygame.draw.polygon(surface, (255, 255, 255), inner_points)
            
    def draw_effects(self, surface):
        # Effects have their own color embedded
        for e in self.effects:
            if e['type'] == 'text':
                # Float calculation logic in update_effects, we just draw x,y
                # Alpha fade
                # Pygame font rendering with alpha is tricky without intermediate surface
                # Simple approach: standard blit.
                self.draw_text(surface, e['text'], int(e['x']), int(e['y']), e['color'])
            
            elif e['type'] == 'particle':
                 # Draw small rects
                 r = pygame.Rect(int(e['x']), int(e['y']), e['size'], e['size'])
                 pygame.draw.rect(surface, e['color'], r)

    def add_hit_effect(self, text, lane, upscroll=False, color=None):
        theme = self.get_theme()
        
        # Lane X calc:
        center_x = self.ref_w // 2
        lane_w = 100
        start_x = center_x - (lane_w * 2)
        x = start_x + lane * lane_w + lane_w // 2
        
        # Hit Line Y
        hit_y = int(self.ref_h * (0.15 if upscroll else 0.85))
        y = hit_y
        
        # Color Logic
        col = color if color else theme["primary"]
        if text == "MISS": col = theme["error"]
        
        # Add Text Effect
        # For text, we center it.
        # estimate width
        txt_w = len(text) * 15 
        
        self.effects.append({
            'type': 'text',
            'x': x - txt_w // 2,
            'y': y - 40 if not upscroll else y + 20,
            'vx': 0,
            'vy': -1 if not upscroll else 1, # Float away from receptor
            'life': 40,
            'text': text,
            'color': col
        })
        
        # Add Pixel Explosion
        import random
        count = 8 if text == "PERFECT" else 4
        if text == "MISS": count = 2
        
        for _ in range(count):
            size = random.randint(4, 10)
            vx = random.uniform(-6, 6) 
            # Particles should explode OUTWARDS from hit line.
            # If downscroll (hit bottom), they should fly UP (-vy) mostly?
            # Or just fountain? Fountain is nice.
            vy = random.uniform(-10, -2) if not upscroll else random.uniform(2, 10)
            
            self.effects.append({
                'type': 'particle',
                'x': x + random.randint(-20, 20),
                'y': y,
                'vx': vx,
                'vy': vy,
                'life': random.randint(20, 40),
                'color': col,
                'size': size
            })
