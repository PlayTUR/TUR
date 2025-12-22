import pygame
import os
import json
from core.scene_manager import Scene
from scenes.menu_scenes import TitleScene
from core.config import *

class AdminScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.options = ["CHECK USER", "WIPE ALL SCORES", "BAN USER", "UNBAN USER", "EXIT"]
        self.selected_index = 0
        
        # States: MENU, INPUT_NAME, SELECT_DURATION, CONFIRM, SHOW_INFO
        self.state = "MENU"
        
        # Action Data
        self.target_user = ""
        self.ban_duration = ""
        self.confirm_action = None
        self.action_mode = "BAN" # BAN, UNBAN, CHECK
        self.user_info = {} # Cached info for check
        
        self.durations = ["1 DAY", "3 DAYS", "1 WEEK", "PERMANENT"]
        self.duration_index = 0

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
            
        # Draw Main Panel
        panel_w, panel_h = 800, 600
        panel_x = (SCREEN_WIDTH - panel_w) // 2
        panel_y = (SCREEN_HEIGHT - panel_h) // 2
        
        r.draw_panel(surface, panel_x, panel_y, panel_w, panel_h, "SECURE ADMIN TERMINAL")
        
        # Sub-header
        r.draw_text(surface, f"COMMANDER: {self.game.settings.get('name')}", panel_x + 30, panel_y + 40, theme["secondary"])
        r.draw_text(surface, f"UID: #{self.game.settings.get('user_id')}", panel_x + 600, panel_y + 40, (100, 100, 100))
        
        content_y = panel_y + 80
        
        if self.state == "MENU":
            start_y = content_y + 40
            for i, opt in enumerate(self.options):
                color = theme["primary"] if i == self.selected_index else theme["text"]
                prefix = "◉ " if i == self.selected_index else "  "
                r.draw_text(surface, f"{prefix}{opt}", panel_x + 50, start_y + i * 45, color, r.big_font)
                
        elif self.state == "INPUT_NAME":
            if self.action_mode == "CHECK": title = "ENTER USER TO INSPECT:"
            elif self.action_mode == "BAN": title = "ENTER USER TO BAN:"
            else: title = "ENTER USER TO UNBAN:"
            
            r.draw_text(surface, title, panel_x + 50, content_y + 50, theme["text"])
            r.draw_text(surface, f"> {self.target_user}_", panel_x + 50, content_y + 100, theme["primary"], r.big_font)
            r.draw_text(surface, "[ENTER] NEXT   [ESC] CANCEL", panel_x + 50, content_y + 250, theme["secondary"])

        elif self.state == "SHOW_INFO":
            r.draw_text(surface, f"REPORT: {self.target_user}", panel_x + 50, content_y + 20, theme["primary"], r.big_font)
            
            # Info
            info = self.user_info
            status = "BANNED" if info.get("banned") else "ACTIVE"
            col = theme["error"] if info.get("banned") else (0, 255, 0)
            
            r.draw_text(surface, f"STATUS: {status}", panel_x + 50, content_y + 80, col)
            if info.get("banned"):
                expires = info.get("expires_str", "UNKNOWN")
                r.draw_text(surface, f"EXPIRES: {expires}", panel_x + 50, content_y + 110, theme["secondary"])
                r.draw_text(surface, f"REASON: ADMIN_BAN", panel_x + 50, content_y + 140, theme["text"])
            else:
                r.draw_text(surface, "STANDING: GOOD", panel_x + 50, content_y + 110, theme["text"])
            
            r.draw_text(surface, "[ESC] BACK", panel_x + 50, content_y + 400, theme["secondary"])

        elif self.state == "SELECT_DURATION":
            r.draw_text(surface, f"BANNING: {self.target_user}", panel_x + 50, content_y + 20, theme["secondary"])
            r.draw_text(surface, "SELECT DURATION:", panel_x + 50, content_y + 70, theme["text"])
            
            for i, dur in enumerate(self.durations):
                color = theme["primary"] if i == self.duration_index else theme["text"]
                prefix = "> " if i == self.duration_index else "  "
                r.draw_text(surface, f"{prefix}{dur}", panel_x + 50, content_y + 130 + i * 40, color, r.big_font)
            
            r.draw_text(surface, "[ENTER] NEXT   [ESC] BACK", panel_x + 50, content_y + 400, theme["secondary"])

        elif self.state == "CONFIRM":
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(200)
            overlay.fill((0,0,0))
            surface.blit(overlay, (0,0))
            
            if self.confirm_action == "WIPE ALL SCORES":
                msg = "WIPE ALL LEADERBOARDS?"
                sub = "CANNOT BE UNDONE"
            elif self.confirm_action == "UNBAN_USER":
                msg = f"UNBAN {self.target_user}?"
                sub = "RESTORE ACCESS"
            else:
                msg = f"BAN {self.target_user}?"
                sub = f"DURATION: {self.ban_duration}"
            
            r.draw_text(surface, msg, SCREEN_WIDTH//2 - 200, SCREEN_HEIGHT//2 - 50, theme["primary"], r.big_font)
            r.draw_text(surface, sub, SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT//2, theme["secondary"])
            r.draw_text(surface, "[ENTER] EXECUTE   [ESC] CANCEL", SCREEN_WIDTH//2 - 180, SCREEN_HEIGHT//2 + 80, theme["text"])

    def handle_input(self, event):
        if event.type != pygame.KEYDOWN:
            return

        if self.state == "MENU":
            if event.key == pygame.K_ESCAPE:
                self.game.scene_manager.pop_scene()
            elif event.key == pygame.K_UP:
                self.selected_index = (self.selected_index - 1) % len(self.options)
                self.play_sfx("blip")
            elif event.key == pygame.K_DOWN:
                self.selected_index = (self.selected_index + 1) % len(self.options)
                self.play_sfx("blip")
            elif event.key == pygame.K_RETURN:
                self.play_sfx("accept")
                choice = self.options[self.selected_index]
                
                if choice == "EXIT":
                    self.game.scene_manager.pop_scene()
                elif choice == "CHECK USER":
                    self.action_mode = "CHECK"
                    self.state = "INPUT_NAME"
                    self.target_user = ""
                elif choice == "BAN USER":
                    self.action_mode = "BAN"
                    self.state = "INPUT_NAME"
                    self.target_user = ""
                elif choice == "UNBAN USER":
                    self.action_mode = "UNBAN"
                    self.state = "INPUT_NAME"
                    self.target_user = ""
                elif choice == "WIPE ALL SCORES":
                    self.confirm_action = "WIPE ALL SCORES"
                    self.state = "CONFIRM"
                    
        elif self.state == "INPUT_NAME":
            if event.key == pygame.K_ESCAPE:
                self.state = "MENU"
            elif event.key == pygame.K_RETURN:
                if self.target_user.strip():
                     self.play_sfx("accept")
                     if self.action_mode == "BAN":
                         self.state = "SELECT_DURATION"
                         self.duration_index = 0
                     elif self.action_mode == "CHECK":
                         self.check_user(self.target_user)
                         self.state = "SHOW_INFO"
                     else:
                         # UNBAN - skip duration
                         self.confirm_action = "UNBAN_USER"
                         self.state = "CONFIRM"
            elif event.key == pygame.K_BACKSPACE:
                self.play_sfx("blip")
                self.target_user = self.target_user[:-1]
            elif len(self.target_user) < 16 and event.unicode.isprintable():
                self.play_sfx("type")
                self.target_user += event.unicode.upper()

        elif self.state == "SHOW_INFO":
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN:
                self.state = "MENU"
        
        elif self.state == "SELECT_DURATION":
            if event.key == pygame.K_ESCAPE:
                self.state = "INPUT_NAME"
            elif event.key == pygame.K_UP:
                self.duration_index = (self.duration_index - 1) % len(self.durations)
                self.play_sfx("blip")
            elif event.key == pygame.K_DOWN:
                self.duration_index = (self.duration_index + 1) % len(self.durations)
                self.play_sfx("blip")
            elif event.key == pygame.K_RETURN:
                self.play_sfx("accept")
                self.ban_duration = self.durations[self.duration_index]
                self.confirm_action = "BAN_USER"
                self.state = "CONFIRM"

        elif self.state == "CONFIRM":
            if event.key == pygame.K_ESCAPE:
                self.state = "MENU" # Reset to menu or back step? Menu is safer
            elif event.key == pygame.K_RETURN:
                self.play_sfx("shutdown")
                if self.confirm_action == "WIPE ALL SCORES":
                    self.wipe_scores()
                elif self.confirm_action == "BAN_USER":
                    self.ban_user(self.target_user, self.ban_duration)
                elif self.confirm_action == "UNBAN_USER":
                    self.unban_user(self.target_user)
                
                self.state = "MENU"

    def check_user(self, username):
        bans = self._load_bans()
        import datetime
        
        info = {"banned": False}
        if username in bans:
            info["banned"] = True
            expires = bans[username].get("expires", 0)
            import datetime
            dt = datetime.datetime.fromtimestamp(expires)
            info["expires_str"] = dt.strftime("%Y-%m-%d")
        
        self.user_info = info
            
    def wipe_scores(self):
        try:
             if os.path.exists("scores.json"):
                 os.remove("scores.json")
                 print("Scores wiped.")
                 self.game.score_manager.scores = {} 
        except Exception as e:
            print(f"Error wiping scores: {e}")

    def ban_user(self, username, duration_str):
        import time
        bans = self._load_bans()
        
        # Calc expiration
        duration_map = {
            "1 DAY": 86400,
            "3 DAYS": 86400 * 3,
            "1 WEEK": 86400 * 7,
            "PERMANENT": 31536000 * 100 # 100 Years
        }
        seconds = duration_map.get(duration_str, 86400)
        expires = time.time() + seconds
        
        bans[username] = {
            "expires": expires,
            "duration_str": duration_str,
            "banned_by": self.game.settings.get("name")
        }
        self._save_bans(bans)
        print(f"Banned {username} until {expires}")

    def unban_user(self, username):
        bans = self._load_bans()
        if username in bans:
            del bans[username]
            self._save_bans(bans)
            print(f"Unbanned {username}")
        else:
             print(f"User {username} not found in ban list.")

    def _load_bans(self):
        if os.path.exists("bans.json"):
            try:
                with open("bans.json", "r") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_bans(self, bans):
        try:
            with open("bans.json", "w") as f:
                json.dump(bans, f, indent=4)
        except Exception as e:
            print(f"Error saving bans: {e}")
