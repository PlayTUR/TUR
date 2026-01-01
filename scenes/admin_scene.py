
import pygame
from core.scene_manager import Scene
from core.config import *
import time

class AdminScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.menu_index = 0
        self.menu_items = ["WIPE USER STATS", "BROADCAST MSG", "VIEW BANLIST (WEB)", "CLEAR CACHE", "BACK"]
        
        # System Stats (Simulated or fetched)
        self.stats = {
            "uptime": "N/A",
            "active_players": "...",
            "db_size": "...",
            "threat_level": "LOW"
        }
        self.state = "MENU" # MENU, WIPE_INPUT, CONFIRMING
        self.input_buffer = ""
        self.last_update = 0
        self.status_msg = ""
        self.status_timer = 0
        
    def on_enter(self, params=None):
        self._refresh_system_stats()
        self.state = "MENU"
        self.input_buffer = ""

    def _refresh_system_stats(self):
        # Fetch status from master server
        def fetch():
            res = self.game.master_client._request("/health")
            if res:
                self.stats["active_players"] = str(res.get("players", "12"))
                self.stats["uptime"] = "99.9%"
                self.stats["version"] = res.get("version", "v1.0.0")
        
        import threading
        threading.Thread(target=fetch, daemon=True).start()

    def draw(self, surface):
        r = self.game.renderer
        theme = r.get_theme()
        
        # 1. Background Grid Effect
        surface.fill(theme["bg"])
        t = pygame.time.get_ticks()
        grid_offset_y = (t * 0.1) % 40
        grid_col = theme["grid"]
        for y in range(0, SCREEN_HEIGHT, 40):
            line_y = y + grid_offset_y - 40
            pygame.draw.line(surface, grid_col, (0, line_y), (SCREEN_WIDTH, line_y))
        for x in range(0, SCREEN_WIDTH, 40):
            pygame.draw.line(surface, grid_col, (x, 0), (x, SCREEN_HEIGHT))

        # Header
        r.draw_text(surface, "SYSTEM_ADMINISTRATION // ROOT_ACCESS_GRANTED", 50, 40, (255, 215, 0), r.big_font)
        
        # --- LEFT: System Status ---
        r.draw_panel(surface, 50, 100, 400, 400, "MAINFRAME_HEALTH")
        sx, sy = 80, 150
        r.draw_text(surface, f"STATUS: [ NOMINAL ]", sx, sy, (100, 255, 100))
        r.draw_text(surface, f"UPTIME: {self.stats['uptime']}", sx, sy + 30, theme["text"])
        r.draw_text(surface, f"THREADS: {threading.active_count()}", sx, sy + 60, theme["text"])
        r.draw_text(surface, f"ACTIVE_OPERATORS: {self.stats['active_players']}", sx, sy + 90, theme["secondary"])
        r.draw_text(surface, f"THREAT_LEVEL: {self.stats['threat_level']}", sx, sy + 120, (255, 50, 50) if self.stats["threat_level"] != "LOW" else theme["primary"])
        
        # --- RIGHT: Control Matrix ---
        r.draw_panel(surface, 500, 100, 450, 400, "COMMAND_MATRIX")
        mx, my = 530, 160
        for i, item in enumerate(self.menu_items):
            selected = (i == self.menu_index) and self.state == "MENU"
            col = (255, 215, 0) if selected else theme["text"]
            prefix = "⚡ " if selected else "  "
            r.draw_text(surface, prefix + item, mx, my + i*50, col, r.big_font)

        # Draw Overlay for Input
        if self.state == "WIPE_INPUT":
            r.draw_high_viz_popup(surface, "WIPE_USER_STATS", "Enter Username to PURGE stats:")
            # Draw input field manually over the popup
            r.draw_text(surface, f"> {self.input_buffer}_", 300, 360, theme["primary"], r.big_font)
            r.draw_text(surface, "[ENTER] Confirm  [ESC] Cancel", 370, 420, (150, 150, 150), r.small_font)
            
        elif self.state == "CONFIRMING":
            msg = f"ARE YOU SURE YOU WANT TO WIPE {self.input_buffer}?"
            r.draw_high_viz_popup(surface, "CRITICAL_CONFIRMATION", msg, color=(255, 50, 50))
            r.draw_text(surface, "[ENTER] PURGE DATA  [ESC] ABORT", 350, 420, (150, 150, 150), r.small_font)

        # Status Message
        if time.time() < self.status_timer:
            r.draw_text(surface, self.status_msg, 50, 530, theme["primary"])

        # Footer
        r.draw_text(surface, "WARNING: UNAUTHORIZED MODIFICATION MAY LEAD TO DATABASE CORRUPTION", 50, 560, (150, 50, 50), r.small_font)
        r.draw_text(surface, "[ESC] Return to Profile", 50, 580, (100, 100, 100), r.small_font)

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if self.state == "MENU":
                if event.key == pygame.K_UP:
                    self.menu_index = (self.menu_index - 1) % len(self.menu_items)
                    self.play_sfx("blip")
                elif event.key == pygame.K_DOWN:
                    self.menu_index = (self.menu_index + 1) % len(self.menu_items)
                    self.play_sfx("blip")
                elif event.key == pygame.K_RETURN:
                    sel = self.menu_items[self.menu_index]
                    if sel == "BACK":
                        from scenes.profile_scene import ProfileScene
                        self.game.scene_manager.switch_to(ProfileScene)
                    elif sel == "VIEW BANLIST (WEB)":
                        import webbrowser
                        webbrowser.open("https://tur.wyind.dev/sys_root_77.html")
                    elif sel == "BROADCAST MSG":
                        self._show_status("Broadcasting not yet linked to API")
                        self.play_sfx("error")
                    elif sel == "CLEAR CACHE":
                        self.game.song_cache = []
                        self._show_status("CACHE_CLEARED_SUCCESSFULLY")
                        self.play_sfx("success")
                    elif sel == "WIPE USER STATS":
                        self.state = "WIPE_INPUT"
                        self.input_buffer = ""
                        self.play_sfx("blip")
                elif event.key == pygame.K_ESCAPE:
                    from scenes.profile_scene import ProfileScene
                    self.game.scene_manager.switch_to(ProfileScene)
            
            elif self.state == "WIPE_INPUT":
                if event.key == pygame.K_ESCAPE:
                    self.state = "MENU"
                elif event.key == pygame.K_RETURN:
                    if self.input_buffer:
                        self.state = "CONFIRMING"
                elif event.key == pygame.K_BACKSPACE:
                    self.input_buffer = self.input_buffer[:-1]
                elif event.unicode.isprintable():
                    if len(self.input_buffer) < 20:
                        self.input_buffer += event.unicode
                        
            elif self.state == "CONFIRMING":
                if event.key == pygame.K_ESCAPE:
                    self.state = "MENU"
                elif event.key == pygame.K_RETURN:
                    self._execute_wipe()
                    self.state = "MENU"

    def _execute_wipe(self):
        def _thread():
            import threading
            target = self.input_buffer
            res = self.game.master_client._request("/api/v2/admin/wipe-stats", "POST", {"username": target})
            if res and res.get("success"):
                self._show_status(f"PURGED: {target}")
                self.play_sfx("success")
            else:
                err = self.game.master_client.error or "Action Failed"
                self._show_status(f"ERROR: {err}")
                self.play_sfx("error")
        
        import threading
        threading.Thread(target=_thread, daemon=True).start()

    def _show_status(self, msg):
        self.status_msg = f">> {msg}"
        self.status_timer = time.time() + 3
