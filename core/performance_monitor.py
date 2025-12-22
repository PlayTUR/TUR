import pygame
import psutil
import time

class PerformanceMonitor:
    def __init__(self, game):
        self.game = game
        self.font = None # Lazy load
        self.last_update = 0
        self.cpu_usage = 0
        self.ram_usage = 0
        self.fps_history = []
        
    def update(self):
        t = time.time()
        if t - self.last_update > 0.5: # Update stats every 500ms
            self.last_update = t
            try:
                self.cpu_usage = psutil.cpu_percent()
                self.ram_usage = psutil.virtual_memory().percent
            except:
                pass
                
    def draw(self, surface):
        if not self.font:
            self.font = pygame.font.SysFont("monospace", 12, bold=True)
            
        settings = self.game.settings
        mode = settings.get("show_fps")
        
        # Mode 0: Off
        if not mode: return
        
        # Common Data
        clock = self.game.clock
        fps = int(clock.get_fps())
        
        # Setup Text
        lines = []
        
        if mode == 1: # SIMPLE
            lines.append(f"FPS: {fps}")
            
        elif mode == 2: # DETAILED
            lines.append(f"FPS: {fps}")
            lines.append(f"FT:  {clock.get_time()}ms")
            lines.append(f"CPU: {self.cpu_usage:.1f}%")
            lines.append(f"RAM: {self.ram_usage:.1f}%")
            
        # Draw Top Right (User request: Top Left or Right, let's go Top Right for clean look)
        # Actually Top Left is usually standard for FPS counters to not block game UI (often top right has scores)
        # Let's check game UI... Menu has stuff in center/right. GameScene has score top right.
        # Top Left seems safest.
        
        start_x = 10
        start_y = 10
        width = 120
        height = len(lines) * 15 + 10
        
        # Draw Background Panel
        s = pygame.Surface((width, height))
        s.set_alpha(180)
        s.fill((0, 0, 0))
        surface.blit(s, (start_x, start_y))
        
        # Border
        pygame.draw.rect(surface, (50, 50, 50), (start_x, start_y, width, height), 1)
        
        # Draw Lines
        y = start_y + 5
        for line in lines:
            col = (0, 255, 0) # Good
            if "FPS" in line and fps < 55: col = (255, 255, 0) # Warn
            if "FPS" in line and fps < 30: col = (255, 0, 0) # Bad
            
            # CPU/RAM warnings
            if "CPU" in line and self.cpu_usage > 80: col = (255, 0, 0)
            
            surf = self.font.render(line, True, col)
            surface.blit(surf, (start_x + 10, y))
            y += 15
