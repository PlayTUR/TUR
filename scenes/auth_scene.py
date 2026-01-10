"""
Auth Scene - Login Only
Users register on website, login in-game
"""

import pygame
import time
import webbrowser
from core.scene_manager import Scene
from core.config import *

# Website URL for registration
REGISTER_URL = "https://wyind.dev/#account"

class AuthScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        
        # Fields: 0=Username, 1=Password
        self.active_field = 0
        self.username = ""
        self.password = ""
        self.error_msg = ""
        self.error_timer = 0
        self.error_timer = 0
        self.logging_in = False
        self.remember_me = True # Default to True
        
    def on_enter(self, params=None):
        # Discord RPC
        self.game.discord.update("Identifying...", "In Login Screen")
            
        # Reset state
        self.active_field = 0
        self.username = "" # Always start empty
        self.password = ""
        self.error_msg = ""
        self.logging_in = False

    def draw(self, surface):
        r = self.game.renderer
        theme = r.get_theme()
        
        sw = surface.get_width()
        sh = surface.get_height()
        
        # Background Grid Effect
        t = pygame.time.get_ticks()
        surface.fill(theme["bg"])
        grid_offset_y = (t * 0.1) % 40
        grid_col = theme["grid"]
        
        for y in range(0, sh + 40, 40):
            line_y = y + grid_offset_y - 40
            pygame.draw.line(surface, grid_col, (0, line_y), (sw, line_y))
        for x in range(0, sw, 40):
            pygame.draw.line(surface, grid_col, (x, 0), (x, sh))

        # Main Panel
        panel_w, panel_h = min(550, sw - 40), 360
        px = (sw - panel_w) // 2
        py = (sh - panel_h) // 2
        
        mode_color = TERM_AMBER
        
        # Draw Main Panel
        r.draw_panel(surface, px, py, panel_w, panel_h, "LOGIN")
        
        # Helper for fields
        def draw_field(label, value, y_start, active, masked=False):
            lw, lh = r.font.size(label)
            r.draw_text(surface, label, px + (panel_w - lw)//2, y_start, theme["secondary"])
            
            bw, bh = min(420, panel_w - 50), 45
            bx, by = px + (panel_w - bw)//2, y_start + 28
            pygame.draw.rect(surface, (0, 0, 0), (bx, by, bw, bh))
            pygame.draw.rect(surface, mode_color if active else theme["grid"], (bx, by, bw, bh), 2 if active else 1)
            
            display = "*" * len(value) if masked else value
            if active and int(time.time() * 2) % 2 == 0:
                display += "_"
            else:
                display += " "
                
            tw, th = r.big_font.size(display)
            r.draw_text(surface, display, bx + (bw - tw)//2, by + 8, theme["text"], r.big_font)

        # Fields
        draw_field("USERNAME", self.username, py + 35, self.active_field == 0)
        draw_field("PASSWORD", self.password, py + 125, self.active_field == 1, masked=True)

        if self.active_field == 2:
            pass

        # Controls
        controls_y = py + 220
        r.draw_text(surface, "[TAB] Switch Field", px + 30, controls_y, (100, 100, 100))
        r.draw_text(surface, "[ENTER] Login", px + 30, controls_y + 25, (100, 100, 100))
        
        # "Remember Me" integrated into controls
        chk_char = "x" if self.remember_me else " "
        chk_col = theme["text"] if self.remember_me else (100, 100, 100)
        
        r.draw_text(surface, f"[{chk_char}] REMEMBER ME [F1]", px + 30, controls_y + 50, chk_col)
        
        r.draw_text(surface, "[ESC] Cancel", px + 30, controls_y + 75, (100, 100, 100))
        
        # Password reset hint
        if getattr(self, 'reset_hint', False) and time.time() < getattr(self, 'reset_hint_timer', 0):
            r.draw_text(surface, "Forgot password? Reset at tur.wyind.dev", px + 30, controls_y + 110, (100, 150, 255))
        
        # Register link - Simplified formatting
        reg_x = px + panel_w - 160
        r.draw_text(surface, "No account?", reg_x, controls_y, (100, 100, 100))
        r.draw_text(surface, "[F2] Register", reg_x, controls_y + 25, theme["primary"])

        # Error Message Overlay (Moved to end for Z-Index)
        if time.time() < self.error_timer:
            r.draw_high_viz_popup(surface, "IDENT_FAILURE", self.error_msg)

    def handle_input(self, event):
        if self.logging_in:
            return
            
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.play_sfx("back")
                from scenes.menu_scenes import TitleScene
                self.game.scene_manager.switch_to(TitleScene)
                
            elif event.key == pygame.K_TAB:
                self.play_sfx("blip")
                self.active_field = (self.active_field + 1) % 2 # 0=User, 1=Pass
                
            elif event.key == pygame.K_F1:
                 # Toggle Remember Me via Keybind
                 self.remember_me = not self.remember_me
                 self.play_sfx("blip")
                
            elif event.key == pygame.K_F2:
                # Open URL
                self.play_sfx("accept")
                try:
                    print(f"Opening register URL: {REGISTER_URL}")
                    webbrowser.open(REGISTER_URL)
                except Exception as e:
                    print(f"Failed to open URL: {e}")

            elif event.key == pygame.K_RETURN:
                if self.active_field == 0 and self.username:
                    self.active_field = 1
                    self.play_sfx("blip")
                elif self.active_field == 1 or (self.active_field == 0 and self.username):
                    # Enter always tries to submit if we have a username, or moves to pass
                    if not self.password:
                         self.active_field = 1
                         self.play_sfx("blip")
                    else:
                         self._submit()
                    
            elif event.key == pygame.K_BACKSPACE:
                self.play_sfx("type")
                if self.active_field == 0:
                    self.username = self.username[:-1]
                else:
                    self.password = self.password[:-1]
                    
            elif event.unicode.isprintable() and len(event.unicode) > 0:
                self.play_sfx("type")
                if self.active_field == 0:
                    if len(self.username) < 16:
                        self.username += event.unicode  # Keep original case
                else:
                    if len(self.password) < 24:
                        self.password += event.unicode
                        
    def _submit(self):
        if not self.username.strip():
            self._show_error("USERNAME REQUIRED")
            return
            
        if not self.password:
            self._show_error("PASSWORD REQUIRED")
            return
        
        self.logging_in = True
        
        # Try master server login
        import threading
        def login_thread():
            try:
                from core.master_client import get_master_client
                mc = get_master_client()
                
                if mc.login(self.username.strip(), self.password):
                    # Success
                    self.game.settings.set("name", mc.username)
                    self.game.settings.set("account_type", "REGISTERED")
                    self.game.settings.set("logged_in", True)
                    self.game.settings.set("account_type", "REGISTERED")
                    self.game.settings.set("logged_in", True)
                    
                    if self.remember_me:
                         self.game.settings.set("auth_token", mc.auth_token)
                    else:
                         self.game.settings.set("auth_token", None) # Clear it if user unchecked
                         
                    self.play_sfx("success")
                    
                    from scenes.menu_scenes import TitleScene
                    self.game.scene_manager.switch_to(TitleScene)
                else:
                    # Show error with password reset hint
                    error = mc.error or "Invalid credentials"
                    self._show_error(error)
                    self._show_reset_hint()
                    self.logging_in = False
            except Exception as e:
                self._show_error("Server unreachable")
                self.logging_in = False
        
        threading.Thread(target=login_thread, daemon=True).start()
        
    def _show_error(self, msg):
        self.error_msg = msg
        self.error_timer = time.time() + 4
        self.play_sfx("blip")
    
    def _show_reset_hint(self):
        """Show password reset hint"""
        self.reset_hint = True
        self.reset_hint_timer = time.time() + 6
