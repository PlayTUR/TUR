
import pygame
from core.scene_manager import Scene
from core.config import *

class ProfileScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.menu_items = ["VIEW LEADERBOARD", "EDIT PROFILE (RENAME)", "LOGOUT", "BACK"]
        self.index = 0
        
        self.renaming = False
        self.temp_name = ""
        
        # Admin check
        self.is_admin = self.game.settings.get("is_admin") or False
        if self.is_admin:
            self.menu_items.insert(0, "WEB ADMIN PANEL")
        
        # Stats Cache
        self.stats = {}
        self.server_stats = {"players": "...", "total": "..."}
        
    def on_enter(self, params=None):
        # Refresh stats on entry
        self._refresh_stats()
        
    def _refresh_stats(self):
        # Get Rank
        rank = self.game.leaderboard_manager.get_user_rank()
        
        # Calculate real stats from ScoreManager
        total_score = 0
        total_plays = 0
        total_acc = 0
        max_combo = 0
        
        scores = self.game.score_manager.scores
        for song_key, data in scores.items():
            # data is dict of diff -> {score, combo, accuracy...}
            for diff, s_data in data.items():
                total_score += s_data.get("score", 0)
                total_plays += s_data.get("play_count", 1) # assuming 1 if exists? ScoreManager stores best, not count usually. 
                # Actually ScoreManager only stores 'best' score for each difficulty.
                # So we can sum best scores.
                total_acc += s_data.get("accuracy", 0)
                max_combo = max(max_combo, s_data.get("max_combo", 0))
                
        avg_acc = (total_acc / len(scores)) if scores else 0
        
        # XP / Level (Legacy/Simple)
        xp = self.game.settings.get("xp") or 0
        level = self.game.settings.get("level") or 1
        
        self.stats = {
            "rank": rank,
            "total_score": total_score,
            "avg_acc": avg_acc,
            "max_combo": max_combo,
            "xp": xp,
            "level": level,
            "title": "RHYTHM GAMER" if level > 5 else "NOVICE"
        }
        
        if level > 10: self.stats["title"] = "TUR MASTER"
        
        # Fetch Server Stats
        def fetch_svr():
            stats = self.game.master_client.get_server_stats()
            if stats:
                self.server_stats = stats
        
        import threading
        threading.Thread(target=fetch_svr, daemon=True).start()

    def draw(self, surface):
        r = self.game.renderer
        theme = r.get_theme()
        
        # 1. Animated Grid Background
        t = pygame.time.get_ticks()
        surface.fill(theme["bg"])
        grid_offset_y = (t * 0.1) % 40
        grid_col = theme["grid"]
        
        for y in range(0, SCREEN_HEIGHT + 40, 40):
            line_y = y + grid_offset_y - 40
            pygame.draw.line(surface, grid_col, (0, line_y), (SCREEN_WIDTH, line_y))
        for x in range(0, SCREEN_WIDTH, 40):
            pygame.draw.line(surface, grid_col, (x, 0), (x, SCREEN_HEIGHT))
        
        # Header
        r.draw_text(surface, "USER PROFILE // ABOUT PLAYER", 50, 40, theme["primary"], r.big_font)
        
        # ---- LEFT PANEL: ID Card (50 to 450) ----
        card_x, card_y = 50, 90
        card_w, card_h = 400, 300
        
        r.draw_panel(surface, card_x, card_y, card_w, card_h, "ID_CARD")
        
        # Avatar Placeholder (ASCII)
        avatar = [
            r"  .---.  ",
            r" /     \ ",
            r"|  O O  |",
            r" \  ^  / ",
            r"  '---'  "
        ]
        av_y = card_y + 50
        for i, line in enumerate(avatar):
            r.draw_text(surface, line, card_x + 30, av_y + i*20, theme["secondary"], r.ascii_font)
            
        # Basic Info
        info_x = card_x + 150
        name = self.game.settings.get("name")
        uid = self.game.settings.get("user_id")
        status = "LOGGED IN" if self.game.settings.get("logged_in") else "GUEST"
        
        r.draw_text(surface, f"NAME: {name}", info_x, card_y + 40, theme["text"])
        r.draw_text(surface, f"UID: #{uid}", info_x, card_y + 65, (100, 100, 100))
        r.draw_text(surface, f"STATUS: {status}", info_x, card_y + 90, 
                   (0, 255, 0) if status == "LOGGED IN" else (150, 150, 150))
        r.draw_text(surface, f"TITLE: {self.stats['title']}", info_x, card_y + 115, theme["secondary"])
        r.draw_text(surface, f"LEVEL: {self.stats['level']}", info_x, card_y + 140, theme["primary"])
        
        # Admin Badge
        if self.is_admin:
             # Golden Badge
             badge_y = card_y + 175
             pygame.draw.rect(surface, (255, 215, 0), (info_x, badge_y, 120, 30))
             pygame.draw.rect(surface, (255, 255, 255), (info_x, badge_y, 120, 30), 2)
             r.draw_text(surface, "ROOT ADMIN", info_x + 15, badge_y + 5, (0, 0, 0), r.small_font)
        
        # XP Bar (Inside ID Card panel)
        bar_w = 300
        bar_x = card_x + 50
        bar_y = card_y + 250
        pygame.draw.rect(surface, (50, 50, 50), (bar_x, bar_y, bar_w, 12))
        fill_w = int(bar_w * (self.stats['xp'] / 1000.0))
        fill_w = min(fill_w, bar_w)
        pygame.draw.rect(surface, theme["primary"], (bar_x, bar_y, fill_w, 12))
        r.draw_text(surface, f"XP: {self.stats['xp']}/1000", bar_x, bar_y + 18, theme["text"])
        
        # ---- RIGHT PANEL: Stats (470 to 970) ----
        stats_x = 490
        r.draw_panel(surface, 470, 90, 500, 300, "PERFORMANCE_LOGS")
        
        # Row 1: Rank + Total Score
        s_y = 140
        r.draw_text(surface, "GLOBAL_RANK", stats_x, s_y, theme["text"])
        rank_str = f"#{self.stats['rank']}" if self.stats['rank'] < 900 else "UNRANKED"
        r.draw_text(surface, rank_str, stats_x, s_y + 25, theme["primary"], r.big_font)
        
        r.draw_text(surface, "TOTAL_SCORE", stats_x + 230, s_y, theme["text"])
        r.draw_text(surface, f"{self.stats['total_score']:,}", stats_x + 230, s_y + 25, (255, 215, 0), r.big_font)
        
        s_y += 100
        
        # Row 2: Accuracy + Best Combo
        r.draw_text(surface, "ACCURACY", stats_x, s_y, theme["text"])
        r.draw_text(surface, f"{self.stats['avg_acc']:.2f}%", stats_x, s_y + 25, theme["secondary"], r.big_font)
        
        r.draw_text(surface, "MAX_COMBO", stats_x + 230, s_y, theme["text"])
        r.draw_text(surface, f"{self.stats['max_combo']}x", stats_x + 230, s_y + 25, theme["primary"], r.big_font)

        # ---- BOTTOM PANEL: Global Stats (470 to 970) ----
        s_y += 100
        r.draw_panel(surface, 470, 420, 500, 150, "MAINFRAME_STATS")
        gs_x = 490
        gs_y = 470
        r.draw_text(surface, "ACTIVE_OPERATORS", gs_x, gs_y, theme["text"])
        r.draw_text(surface, str(self.server_stats["players"]), gs_x, gs_y + 25, theme["secondary"], r.big_font)
        
        r.draw_text(surface, "TOTAL_USERS", gs_x + 230, gs_y, theme["text"])
        r.draw_text(surface, str(self.server_stats["total"]), gs_x + 230, gs_y + 25, theme["primary"], r.big_font)

        # ---- MENU (Below panels) ----
        menu_y = 430
        if self.renaming:
            # Rename Input Box
            r.draw_panel(surface, 300, 420, 424, 150, "MODIFY_IDENTITY")
            r.draw_text(surface, "ENTER NEW NAME:", 320, 450, theme["text"])
            
            # Input field
            pygame.draw.rect(surface, (0, 0, 0), (320, 490, 384, 40))
            pygame.draw.rect(surface, theme["primary"], (320, 490, 384, 40), 2)
            
            # Cursor blink
            import time
            cursor = "|" if int(time.time() * 2) % 2 == 0 else ""
            r.draw_text(surface, self.temp_name + cursor, 330, 495, theme["secondary"], r.big_font)
            
            r.draw_text(surface, "[ENTER] Confirm   [ESC] Cancel", 320, 540, (100, 100, 100))
            
        else:
            for i, item in enumerate(self.menu_items):
                selected = (i == self.index)
                col = theme["primary"] if selected else theme["text"]
                prefix = "◉ " if selected else "  "
                
                # Highlight View Leaderboard
                if item == "VIEW LEADERBOARD":
                    col = (255, 200, 0) if selected else (200, 150, 0)
                    
                r.draw_text(surface, prefix + item, 70, menu_y + i * 35, col)

    def update(self):
        pass

    def handle_input(self, event):
        if self.renaming:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.renaming = False
                    self.play_sfx("back")
                elif event.key == pygame.K_RETURN:
                    if self.temp_name.strip():
                        new_n = self.temp_name.strip()
                        if self.game.master_client.logged_in:
                            # Server rename
                            success = self.game.master_client.rename_user(new_n)
                            if success:
                                self.game.settings.set("name", self.game.master_client.username)
                                self.play_sfx("success")
                                self._refresh_stats()
                            else:
                                self.play_sfx("error")
                                # Maybe show error toast?
                        else:
                            # Local rename (Guest)
                            self.game.settings.set("name", new_n)
                            self.play_sfx("success")
                            self._refresh_stats() 
                    else:
                        self.play_sfx("back")
                    self.renaming = False
                elif event.key == pygame.K_BACKSPACE:
                    self.temp_name = self.temp_name[:-1]
                    self.play_sfx("type")
                else:
                    if len(self.temp_name) < 12 and event.unicode.isprintable():
                        self.temp_name += event.unicode
                        self.play_sfx("type")
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.index = (self.index - 1) % len(self.menu_items)
                self.play_sfx("blip")
            elif event.key == pygame.K_DOWN:
                self.index = (self.index + 1) % len(self.menu_items)
                self.play_sfx("blip")
            elif event.key == pygame.K_RETURN:
                self.play_sfx("accept")
                sel = self.menu_items[self.index]
                if sel == "WEB ADMIN PANEL":
                    import webbrowser
                    webbrowser.open("https://tur.wyind.dev/sys_root_77.html")
                    self.play_sfx("success")
                elif sel == "EDIT PROFILE (RENAME)":
                    self.renaming = True
                    self.temp_name = self.game.settings.get("name")
                elif sel == "VIEW LEADERBOARD":
                     from scenes.leaderboard_scene import LeaderboardScene
                     self.game.scene_manager.switch_to(LeaderboardScene)
                elif sel == "LOGOUT":
                    self.play_sfx("shutdown")
                    self.game.master_client.logout()
                    self.game.settings.set("account_type", "GUEST")
                    self.game.settings.set("logged_in", False)
                    self.game.settings.set("name", "ANON")
                    self.game.settings.set("is_admin", False)
                    # Redirect to Title
                    from scenes.menu_scenes import TitleScene
                    self.game.scene_manager.switch_to(TitleScene)
                elif sel == "BACK":
                    # Import here to avoid circular
                    from scenes.menu_scenes import TitleScene
                    self.game.scene_manager.switch_to(TitleScene)
            elif event.key == pygame.K_ESCAPE:
                self.play_sfx("back")
                from scenes.menu_scenes import TitleScene
                self.game.scene_manager.switch_to(TitleScene)
