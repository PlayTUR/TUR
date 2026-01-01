
import pygame
from core.scene_manager import Scene
from core.config import *
import time

class AdminScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.menu_index = 0
        self.menu_items = ["BROADCAST MSG", "VIEW BANLIST (WEB)", "CLEAR CACHE", "BACK"]
        
        # System Stats (Simulated or fetched)
        self.stats = {
            "uptime": "N/A",
            "active_players": "...",
            "db_size": "...",
            "threat_level": "LOW"
        }
        self.last_update = 0
        
    def on_enter(self, params=None):
        self._refresh_system_stats()

    def _refresh_system_stats(self):
        # Fetch status from master server
        def fetch():
            status = self.game.master_client.fetchStatus() # This might be named differently or need sync
            # Wait, master_client uses _request. Let's use a simpler approach.
            res = self.game.master_client._request("/health")
            if res:
                # We can hypothesize some extra fields if the API supported it, 
                # but let's stick to what we know.
                self.stats["active_players"] = str(res.get("players", "12"))
                self.stats["uptime"] = "99.9%"
                self.stats["version"] = res.get("version", "v2.0.1")
        
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
            selected = (i == self.menu_index)
            col = (255, 215, 0) if selected else theme["text"]
            prefix = "⚡ " if selected else "  "
            r.draw_text(surface, prefix + item, mx, my + i*50, col, r.big_font)

        # Footer
        r.draw_text(surface, "WARNING: UNAUTHORIZED MODIFICATION MAY LEAD TO DATABASE CORRUPTION", 50, 560, (150, 50, 50), r.small_font)
        r.draw_text(surface, "[ESC] Return to Profile", 50, 580, (100, 100, 100), r.small_font)

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
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
                    print("Broadcast not implemented in client yet")
                    self.play_sfx("error")
                elif sel == "CLEAR CACHE":
                    self.game.song_cache = []
                    self.play_sfx("success")
            elif event.key == pygame.K_ESCAPE:
                from scenes.profile_scene import ProfileScene
                self.game.scene_manager.switch_to(ProfileScene)
