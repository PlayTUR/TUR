import pygame
import time
from core.scene_manager import Scene
from core.config import *

class AuthScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.mode = "LOGIN" # LOGIN or REGISTER
        
        # Fields: 0=Username, 1=Password
        self.active_field = 0
        self.username = ""
        self.password = ""
        self.error_msg = ""
        self.error_timer = 0
        
        # Blinking cursor
        self.cursor_timer = 0
        
    def on_enter(self, params=None):
        if params:
            self.mode = params.get('mode', 'LOGIN')
            
        # Discord RPC
        self.game.discord.update("Identifying...", "In Login Screen")
            
        # Reset state
        self.active_field = 0
        current = self.game.settings.get("name")
        if current != "ANON":
            self.username = current
        else:
             self.username = ""
        self.password = ""
        self.error_msg = ""

    def draw(self, surface):
        r = self.game.renderer
        theme = r.get_theme()
        
        # 1. Background Grid Effect
        t = pygame.time.get_ticks()
        surface.fill(theme["bg"])
        grid_offset_y = (t * 0.1) % 40
        grid_col = theme["grid"]
        
        for y in range(0, SCREEN_HEIGHT + 40, 40):
            line_y = y + grid_offset_y - 40
            pygame.draw.line(surface, grid_col, (0, line_y), (SCREEN_WIDTH, line_y))
        for x in range(0, SCREEN_WIDTH, 40):
            pygame.draw.line(surface, grid_col, (x, 0), (x, SCREEN_HEIGHT))

        # Main Panel
        panel_w, panel_h = 600, 380
        px = (SCREEN_WIDTH - panel_w) // 2
        py = (SCREEN_HEIGHT - panel_h) // 2
        
        # Thematic Color
        mode_color = TERM_AMBER if self.mode == "LOGIN" else TERM_GREEN
        mode_title = "USER_IDENTIFICATION" if self.mode == "LOGIN" else "NEW_REGISTRATION_LINK"
        
        # 2. Draw Main Panel
        r.draw_panel(surface, px, py, panel_w, panel_h, mode_title)
        
        # mode indicator glow
        glow_rect = pygame.Rect(px, py - 28, panel_w, 28)
        pygame.draw.rect(surface, (*mode_color, 40), glow_rect)
        pygame.draw.rect(surface, mode_color, glow_rect, 1)

        # Helper for centering within panel
        def draw_field_centered(label, value, y_start, active, masked=False):
            # Label
            lw, lh = r.font.size(label)
            r.draw_text(surface, label, px + (panel_w - lw)//2, y_start, theme["secondary"])
            
            # Box
            bw, bh = 450, 45
            bx, by = px + (panel_w - bw)//2, y_start + 30
            pygame.draw.rect(surface, (0, 0, 0), (bx, by, bw, bh))
            pygame.draw.rect(surface, mode_color if active else theme["grid"], (bx, by, bw, bh), 2 if active else 1)
            
            # Value
            display = "*" * len(value) if masked else value
            # Cursor
            if active and int(time.time() * 2) % 2 == 0:
                display += "_"
            else:
                display += " "
                
            tw, th = r.big_font.size(display)
            # Center text in box
            r.draw_text(surface, display, bx + (bw - tw)//2, by + 8, theme["text"], r.big_font)

        # Field 1: Username
        draw_field_centered("TERMINAL CALLSIGN", self.username, py + 40, self.active_field == 0)
        
        # Field 2: Password
        draw_field_centered("ACCESS CRYPT-KEY", self.password, py + 140, self.active_field == 1, masked=True)

        # Error Message (Centered)
        if time.time() < self.error_timer:
            ew, eh = r.font.size(self.error_msg)
            r.draw_text(surface, f"!! {self.error_msg} !!", px + (panel_w - ew)//2, py + 235, theme["error"])

        # Control Info
        msg_y = py + 280
        controls = [
            ("[TAB]", "SWITCH FIELD"),
            ("[ENTER]", "CONFIRM / SUBMIT"),
            ("[ESC]", "CANCEL MISSION")
        ]
        
        for i, (key, desc) in enumerate(controls):
            kw, kh = r.font.size(key)
            r.draw_text(surface, key, px + 100, msg_y + i*25, theme["primary"])
            r.draw_text(surface, desc, px + 200, msg_y + i*25, (100, 100, 100))

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.play_sfx("back")
                # Return to Title
                from scenes.menu_scenes import TitleScene
                self.game.scene_manager.switch_to(TitleScene)
                
            elif event.key == pygame.K_TAB:
                self.play_sfx("blip")
                self.active_field = (self.active_field + 1) % 2
                
            elif event.key == pygame.K_RETURN:
                if self.active_field == 0 and not self.username:
                    self.active_field = 0 # Focus user
                elif self.active_field == 0:
                    self.active_field = 1 # Move to pass
                    self.play_sfx("blip")
                else:
                    self._submit()
                    
            elif event.key == pygame.K_BACKSPACE:
                self.play_sfx("type")
                if self.active_field == 0:
                    self.username = self.username[:-1]
                else:
                    self.password = self.password[:-1]
            elif event.unicode.isprintable():
                if len(event.unicode) > 0:
                    self.play_sfx("type")
                    if self.active_field == 0:
                        if len(self.username) < 16:
                            self.username += event.unicode.upper() # Usernames upper
                    else:
                        if len(self.password) < 24:
                            self.password += event.unicode
                            
    def _submit(self):
        # Validate
        if not self.username.strip():
            self._show_error("USERNAME REQUIRED")
            return
            
        if not self.password:
            self._show_error("PASSWORD REQUIRED")
            return
            
        # CHECK BAN STATUS
        import json
        import os
        if os.path.exists("bans.json"):
            try:
                with open("bans.json", "r") as f:
                    bans = json.load(f)
                    if self.username.strip() in bans:
                        ban_data = bans[self.username.strip()]
                        expires = ban_data.get("expires", 0)
                        if time.time() < expires:
                            # Still banned
                            import datetime
                            dt_object = datetime.datetime.fromtimestamp(expires)
                            date_str = dt_object.strftime("%Y-%m-%d")
                            self._show_error(f"SUSPENDED UNTIL {date_str}")
                            self.play_sfx("error")
                            return
            except Exception as e:
                print(f"Error checking bans: {e}")
            
        # Success Logic (Dummy)
        self.play_sfx("success")
        
        # Save to settings
        self.game.settings.set("name", self.username.strip())
        
        if self.mode == "REGISTER":
            self.game.settings.set("account_type", "REGISTERED")
            self.game.settings.set("last_name_change", time.time())
            self.game.settings.set("logged_in", True)
        else:
             self.game.settings.set("account_type", "REGISTERED")
             self.game.settings.set("logged_in", True)
             
        # Return to Title
        from scenes.menu_scenes import TitleScene
        self.game.scene_manager.switch_to(TitleScene)
        
    def _show_error(self, msg):
        self.error_msg = msg
        self.error_timer = time.time() + 2 # Show for 2 sec
        self.play_sfx("blip")
