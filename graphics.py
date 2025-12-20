import pygame
import random
import math
from config import *

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(2, 6)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = 1.0
        self.decay = random.uniform(0.02, 0.05)
        self.size = random.randint(3, 6)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= self.decay
        self.size *= 0.95

    def draw(self, surface):
        if self.life > 0:
            current_size = int(self.size)
            if current_size > 0:
                # Fade out logic if desired, but simple circle shrink is enough
                alpha = int(self.life * 255)
                # Helper to draw with alpha if needed, but simple RGB drawing is faster for many particles
                # if we just modify color
                col = (
                    min(255, int(self.color[0] * self.life)),
                    min(255, int(self.color[1] * self.life)),
                    min(255, int(self.color[2] * self.life))
                )
                pygame.draw.circle(surface, col, (int(self.x), int(self.y)), current_size)

class Visuals:
    def __init__(self):
        self.particles = []
        self.hit_texts = [] # (text, x, y, life, color)

    def add_hit_effect(self, x, y, color):
        for _ in range(10):
            self.particles.append(Particle(x, y, color))
    
    def add_hit_text(self, text, color):
        # Center of Hit Line
        x = SCREEN_WIDTH // 2
        y = HIT_LINE_Y - 50
        self.hit_texts.append([text, x, y, 1.0, color])

    def update(self):
        # Update particles
        self.particles = [p for p in self.particles if p.life > 0]
        for p in self.particles:
            p.update()

        # Update texts
        # Format: [text, x, y, life, color]
        for t in self.hit_texts:
            t[2] -= 1 # float up
            t[3] -= 0.03 # decay
        self.hit_texts = [t for t in self.hit_texts if t[3] > 0]

    def draw(self, surface, font):
        for p in self.particles:
            p.draw(surface)
        
        for t in self.hit_texts:
            text_str, x, y, life, color = t
            rendered = font.render(text_str, True, color)
            rendered.set_alpha(int(life * 255))
            rect = rendered.get_rect(center=(x, y))
            surface.blit(rendered, rect)

class LaneRenderer:
    def __init__(self):
        self.key_states = [False] * 4 # Pressed state for visual feedback

    def draw_lanes(self, surface):
        # Draw background for lane area
        pygame.draw.rect(surface, LANE_BG, (LANE_START_X, 0, LANE_AREA_WIDTH, SCREEN_HEIGHT))
        
        # Draw Hit Line
        pygame.draw.line(surface, WHITE, (LANE_START_X, HIT_LINE_Y), (LANE_START_X + LANE_AREA_WIDTH, HIT_LINE_Y), 2)
        
        # Draw lanes
        for i in range(NUM_LANES):
            x = LANE_START_X + i * LANE_WIDTH
            
            # Draw separators
            if i > 0:
                pygame.draw.line(surface, LANE_BORDER_COLOR, (x, 0), (x, SCREEN_HEIGHT), 1)

            # Draw Receptor (Key / Button at bottom)
            receptor_y = HIT_LINE_Y
            receptor_color = LANE_COLORS[i]
            
            # If pressed, light up
            if self.key_states[i]:
                pygame.draw.circle(surface, (255, 255, 255), (x + LANE_WIDTH // 2, receptor_y), NOTE_RADIUS)
                # Add a faint glow beam
                s = pygame.Surface((LANE_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                s.fill((receptor_color[0], receptor_color[1], receptor_color[2], 50))
                surface.blit(s, (x, 0))
            else:
                # Dim receptor
                pygame.draw.circle(surface, (receptor_color[0]//2, receptor_color[1]//2, receptor_color[2]//2), (x + LANE_WIDTH // 2, receptor_y), NOTE_RADIUS, 3)

    def draw_notes(self, surface, notes, song_time):
        # notes is a list of note dicts
        # Draw from bottom to top, but only visible ones
        
        # Determine visible time range
        # time = (trigger_y - y) / scroll_speed
        # dist = time * scroll_speed
        # Note y = HIT_LINE_Y - (note_time - song_time) * SCROLL_SPEED
        
        for note in notes:
            if note.get('hit', False):
                continue
            
            dt = note['time'] - song_time
            
            # Simple visibility check to avoid drawing notes way off screen
            if dt < -0.2 or dt > 2.0: # Keep caught misses for a moment or look ahead 2 seconds
                continue
                
            y = HIT_LINE_Y - (dt * SCROLL_SPEED)
            lane = note['lane']
            x = LANE_START_X + lane * LANE_WIDTH + LANE_WIDTH // 2
            
            color = LANE_COLORS[lane]
            pygame.draw.circle(surface, color, (x, int(y)), NOTE_RADIUS)
            # Inner white dot for "circle" polish
            pygame.draw.circle(surface, WHITE, (x, int(y)), NOTE_RADIUS // 3)
