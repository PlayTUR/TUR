import pygame
import os
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
        self.step = 0
        self.finished = False
        
        self.sfx_boot = pygame.mixer.Sound("sfx/sfx_boot.wav") if os.path.exists("sfx/sfx_boot.wav") else None
        if self.sfx_boot: self.sfx_boot.set_volume(0.4)
            
        self.sfx_type = pygame.mixer.Sound("sfx/sfx_type.wav") if os.path.exists("sfx/sfx_type.wav") else None
        if self.sfx_type: self.sfx_type.set_volume(0.2)
        
        self.sfx_hdd = pygame.mixer.Sound("sfx/sfx_hdd.wav") if os.path.exists("sfx/sfx_hdd.wav") else None
        if self.sfx_hdd: self.sfx_hdd.set_volume(0.2)
        
        self.sfx_success = pygame.mixer.Sound("sfx/sfx_success.wav") if os.path.exists("sfx/sfx_success.wav") else None
        if self.sfx_success: self.sfx_success.set_volume(0.5)
        
        # Fake BIOS Data
        self.ram_kb = 0
        self.total_ram = 64 * 1024 # 64 MB retro style
        
        self.boot_steps = [
            {"text": "TERMINAL BIOS v1.0.4 (c) 198X", "delay": 60, "sfx": "type"},
            {"text": "CPU: MOTOROLA 68000 @ 8 MHz", "delay": 30, "sfx": "type"},
            {"text": "CHECKING MEMORY...", "action": "RAM", "delay": 10, "sfx": "hdd"}, 
            {"text": "MEMORY OK.", "delay": 30, "sfx": "type"},
            {"text": "DETECTING DRIVES...", "delay": 40, "sfx": "hdd"},
            {"text": "  DRIVE A: TUR_DISK SYSTEM", "delay": 20, "sfx": "type"},
            {"text": "  DRIVE B: NONE", "delay": 10, "sfx": "type"},
            {"text": "INITIALIZING VIDEO... VGA DETECTED", "delay": 30, "sfx": "type"},
            {"text": "LOADING KERNEL...", "delay": 50, "sfx": "hdd"},
            {"text": "BOOT SEQUENCE COMPLETE.", "delay": 30, "sfx": "success"},
            {"text": "", "delay": 30},
            {"text": "WELCOME TO TUR SYSTEM", "delay": 10, "sfx": "type"}, 
            {"text": "", "delay": 120}, # Explicit wait time for user to read
            {"text": "ENTERING SHELL...", "delay": 30, "sfx": "type"},
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
        
        # Play Start Beep on first frame
        if self.current_step_idx == 0 and self.wait_time == 1:
            if self.sfx_boot: self.sfx_boot.play()
            
        if self.wait_time >= item["delay"]:
            if item.get("action") == "DONE":
                self.finish_boot()
            else:
                txt = item.get("text", "")
                if txt:
                     self.lines.append(txt)
                     
                     # SFX Trigger
                     sfx = item.get("sfx")
                     if sfx == "type" and self.sfx_type: self.sfx_type.play()
                     elif sfx == "hdd" and self.sfx_hdd: self.sfx_hdd.play()
                     elif sfx == "success" and self.sfx_success: self.sfx_success.play()
                     
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
