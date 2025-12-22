"""
Setup Scene - First-run BIOS Configuration
Enhanced with more options and better visuals.
"""

import pygame
from core.scene_manager import Scene
from core.config import *
import os


class SetupScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        
        self.options = [
            {"name": "USER IDENTITY", "key": "name", "type": "text", "desc": "Enter your callsign for the system."},
            {"name": "DISPLAY THEME", "key": "theme", "type": "select", "choices": list(THEMES.keys()), "desc": "Choose terminal color scheme."},
            {"name": "NOTE SPEED", "key": "speed", "type": "int", "min": 200, "max": 1500, "step": 50, "desc": "How fast notes scroll (200-1500)."},
            {"name": "AUDIO OFFSET", "key": "audio_offset", "type": "int", "min": -200, "max": 200, "step": 5, "desc": "Fine-tune audio sync (ms)."},
            {"name": "SCROLL DIRECTION", "key": "upscroll", "type": "bool", "desc": "Toggle upscroll vs downscroll."},
            {"name": "FULLSCREEN", "key": "fullscreen", "type": "bool", "desc": "Enable fullscreen mode."},
            {"name": "HIT SOUNDS", "key": "hit_sounds", "type": "bool", "desc": "Play sounds when hitting notes."},
            {"name": "VISUAL EFFECTS", "key": "visual_effects", "type": "bool", "desc": "Enable particle effects."},
            {"name": "", "key": "spacer", "type": "spacer"},
            {"name": "SAVE & CONTINUE", "key": "exit", "type": "action", "desc": "Save settings and start!"}
        ]
        
        self.selected_index = 0
        self.edit_mode = False
        self.blink_timer = 0
        
        # Load sounds
        self.sfx_blip = self._load_sfx("sfx/sfx_blip.wav")
        self.sfx_accept = self._load_sfx("sfx/sfx_accept.wav")
    
    def _load_sfx(self, path):
        if os.path.exists(path):
            return pygame.mixer.Sound(path)
        return None
    
    def play_sfx(self, name):
        if name == "blip" and self.sfx_blip:
            self.sfx_blip.play()
        elif name == "accept" and self.sfx_accept:
            self.sfx_accept.play()

    def update(self):
        self.blink_timer = (self.blink_timer + 1) % 60

    def draw(self, surface):
        r = self.game.renderer
        theme = r.get_theme()
        
        # Draw theme-aligned background
        surface.fill(theme["bg"])
        
        # Subtle scanlines (common to BIOS scenes)
        for y in range(0, 768, 6):
            pygame.draw.line(surface, [max(0, c - 5) for c in theme["bg"]], (0, y), (1024, y))
        
        # Header box (inverted theme)
        pygame.draw.rect(surface, theme["primary"], (0, 0, 1024, 60))
        r.draw_text(surface, " INITIAL CRITICAL CONFIGURATION ", 280, 18, theme["bg"], r.big_font)
        
        # Main panel
        r.draw_panel(surface, 80, 90, 550, 520, "SYS_OPTIONS")
        
        y = 115
        for i, opt in enumerate(self.options):
            if opt["type"] == "spacer":
                y += 20
                continue
            
            # Get value
            if opt["type"] == "action":
                val_str = "→"
            elif opt["type"] == "bool":
                val = self.game.settings.get(opt["key"])
                val_str = "ENABLED" if val else "DISABLED"
            else:
                val = self.game.settings.get(opt["key"])
                val_str = str(val)
            
            selected = (i == self.selected_index)
            
            # Draw selection highlight (using theme grid color)
            if selected:
                pygame.draw.rect(surface, [min(255, c + 20) for c in theme["grid"]], (95, y - 3, 520, 36))
            
            # Label
            label_color = theme["primary"] if selected else [max(0, c - 50) for c in theme["text"]]
            r.draw_text(surface, f"{'█' if selected else ' '} {opt['name']}", 100, y + 5, label_color)
            
            # Value
            if opt["type"] != "action":
                if self.edit_mode and selected:
                    val_color = theme["primary"]
                    if self.blink_timer < 30:
                        val_str = f"[{val_str}]"
                    else:
                        val_str = f" {val_str} "
                else:
                    val_color = theme["secondary"] if selected else (120, 120, 120)
                
                r.draw_text(surface, val_str, 450, y + 5, val_color)
            else:
                if selected:
                    r.draw_text(surface, "EXECUTE", 500, y + 5, theme["primary"])
            
            y += 42
        
        # Preview panel with theme colors
        r.draw_panel(surface, 660, 90, 300, 200, "COLOR_BUFFER")
        th = theme # Use current theme instead of lookup for better preview during setup
        pygame.draw.rect(surface, th["bg"], (680, 120, 260, 140))
        pygame.draw.rect(surface, th["primary"], (700, 140, 80, 30))
        r.draw_text(surface, "PRIMARY", 700, 145, th["bg"])
        pygame.draw.rect(surface, th["secondary"], (700, 180, 80, 30))
        r.draw_text(surface, "SECOND", 700, 185, th["bg"])
        r.draw_text(surface, "Rhythm Test", 800, 150, th["text"])
        r.draw_text(surface, "Warn: High", 800, 190, th["error"])
        
        # Help panel
        r.draw_panel(surface, 660, 320, 300, 180, "COMMANDS")
        r.draw_text(surface, "[UP/DOWN] Move Cursor", 680, 345, theme["text"])
        r.draw_text(surface, "[ENTER]   Action/Edit", 680, 375, theme["text"])
        r.draw_text(surface, "[L/R]     Adjust", 680, 405, theme["text"])
        r.draw_text(surface, "[ESC]     Cancel", 680, 435, theme["text"])
        
        # Description (Bottom bar)
        opt = self.options[self.selected_index]
        desc = opt.get("desc", "").upper()
        pygame.draw.rect(surface, theme["grid"], (0, 650, 1024, 120))
        pygame.draw.rect(surface, theme["primary"], (0, 650, 1024, 2))
        r.draw_text(surface, f"STATUS//DESCRIPTION: {desc}", 100, 680, theme["text"])
        
        # Footer
        r.draw_text(surface, "CORE SYSTEM KERNEL v2.0.4-LTS", 380, 725, theme["grid"])

    def handle_input(self, event):
        if event.type != pygame.KEYDOWN:
            return
        
        if self.edit_mode:
            self._handle_edit(event)
            return
        
        if event.key == pygame.K_UP:
            self._move_selection(-1)
        elif event.key == pygame.K_DOWN:
            self._move_selection(1)
        elif event.key == pygame.K_RETURN:
            self._select_option()
        elif event.key == pygame.K_ESCAPE:
            # Exit without saving
            from scenes.menu_scenes import TitleScene
            self.game.scene_manager.switch_to(TitleScene)
    
    def _move_selection(self, direction):
        for _ in range(len(self.options)):
            self.selected_index = (self.selected_index + direction) % len(self.options)
            if self.options[self.selected_index]["type"] != "spacer":
                break
        self.play_sfx("blip")
    
    def _select_option(self):
        opt = self.options[self.selected_index]
        self.play_sfx("accept")
        
        if opt["type"] == "action":
            if opt["key"] == "exit":
                self.game.settings.set("setup_complete", True)
                self.game.settings.save()
                from scenes.menu_scenes import TitleScene
                self.game.scene_manager.switch_to(TitleScene)
                self.game.play_menu_bgm()
        elif opt["type"] == "bool":
            # Toggle directly
            cur = self.game.settings.get(opt["key"])
            self.game.settings.set(opt["key"], not cur)
            self._apply_setting(opt["key"])
        else:
            self.edit_mode = True
    
    def _handle_edit(self, event):
        opt = self.options[self.selected_index]
        key = opt["key"]
        val = self.game.settings.get(key)
        
        if event.key in [pygame.K_RETURN, pygame.K_ESCAPE]:
            self.edit_mode = False
            self.game.settings.save()
            self.play_sfx("accept")
            return
        
        if opt["type"] == "int":
            change = 0
            if event.key == pygame.K_LEFT:
                change = -opt["step"]
            elif event.key == pygame.K_RIGHT:
                change = opt["step"]
            
            if change:
                new_val = max(opt["min"], min(opt["max"], val + change))
                self.game.settings.set(key, new_val)
                self.play_sfx("blip")
        
        elif opt["type"] == "select":
            choices = opt["choices"]
            try:
                idx = choices.index(val)
            except:
                idx = 0
            
            if event.key == pygame.K_LEFT:
                idx = (idx - 1) % len(choices)
                self.game.settings.set(key, choices[idx])
                self._apply_setting(key)
                self.play_sfx("blip")
            elif event.key == pygame.K_RIGHT:
                idx = (idx + 1) % len(choices)
                self.game.settings.set(key, choices[idx])
                self._apply_setting(key)
                self.play_sfx("blip")
        
        elif opt["type"] == "text":
            if event.key == pygame.K_BACKSPACE:
                self.game.settings.set(key, val[:-1])
                self.play_sfx("blip")
            elif event.unicode.isprintable() and len(val) < 16:
                self.game.settings.set(key, val + event.unicode.upper())
                self.play_sfx("blip")
    
    def _apply_setting(self, key):
        """Apply settings that need immediate effect"""
        if key == "theme":
            # Update note colors to match theme
            th = THEMES.get(self.game.settings.get("theme"), THEMES["TERMINAL"])
            self.game.settings.set("note_col_1", list(th["primary"]))
            self.game.settings.set("note_col_2", list(th["secondary"]))
        elif key == "fullscreen":
            fs = self.game.settings.get("fullscreen")
            res = self.game.settings.get("resolution")
            if fs:
                pygame.display.set_mode(res, pygame.FULLSCREEN)
            else:
                pygame.display.set_mode(res, pygame.RESIZABLE)
