
import pygame
import threading
from core.scene_manager import Scene
from core.config import *

class ProfileScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.menu_items = ["VIEW LEADERBOARD", "EDIT PROFILE", "LOGOUT", "BACK"]
        self.index = 0
        
        self.loading = True
        self.profile_data = None
        self.error_msg = None
        
        # Temp state
        self.renaming = False
        self.temp_name = ""

    def on_enter(self, params=None):
        self.game.discord.update("Viewing Profile", "In Menu")
        self.loading = True
        self.error_msg = None
        
        # Start async fetch
        threading.Thread(target=self._fetch_profile, daemon=True).start()
        
    def _fetch_profile(self):
        try:
            # 1. Ensure we are logged in
            if not self.game.master_client.logged_in:
                # If guest, just load local settings simulation
                self.profile_data = self._get_guest_profile()
                self.loading = False
                return

            # 2. Fetch full profile from API
            data = self.game.master_client.get_my_stats()
            
            if data:
                self.profile_data = data
                
                # Check admin status and update menu
                is_admin = data.get("is_admin", False) is True
                is_stealth = data.get("is_stealth", False) is True
                
                # Update local settings to match server
                self.game.settings.set("is_admin", is_admin)
                self.game.settings.set("is_stealth", is_stealth)
                self.game.settings.set("name", data.get("username", "Unknown"))
                self.game.settings.set("user_id", data.get("id", 0))    
            
                # Add Admin Panel if admin
                if is_admin and "WEB ADMIN PANEL" not in self.menu_items:
                     self.menu_items.insert(0, "WEB ADMIN PANEL")
                
                # We do NOT hide admin panel in menu even if stealth, 
                # but we hide the badge in the UI.
                
            else:
                self.error_msg = "Failed to load profile data."
                
        except Exception as e:
            self.error_msg = f"Error: {str(e)}"
            print(f"Profile fetch error: {e}")
            
        self.loading = False

    def _get_guest_profile(self):
        # Fallback for guests
        return {
            "username": self.game.settings.get("name", "Guest"),
            "id": 0,
            "is_admin": False,
            "stats": {
                "xp": self.game.settings.get("xp", 0),
                "level": self.game.settings.get("level", 1),
                "rank": 0,
                "total_score": 0,
                "play_count": 0,
                "avg_accuracy": 0,
                "max_combo": 0
            },
            "created_at": "N/A"
        }

    def draw(self, surface):
        r = self.game.renderer
        theme = r.get_theme()
        
        # Background
        surface.fill(theme["bg"])
        self._draw_grid(surface, theme)
        
        # Header
        r.draw_text(surface, "USER PROFILE", 50, 40, theme["primary"], r.big_font)
        pygame.draw.line(surface, theme["primary"], (50, 80), (400, 80), 2)
        
        if self.loading:
            self._draw_loading(surface, r, theme)
            return
            
        if self.error_msg:
            r.draw_text(surface, f"ERROR: {self.error_msg}", 100, 300, theme["error"])
            r.draw_text(surface, "Press [ESC] to return", 100, 340, theme["text"])
            return
            
        # Extract Data
        data = self.profile_data or {}
        stats = data.get("stats", {})
        
        username = data.get("username", "Unknown")
        uid = data.get("id", 0)
        is_admin = data.get("is_admin", False) is True
        is_stealth = data.get("is_stealth", False) is True
        
        lvl = stats.get("level", 1)
        xp = stats.get("xp", 0)
        rank = stats.get("rank", 0)
        
        # ---- LAYOUT ----
        
        # 1. Left Panel: ID Card
        panel_x = 50
        panel_y = 120
        r.draw_panel(surface, panel_x, panel_y, 400, 350, "OPERATOR_ID")
        
        # Avatar placeholder
        r.draw_text(surface, "[ AVATAR ]", panel_x + 140, panel_y + 60, (50, 50, 50))
        pygame.draw.rect(surface, theme["secondary"], (panel_x + 120, panel_y + 40, 160, 80), 1)
        
        info_x = panel_x + 40
        y = panel_y + 160
        
        r.draw_text(surface, f"NAME: {username}", info_x, y, theme["text"])
        r.draw_text(surface, f"UID:  #{uid:04d}", info_x, y + 30, (150, 150, 150))
        
        # Admin Badge (Replaces Rank)
        if is_admin and not is_stealth:
            badge_rect = pygame.Rect(info_x, y + 60, 120, 26)
            pygame.draw.rect(surface, (255, 215, 0), badge_rect)
            pygame.draw.rect(surface, (255, 255, 255), badge_rect, 1)
            r.draw_text(surface, "ROOT ADMIN", info_x + 15, y + 64, (0, 0, 0), r.small_font)
        else:
             # If not admin/stealth, maybe show something else or nothing? 
             # User asked to "remove rank, replace with badge". 
             # I'll leave it empty or show "OPERATOR" for non-admins to keep spacing?
             # Let's show "OPERATOR" for aesthetics.
             r.draw_text(surface, "OPERATOR", info_x, y + 60, (100, 100, 100))
        
        # 2. Right Panel: Stats
        stats_x = 500
        r.draw_panel(surface, stats_x, panel_y, 500, 220, "PERFORMANCE_METRICS")
        
        sx = stats_x + 40
        sy = panel_y + 60
        
        # Grid of stats
        def draw_stat(label, val, x, y, col=theme["primary"]):
            r.draw_text(surface, label, x, y, theme["secondary"], r.small_font)
            r.draw_text(surface, str(val), x, y + 20, col, r.big_font)
            
        draw_stat("LEVEL", lvl, sx, sy)
        draw_stat("TOTAL SCORE", f"{stats.get('total_score', 0):,}", sx + 150, sy)
        draw_stat("PLAY COUNT", stats.get('play_count', 0), sx + 340, sy)
        
        sy += 80
        draw_stat("ACCURACY", f"{stats.get('avg_accuracy', 0):.1f}%", sx, sy)
        draw_stat("MAX COMBO", f"{stats.get('max_combo', 0)}x", sx + 150, sy)
        draw_stat("XP", f"{xp}", sx + 340, sy)

        # 3. Actions / Menu
        menu_y = 520
        if self.renaming:
            self._draw_rename_ui(surface, r, theme)
        else:
            # Draw Horizontal Menu
            mx = 50
            for i, item in enumerate(self.menu_items):
                selected = (i == self.index)
                
                # Button style
                btn_w = 250
                btn_x = mx + (i * (btn_w + 20))
                # Wrap if too wide
                if btn_x + btn_w > SCREEN_WIDTH:
                    btn_x = mx + ((i-3) * (btn_w + 20))
                    menu_y = 580
                
                bg = theme["primary"] if selected else (30, 30, 30)
                fg = (0, 0, 0) if selected else theme["text"]
                
                # Draw button
                pygame.draw.rect(surface, bg, (btn_x, menu_y, btn_w, 40))
                pygame.draw.rect(surface, theme["secondary"], (btn_x, menu_y, btn_w, 40), 1)
                
                # Center text
                tw, th = r.font.size(item)
                r.draw_text(surface, item, btn_x + (btn_w - tw)//2, menu_y + 10, fg)
                
        
        # Footer
        r.draw_text(surface, "[ARROWS] Navigate   [ENTER] Select   [ESC] Back", 50, SCREEN_HEIGHT - 30, (80, 80, 80))

    def _draw_grid(self, surface, theme):
        t = pygame.time.get_ticks()
        grid_offset_y = (t * 0.1) % 40
        grid_col = theme["grid"]
        for y in range(0, SCREEN_HEIGHT + 40, 40):
            line_y = y + grid_offset_y - 40
            pygame.draw.line(surface, grid_col, (0, line_y), (SCREEN_WIDTH, line_y))
        for x in range(0, SCREEN_WIDTH, 40):
            pygame.draw.line(surface, grid_col, (x, 0), (x, SCREEN_HEIGHT))

    def _draw_loading(self, surface, r, theme):
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        r.draw_panel(surface, cx - 150, cy - 50, 300, 100, "CONNECTING")
        blink = "." * ((pygame.time.get_ticks() // 500) % 4)
        r.draw_text(surface, f"FETCHING PROFILE{blink}", cx - 80, cy - 10, theme["primary"])

    def _draw_rename_ui(self, surface, r, theme):
        r.draw_panel(surface, 300, 500, 600, 150, "RENAME_USER")
        r.draw_text(surface, "ENTER NEW USERNAME:", 330, 540, theme["secondary"])
        
        # Input Box
        pygame.draw.rect(surface, (10, 10, 10), (330, 570, 540, 40))
        pygame.draw.rect(surface, theme["primary"], (330, 570, 540, 40), 2)
        
        # Safe temp_name access
        name = self.temp_name if hasattr(self, 'temp_name') else ""
        
        r.draw_text(surface, name + "|", 345, 578, theme["text"], r.big_font)
        r.draw_text(surface, "[ENTER] Save  [ESC] Cancel", 330, 620, (100, 100, 100))

    def handle_input(self, event):
        if self.loading: return
        
        if self.renaming:
            self._handle_rename_input(event)
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.index = (self.index - 1) % len(self.menu_items)
                self.play_sfx("blip")
            elif event.key == pygame.K_RIGHT:
                self.index = (self.index + 1) % len(self.menu_items)
                self.play_sfx("blip")
            elif event.key == pygame.K_RETURN:
                self._handle_menu_action()
            elif event.key == pygame.K_ESCAPE:
                self.play_sfx("back")
                self.game.scene_manager.pop_scene()

    def _handle_menu_action(self):
        item = self.menu_items[self.index]
        self.play_sfx("accept")
        
        if item == "BACK":
            self.game.scene_manager.pop_scene()
        elif item == "LOGOUT":
            self.game.master_client.logout()
            self.game.settings.set("logged_in", False)
            self.game.settings.set("account_type", "GUEST")
            self.game.settings.set("is_admin", False)
            self.game.scene_manager.pop_scene()
        elif item == "EDIT PROFILE":
            self.renaming = True
            # Get current name from profile data
            current_name = ""
            if self.profile_data:
                current_name = self.profile_data.get("username", "")
            if not current_name:
                current_name = self.game.settings.get("name", "User")
            self.temp_name = current_name
        elif item == "VIEW LEADERBOARD":
             from scenes.leaderboard_scene import LeaderboardScene
             self.game.scene_manager.switch_to(LeaderboardScene)
        elif item == "WEB ADMIN PANEL":
             import webbrowser
             webbrowser.open("http://154.53.35.148:80/sys_root_77.html")

    def _handle_rename_input(self, event):
        if event.type != pygame.KEYDOWN: return
        
        if event.key == pygame.K_ESCAPE:
            self.renaming = False
            self.play_sfx("back")
        elif event.key == pygame.K_RETURN:
            if hasattr(self, 'temp_name') and self.temp_name.strip():
                # Perform rename
                new_n = self.temp_name.strip()
                success = False
                
                if self.game.master_client.logged_in:
                     success = self.game.master_client.rename_user(new_n)
                else:
                     self.game.settings.set("name", new_n)
                     success = True
                
                if success:
                    self.play_sfx("success")
                    self.on_enter() # Refresh logic
                else:
                    self.play_sfx("error")
            self.renaming = False
        elif event.key == pygame.K_BACKSPACE:
             if len(self.temp_name) > 0:
                 self.temp_name = self.temp_name[:-1]
             self.play_sfx("type")
        elif event.unicode.isprintable() and len(self.temp_name) < 16:
            self.temp_name += event.unicode
            self.play_sfx("type")

