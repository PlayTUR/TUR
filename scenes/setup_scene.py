import pygame
from core.scene_manager import Scene
from core.config import *

class SetupScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.options = [
            {"name": "USER IDENTITY", "key": "name", "type": "text"},
            {"name": "THEME SELECTION", "key": "theme", "type": "select", "choices": list(THEMES.keys())},
            {"name": "AUDIO OFFSET", "key": "audio_offset", "type": "int", "min": -200, "max": 200, "step": 5},
            {"name": "SCROLL SPEED", "key": "speed", "type": "int", "min": 100, "max": 2000, "step": 50},
            {"name": "UPDATE SOURCE", "key": "update_url", "type": "text", "readonly": True, "val": "OFFICIAL_REPO"},
            {"name": "SAVE & EXIT", "key": "exit", "type": "action"}
        ]
        self.selected_index = 0
        self.edit_mode = False
        
        # BIOS Colors
        self.bios_bg = (0, 0, 170) # Classic Blue
        self.bios_fg = (200, 200, 200) # Light Grey
        self.bios_hl = (255, 255, 0) # Yellow highlight usually? Or just inverted.
        self.bios_bar = (0, 0, 0)
        
    def draw(self, surface):
        # Always BIOS Blue for this screen, regardless of theme
        surface.fill(self.bios_bg)
        
        # Header
        pygame.draw.rect(surface, (200, 200, 200), (0, 0, SCREEN_WIDTH, 40))
        self.game.renderer.draw_text(surface, "TUR // BIOS SETUP UTILITY", 20, 10, (0, 0, 170), self.game.renderer.font)
        
        # Footer
        pygame.draw.rect(surface, (200, 200, 200), (0, SCREEN_HEIGHT-40, SCREEN_WIDTH, 40))
        self.game.renderer.draw_text(surface, "[ARROWS] Navigate  [ENTER] Select  [ESC] Exit Without Saving", 20, SCREEN_HEIGHT-30, (0, 0, 170))
        
        # Main Area
        list_x = 50
        list_y = 100
        
        for i, opt in enumerate(self.options):
            y = list_y + i * 40
            
            # Get current val
            val = "ACTION"
            if opt["type"] != "action":
                if opt.get("readonly"):
                    val = opt.get("val")
                else:
                    val = self.game.settings.get(opt["key"])
            
            label = opt["name"]
            
            # Draw line
            col = self.bios_fg
            bg_rect_col = None
            
            if i == self.selected_index:
                col = (255, 255, 0) # Yellow text
                if self.edit_mode:
                    col = (0, 255, 0) # Green when editing
                    val = f" < {val} > "
            
            self.game.renderer.draw_text(surface, label, list_x, y, col)
            self.game.renderer.draw_text(surface, str(val), list_x + 400, y, col)
            
        # Help Text
        desc = "Configure system parameters."
        if self.options[self.selected_index]["key"] == "update_url":
            desc = "Updates are currently SIMULATED. No server connected."
        
        self.game.renderer.draw_text(surface, desc, 50, 600, (150, 150, 255))

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if self.edit_mode:
                self.handle_edit(event)
                return
                
            if event.key == pygame.K_UP:
                self.selected_index = (self.selected_index - 1) % len(self.options)
            elif event.key == pygame.K_DOWN:
                self.selected_index = (self.selected_index + 1) % len(self.options)
            elif event.key == pygame.K_RETURN:
                opt = self.options[self.selected_index]
                if opt["type"] == "action":
                    if opt["key"] == "exit":
                        self.game.settings.set("setup_complete", True) 
                        self.game.settings.save()
                        from scenes.menu_scenes import TitleScene
                        self.game.scene_manager.switch_to(TitleScene)
                elif not opt.get("readonly"):
                    self.edit_mode = True
            elif event.key == pygame.K_ESCAPE:
                from scenes.menu_scenes import TitleScene
                self.game.scene_manager.switch_to(TitleScene)

    def handle_edit(self, event):
        opt = self.options[self.selected_index]
        s = self.game.settings
        key = opt["key"]
        val = s.get(key)
        
        if event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
            self.edit_mode = False
            s.save() # Auto save on exit edit
            return
            
        if opt["type"] == "int":
            change = 0
            if event.key == pygame.K_LEFT: change = -opt["step"]
            elif event.key == pygame.K_RIGHT: change = opt["step"]
            
            new_val = max(opt["min"], min(opt["max"], val + change))
            s.set(key, new_val)
            
        elif opt["type"] == "select":
            choices = opt["choices"]
            try: idx = choices.index(val)
            except: idx = 0
            
            if event.key == pygame.K_LEFT: idx = (idx - 1) % len(choices)
            elif event.key == pygame.K_RIGHT: idx = (idx + 1) % len(choices)
            
            s.set(key, choices[idx])
            
        elif opt["type"] == "text":
            # Simple text entry
            if event.key == pygame.K_BACKSPACE:
                s.set(key, val[:-1])
            elif event.unicode.isprintable():
                if len(val) < 20:
                    s.set(key, val + event.unicode.upper())
