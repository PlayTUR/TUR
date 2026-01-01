import pygame
from core.scene_manager import Scene
from core.config import *
import threading
from core.localization import get_text

class LeaderboardScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.leaderboard_data = []
        self.my_stats = None
        self.loading = True
        self.error = None
        self.scroll_y = 0
        self.target_scroll_y = 0
        
    def on_enter(self, params=None):
        self.loading = True
        self.error = None
        self.leaderboard_data = []
        self.my_stats = None
        self.scroll_y = 0
        self.target_scroll_y = 0
        
        # Fetch data in background
        threading.Thread(target=self._fetch_data, daemon=True).start()
        
    def _fetch_data(self):
        try:
            # Fetch global leaderboard
            self.leaderboard_data = self.game.master_client.get_leaderboard()
            
            # Fetch own stats if logged in
            if self.game.master_client.logged_in:
                self.my_stats = self.game.master_client.get_my_stats()
            
            self.loading = False
        except Exception as e:
            self.error = str(e)
            self.loading = False
            
    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.play_sfx("back")
                # Return to Lobby
                from scenes.lobby_scene import LobbyScene
                self.game.scene_manager.switch_to(LobbyScene)
            elif event.key == pygame.K_UP:
                self.target_scroll_y = max(0, self.target_scroll_y - 80)
            elif event.key == pygame.K_DOWN:
                # Cap scroll
                max_h = max(0, len(self.leaderboard_data) * 40 - 450)
                self.target_scroll_y = min(max_h, self.target_scroll_y + 80)
            elif event.key == pygame.K_F5:
                # Refresh
                self.on_enter()
                
    def draw(self, surface):
        r = self.game.renderer
        theme = r.get_theme()
        
        # Background
        surface.fill(theme["bg"])
        
        # Header
        r.draw_text(surface, "◉ GLOBAL LEADERBOARD ◉", 50, 30, theme["primary"], r.big_font)
        
        if self.loading:
            r.draw_centered_text(surface, "LOADING DATA...", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, theme["secondary"])
            return
            
        if self.error:
             r.draw_centered_text(surface, f"ERROR: {self.error}", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, theme["error"])
             r.draw_centered_text(surface, "[F5] Retry  [ESC] Back", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40, (150, 150, 150))
             return
        
        # Scroll smoothing
        self.scroll_y += (self.target_scroll_y - self.scroll_y) * 0.2
        
        # My Stats Panel
        panel_y = 90
        if self.my_stats and not self.my_stats.get("error"):
            r.draw_panel(surface, 50, panel_y, 924, 80, "MY STATS")
            
            ms = self.my_stats
            # Level / XP
            r.draw_text(surface, f"LEVEL {ms.get('level', 1)}", 80, panel_y + 40, theme["primary"], r.big_font)
            
            # XP Bar
            xp = ms.get('xp', 0)
            r.draw_text(surface, f"XP: {xp:,}", 250, panel_y + 48, theme["text"])
            
            r.draw_text(surface, f"TOTAL SCORE: {ms.get('total_score', 0):,}", 500, panel_y + 48, theme["secondary"])
            r.draw_text(surface, f"PLAYS: {ms.get('plays', 0)}", 750, panel_y + 48, (150, 150, 150))
        elif self.game.master_client.logged_in:
             # Logged in but failed to fetch stats? Or just empty stats?
             r.draw_panel(surface, 50, panel_y, 924, 60, "MY STATS")
             r.draw_centered_text(surface, "Fetching performance data...", SCREEN_WIDTH // 2, panel_y + 35, (150, 150, 150))
        else:
             r.draw_panel(surface, 50, panel_y, 924, 60, "MY STATS")
             r.draw_centered_text(surface, "Login to track stats!", SCREEN_WIDTH // 2, panel_y + 35, (100, 100, 100))
            
        # Leaderboard List
        list_y = 200
        list_h = 450
        list_w = 924
        list_x = 50
        
        r.draw_panel(surface, list_x, list_y, list_w, list_h, "TOP PLAYERS")
        
        # Headers
        header_y = list_y + 40
        r.draw_text(surface, "#", list_x + 20, header_y, (100, 100, 100))
        r.draw_text(surface, "PLAYER", list_x + 80, header_y, (100, 100, 100))
        r.draw_text(surface, "LEVEL", list_x + 400, header_y, (100, 100, 100))
        r.draw_text(surface, "XP", list_x + 550, header_y, (100, 100, 100))
        r.draw_text(surface, "SCORE", list_x + 750, header_y, (100, 100, 100))
        
        pygame.draw.line(surface, theme["grid"], (list_x + 10, header_y + 25), (list_x + list_w - 10, header_y + 25))
        
        # Entries
        items_area = pygame.Rect(list_x + 10, header_y + 30, list_w - 20, list_h - 80)
        # Clip to area
        old_clip = surface.get_clip()
        
        # For smooth scrolling with clip, we adjust y directly
        
        surface.set_clip(items_area)
        
        entry_y = header_y + 30 - self.scroll_y
        
        for i, entry in enumerate(self.leaderboard_data):
            # Visibilty Check
            if entry_y > items_area.bottom:
                break
            if entry_y + 30 < items_area.top:
                entry_y += 35
                continue
                
            rank = i + 1
            rank_col = theme["secondary"] if rank <= 3 else theme["text"]
            if rank == 1: rank_col = (255, 215, 0) # Gold
            elif rank == 2: rank_col = (192, 192, 192) # Silver
            elif rank == 3: rank_col = (205, 127, 50) # Bronze
            
            # Is me?
            is_me = self.my_stats and entry['username'] == self.game.settings.get("name")
            bg = (*theme["primary"], 50) if is_me else None
            
            if bg:
                s = pygame.Surface((list_w - 30, 30), pygame.SRCALPHA)
                s.fill(bg)
                surface.blit(s, (list_x + 15, entry_y))
            
            r.draw_text(surface, f"#{rank}", list_x + 20, entry_y + 5, rank_col)
            
            u_name = entry['username']
            r.draw_text(surface, u_name, list_x + 80, entry_y + 5, theme["text"])
            
            # Admin Tag
            if entry.get('is_admin'):
                r.draw_text(surface, "[ROOT]", list_x + 80 + r.font.size(u_name)[0] + 10, entry_y + 5, (255, 215, 0), r.small_font)

            r.draw_text(surface, str(entry['level']), list_x + 400, entry_y + 5, theme["secondary"])
            r.draw_text(surface, f"{entry['xp']:,}", list_x + 550, entry_y + 5, (150, 150, 150))
            r.draw_text(surface, f"{entry['score']:,}", list_x + 750, entry_y + 5, theme["primary"])
            
            entry_y += 35
            
        surface.set_clip(old_clip)
        
        # Scroll hint
        if len(self.leaderboard_data) * 35 > list_h - 80:
             bar_h = list_h - 80
             pct = self.scroll_y / max(1, (len(self.leaderboard_data) * 35 - bar_h))
             pct = max(0, min(1, pct))
             
             # Scrollbar
             sb_h = max(20, bar_h * (bar_h / (len(self.leaderboard_data) * 35)))
             sb_y = header_y + 30 + (bar_h - sb_h) * pct
             pygame.draw.rect(surface, (50, 50, 50), (list_x + list_w - 8, header_y + 30, 6, bar_h))
             pygame.draw.rect(surface, theme["secondary"], (list_x + list_w - 8, sb_y, 6, sb_h))
             
        # Controls
        r.draw_text(surface, "[ESC] Back", 50, SCREEN_HEIGHT - 40, theme["secondary"])
