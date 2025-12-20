import pygame
from core.scene_manager import Scene
from core.config import *
import random

class BootScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.lines = []
        self.max_lines = 20
        self.timer = 0
        self.step = 0
        self.finished = False
        
        # Fake BIOS Data
        self.ram_kb = 0
        self.total_ram = 64 * 1024 # 64 MB retro style
        
        self.boot_steps = [
            {"text": "TERMINAL BIOS v1.0.4 (c) 198X", "delay": 60},
            {"text": "CPU: MOTOROLA 68000 @ 8 MHz", "delay": 30},
            {"text": "CHECKING MEMORY...", "action": "RAM", "delay": 10}, # Fast RAM count
            {"text": "MEMORY OK.", "delay": 30},
            {"text": "DETECTING DRIVES...", "delay": 40},
            {"text": "  DRIVE A: TUR_DISK SYSTEM", "delay": 20},
            {"text": "  DRIVE B: NONE", "delay": 10},
            {"text": "INITIALIZING VIDEO... VGA DETECTED", "delay": 30},
            {"text": "LOADING KERNEL...", "delay": 50},
            {"text": "BOOT SEQUENCE COMPLETE.", "delay": 60},
            {"text": "", "action": "DONE", "delay": 10}
        ]
        
        self.current_step_idx = 0
        self.wait_time = 0
        
    def draw(self, surface):
        surface.fill((0, 0, 0))
        
        # Draw all accumulated lines
        start_y = 20
        for i, line in enumerate(self.lines):
            self.game.renderer.draw_text(surface, line, 20, start_y + i * 25, (200, 200, 200), self.game.renderer.font)
            
        # Draw RAM counter if active
        if self.boot_steps[self.current_step_idx].get("action") == "RAM":
            self.game.renderer.draw_text(surface, f"{self.ram_kb} KB OK", 20, start_y + len(self.lines) * 25, (200, 200, 200), self.game.renderer.font)

        # Blinking Cursor at bottom
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            cursor_y = start_y + len(self.lines) * 25
            if self.boot_steps[self.current_step_idx].get("action") == "RAM": cursor_y += 25
            pygame.draw.rect(surface, (200, 200, 200), (20, cursor_y, 10, 20))

    def update(self):
        if self.finished:
            return

        item = self.boot_steps[self.current_step_idx]
        
        # RAM Animation Logic
        if item.get("action") == "RAM":
            self.ram_kb += 1024
            if self.ram_kb >= self.total_ram:
                self.lines.append("CHECKING MEMORY... OK")
                self.lines.append(f"{self.total_ram} KB OK")
                self.advance_step()
            return
            
        # Standard Delay Logic
        self.wait_time += 1
        if self.wait_time >= item["delay"]:
            if item.get("action") == "DONE":
                self.finish_boot()
            else:
                self.lines.append(item["text"])
                self.advance_step()

    def advance_step(self):
        self.current_step_idx += 1
        self.wait_time = 0
        
    def finish_boot(self):
        self.finished = True
        # Decide next scene
        if not self.game.settings.get("setup_complete"):
            from scenes.setup_scene import SetupScene
            self.game.scene_manager.switch_to(SetupScene)
        else:
            from scenes.menu_scenes import TitleScene
            self.game.scene_manager.switch_to(TitleScene)
            self.game.play_menu_bgm()
