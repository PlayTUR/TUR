import pygame
import random
from config import *

class CRTShader:
    def __init__(self):
        self.scanline_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.scanline_surface.set_colorkey((0,0,0))
        self.scanline_surface.set_alpha(30)
        
        # Draw scanlines
        for y in range(0, SCREEN_HEIGHT, 4):
            pygame.draw.line(self.scanline_surface, (0, 0, 0), (0, y), (SCREEN_WIDTH, y), 2)
    
    def apply(self, surface):
        surface.blit(self.scanline_surface, (0, 0))

class TUIRenderer:
    def __init__(self):
        # Load a monospace font
        try:
            # Check for embedded/assets font first
            font_path = os.path.join("assets", "font.ttf")
            if os.path.exists(font_path):
                 self.font = pygame.font.Font(font_path, FONT_SIZE)
            else:
                 self.font = pygame.font.Font(pygame.font.match_font('monospace') or pygame.font.match_font('couriernew'), FONT_SIZE)
        except:
             self.font = pygame.font.SysFont("Courier", FONT_SIZE, bold=True)
            
        try:
             font_path = os.path.join("assets", "font.ttf")
             if os.path.exists(font_path):
                 self.big_font = pygame.font.Font(font_path, FONT_SIZE * 2)
             else:
                 self.big_font = pygame.font.Font(pygame.font.match_font('monospace'), FONT_SIZE * 2)
        except:
             self.big_font = pygame.font.SysFont("Courier", FONT_SIZE * 2, bold=True)
        
        self.key_states = [False] * 4
        self.crt = CRTShader()
        self.hit_animations = [] # Text explosions

    def draw_text(self, surface, text, x, y, color=TERM_GREEN, font=None):
        if font is None:
            font = self.font
        
        # Simple "Bloom" - draw slightly offset with low alpha
        glow_surf = font.render(text, True, (color[0]//3, color[1]//3, color[2]//3))
        surface.blit(glow_surf, (x-1, y))
        surface.blit(glow_surf, (x+1, y))
        surface.blit(glow_surf, (x, y-1))
        surface.blit(glow_surf, (x, y+1))
        
        # Main text
        surf = font.render(text, True, color)
        surface.blit(surf, (x, y))

    def draw_box(self, surface, x, y, w, h, title=""):
        # ASCII Box drawing
        # Top
        pygame.draw.rect(surface, BG_Dark, (x, y, w, h))
        pygame.draw.rect(surface, TERM_GREEN, (x, y, w, h), 1)
        
        if title:
            self.draw_text(surface, f"[{title}]", x + 10, y - 10, TERM_WHITE)

    def draw_notes(self, surface, notes, song_time, scroll_speed, upscroll=False):
        center_x = SCREEN_WIDTH // 2
        start_x = center_x - 200
        hit_y = SCREEN_HEIGHT - 100
        if upscroll:
            hit_y = 100
        
        for note in notes:
            if note.get('hit', False):
                continue
            
            dt = note['time'] - song_time
            if dt < -0.2 or dt > 2.0:
                continue
            
            if upscroll:
                y = hit_y + (dt * scroll_speed)
            else:
                y = hit_y - (dt * scroll_speed)
                
            lane = note['lane']
            x = start_x + lane * 100 + 35
            
            # Note Shape - Improved
            char = "{ O }" if lane in [1, 2] else "< O >"
            color = TERM_BLUE if lane in [1, 2] else TERM_RED
            
            self.draw_text(surface, char, x, y, color, self.big_font)
            
    def draw_lanes(self, surface, upscroll=False):
        center_x = SCREEN_WIDTH // 2
        total_w = 400
        start_x = center_x - 200
        hit_y = 100 if upscroll else (SCREEN_HEIGHT - 100)
        
        # ... (rest of drawing logic, adjust hit line y)
        pygame.draw.line(surface, TERM_WHITE, (start_x, hit_y), (start_x + total_w, hit_y), 2)
        
        offset_y = -30 if upscroll else 30
        text_y = hit_y - 40 if upscroll else hit_y + 10
        
        for i in range(4):
            x = start_x + i * 100
            pygame.draw.line(surface, (30, 60, 30), (x, 0), (x, SCREEN_HEIGHT))
            
            # Receptors
            rx = x + 35
            rect_char = "[ ]"
            color = TERM_GREEN
            
            if self.key_states[i]:
                rect_char = "[#]"
                color = TERM_WHITE
                # Beam
                s = pygame.Surface((100, SCREEN_HEIGHT), pygame.SRCALPHA)
                s.fill((0, 50, 0, 100))
                surface.blit(s, (x, 0))
            
            self.draw_text(surface, rect_char, rx, hit_y - 10, color, self.big_font)

    def add_hit_effect(self, text, lane=None):
        self.hit_animations.append({
            'text': text,
            'x': SCREEN_WIDTH // 2 if lane is None else (SCREEN_WIDTH//2 - 200 + lane*100 + 50),
            'y': SCREEN_HEIGHT - 150,
            'life': 1.0,
            'color': TERM_AMBER
        })

    def update_effects(self):
        for h in self.hit_animations:
            h['y'] -= 2
            h['life'] -= 0.05
        self.hit_animations = [h for h in self.hit_animations if h['life'] > 0]

    def draw_effects(self, surface):
        for h in self.hit_animations:
            col = (
                min(255, int(h['color'][0] * h['life'])),
                min(255, int(h['color'][1] * h['life'])),
                min(255, int(h['color'][2] * h['life']))
            )
            # Use alpha manually if needed, but fading color to black works for "CRT" feel
            self.draw_text(surface, h['text'], h['x'], h['y'], col, self.big_font)
