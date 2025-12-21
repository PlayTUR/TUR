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
             
        # Cache key states
        self.key_states = [False] * 4
        
        # Visual Effects
        self.effects = []

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
        if not font: font = self.font
        if not surface: return # Should not happen in pure pygame mode unless bug
        
        # TUI Look: Drop shadow?
        # shadow = font.render(str(text), False, (0, 50, 0))
        # surface.blit(shadow, (x+2, y+2))
        
        # AA = False for pixelated look
        surf = font.render(str(text), False, color)
        surface.blit(surf, (x, y))

    def get_theme(self):
        name = self.game.settings.get("theme")
        return THEMES.get(name, THEMES["TERMINAL"])

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
        for i in range(4):
            x = start_x + i * lane_w
            rect = pygame.Rect(x + 10, hit_y - 20, lane_w - 20, 40)
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
        
        # Dimensions
        center_x = self.ref_w // 2
        lane_w = 100
        start_x = center_x - (lane_w * 2)
        
        # Hit Line Y
        hit_y = int(self.ref_h * (0.15 if upscroll else 0.85))
        
        # Note Colors (from Settings)
        c1 = self.game.settings.get("note_col_1") # Inner
        c2 = self.game.settings.get("note_col_2") # Outer
        
        # Window of visibility (approx 2 screens worth)
        # speed is px/sec. 
        # Max visible time diff = height / speed
        max_dist = self.ref_h + 100
        
        for note in notes:
            if note.get('hit'): continue
            
            t_diff = note['time'] - song_time
            
            # Don't draw if too far away
            dist = t_diff * scroll_speed
            
            # If passed, don't draw (Miss logic handles hitting it)
            if t_diff < -0.2: continue 
            if dist > max_dist: continue # Too far in future
            
            # Calculate Y
            if upscroll:
                # Target is Top. Future is Below.
                y = hit_y + dist
            else:
                # Target is Bottom. Future is Above.
                y = hit_y - dist
                
            # Render Note (BAR Only)
            lane = note['lane']
            x = start_x + lane * lane_w
            
            color = c1 # Default Inner
            if lane in [0, 3]: color = c2 # Outer
            
            # Bar Shape
            rect = pygame.Rect(x + 5, int(y - 15), lane_w - 10, 30)
            
            # Basic Draw
            pygame.draw.rect(surface, color, rect)
            # Border
            pygame.draw.rect(surface, (255, 255, 255), rect, 2)
            
            # Center line for style
            pygame.draw.line(surface, (0, 0, 0), (x+5, int(y)), (x+lane_w-5, int(y)), 2)
            
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
