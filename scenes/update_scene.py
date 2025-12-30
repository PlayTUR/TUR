"""
Update Scene - Shows update status and download progress
"""

import pygame
from core.scene_manager import Scene
from core.config import *
from core.updater import get_updater
import webbrowser


class UpdateScene(Scene):
    def on_enter(self, params=None):
        # Get update source from settings
        source = self.game.settings.get("update_source") or "github"
        self.updater = get_updater(source)
        self.progress = 0
        self.state = "CHECKING"
        
        # Set status message based on source
        source_name = source.upper() if source else "GITHUB"
        self.status_msg = f"CHECKING {source_name} FOR UPDATES..."
        self.generator = None
        self.blink_timer = 0
        
        # Start checking for updates
        self._start_check()
    
    def _start_check(self):
        """Start update check"""
        import threading
        def check_thread():
            self.updater.check_for_updates()
            if self.updater.update_available:
                self.state = "UPDATE_AVAILABLE"
                self.status_msg = "NEW VERSION AVAILABLE!"
                self.progress = 100
            elif self.updater.error_message:
                self.state = "ERROR"
                self.status_msg = self.updater.error_message
            else:
                self.state = "UP_TO_DATE"
                self.status_msg = "SYSTEM IS UP TO DATE"
                self.progress = 100
        
        threading.Thread(target=check_thread, daemon=True).start()

    def update(self):
        self.blink_timer = (self.blink_timer + 1) % 60
        
        if self.state == "CHECKING":
            # Animate progress while checking
            if self.progress < 90:
                self.progress += 2
            self.status_msg = self.updater.status_message or "CONNECTING..."
                    
        elif self.state == "DOWNLOADING":
            try:
                self.progress = next(self.generator)
                self.status_msg = self.updater.status_message or "DOWNLOADING..."
            except StopIteration:
                self.state = "COMPLETE"
                self.status_msg = "UPDATE DOWNLOADED!"
                self.progress = 100
                
        elif self.state == "COMPLETE":
            pass  # Wait for user to press key

    def draw(self, surface):
        r = self.game.renderer
        theme = r.get_theme()
        surface.fill(theme["bg"])
        
        r.draw_text(surface, "◉ SYSTEM UPDATE ◉", 50, 30, theme["primary"], r.big_font)
        
        # Current version info
        r.draw_panel(surface, 100, 120, 400, 120, "CURRENT_VERSION")
        r.draw_text(surface, f"Build: {self.updater.current_version[:20]}", 130, 155, theme["text"])
        
        # Remote version info
        if self.updater.remote_build_info:
            r.draw_panel(surface, 520, 120, 400, 120, "LATEST_VERSION")
            info = self.updater.remote_build_info
            r.draw_text(surface, f"Commit: {info.get('head_sha', 'unknown')}", 550, 155, theme["secondary"])
            r.draw_text(surface, f"Built: {info.get('created_at', '')[:19]}", 550, 185, (120, 120, 120))
        
        # Status panel
        r.draw_panel(surface, 100, 280, 820, 200, "STATUS")
        
        # Status message (centered)
        status_color = theme["primary"]
        if self.state == "ERROR":
            status_color = theme["error"]
        elif self.state == "UP_TO_DATE":
            status_color = theme["secondary"]
        elif self.state == "UPDATE_AVAILABLE":
            # Flashing green
            if self.blink_timer < 30:
                status_color = (50, 255, 50)
            else:
                status_color = (0, 200, 100)
        
        r.draw_text(surface, self.status_msg, 150, 330, status_color, r.big_font)
        
        # Progress bar
        bar_x, bar_y = 130, 400
        bar_w, bar_h = 760, 30
        pygame.draw.rect(surface, theme["grid"], (bar_x, bar_y, bar_w, bar_h), 2)
        fill_w = int((bar_w - 4) * (self.progress / 100))
        if fill_w > 0:
            pygame.draw.rect(surface, theme["primary"], (bar_x + 2, bar_y + 2, fill_w, bar_h - 4))
        
        pct_text = f"{int(self.progress)}%"
        r.draw_text(surface, pct_text, bar_x + bar_w // 2 - 20, bar_y + 5, theme["bg"])
        
        # Action buttons
        if self.state == "UPDATE_AVAILABLE":
            r.draw_text(surface, "[ENTER] Open GitHub Releases", 150, 520, theme["secondary"])
            r.draw_text(surface, "[D] Download in Browser", 150, 555, (150, 150, 150))
            r.draw_text(surface, "[ESC] Back", 150, 590, (100, 100, 100))
            
            # Instructions
            r.draw_panel(surface, 550, 510, 370, 120, "HOW_TO_UPDATE")
            r.draw_text(surface, "1. Download from GitHub", 570, 545, theme["text"])
            r.draw_text(surface, "2. Extract over this folder", 570, 575, theme["text"])
            r.draw_text(surface, "3. Restart game!", 570, 605, theme["text"])
        elif self.state == "ERROR":
            r.draw_text(surface, "[R] Retry", 150, 520, theme["secondary"])
            r.draw_text(surface, "[ESC] Back", 150, 555, (100, 100, 100))
        elif self.state == "UP_TO_DATE":
            r.draw_text(surface, "✓ No updates needed", 150, 520, (100, 255, 100))
            r.draw_text(surface, "[ESC] Back", 150, 555, (100, 100, 100))
        else:
            # Still checking
            dots = "." * ((self.blink_timer // 15) % 4)
            r.draw_text(surface, f"Please wait{dots}", 150, 520, (100, 100, 100))

    def handle_input(self, event):
        if event.type != pygame.KEYDOWN:
            return
            
        if event.key == pygame.K_ESCAPE:
            self.play_sfx("back")
            from scenes.menu_scenes import TitleScene
            self.game.scene_manager.switch_to(TitleScene)
        
        elif event.key == pygame.K_RETURN and self.state == "UPDATE_AVAILABLE":
            # Open GitHub releases page
            self.play_sfx("accept")
            try:
                from core.updater import GITHUB_OWNER, GITHUB_REPO
                url = f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/releases"
                webbrowser.open(url)
            except Exception as e:
                print(f"Failed to open browser: {e}")
        
        elif event.key == pygame.K_d and self.state == "UPDATE_AVAILABLE":
            # Open actions artifacts page
            self.play_sfx("blip")
            try:
                from core.updater import GITHUB_OWNER, GITHUB_REPO
                url = f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/actions"
                webbrowser.open(url)
            except Exception as e:
                print(f"Failed to open browser: {e}")
        
        elif event.key == pygame.K_r and self.state == "ERROR":
            self.play_sfx("accept")
            self.state = "CHECKING"
            self.progress = 0
            self._start_check()
