import pygame
from core.scene_manager import Scene
from core.config import *
import os
import math
import webbrowser
from core.localization import get_text

VERSION = "Private Beta 1"

class TitleScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.game.discord.update("In Main Menu", "Waiting for command...")
        import random
        self.quotes = [
            "INITIALIZING KERNEL...",
            "LOADING ASSETS... [||||||||||]",
            "ERROR 418: I'M A TEAPOT",
            "ALL YOUR BASE ARE BELONG TO US",
            "HACK THE PLANET",
            "IT WORKS ON MY MACHINE",
            "SUDO MAKE ME A SANDWICH",
            "INSERT COIN TO CONTINUE",
            "BUFFER OVERFLOW DETECTED",
            "TUR? MORE LIKE TURD",
            "NOW WITH 100% MORE BUGS",
            "PRESS F TO PAY RESPECTS",
        ]
        self.quote = random.choice(self.quotes)
        
        # Menu Options
        self.menu_items = ["PLAY", "MULTIPLAYER", "REPLAYS", "OPTIONS", "CREDITS", "HOW TO PLAY"]
        if pygame.joystick.get_count() > 0:
            self.menu_items.insert(5, "CONTROLLER CONFIG")
        self.menu_items.append("SUPPORT")
        self.menu_items.append("EXIT")
        
        self.selected_index = 0
        self.show_exit_confirm = False
        self.show_donate_confirm = False
        
        # Update notification
        # Uses self.game.updater.update_available instead of local state

        
        # Auto-convert counter
        self.converting = False
        self.convert_count = 0
        self.convert_status = ""
        self.convert_pct = 0

    def on_enter(self, params=None):
        self.game.discord.update("In Main Menu", "Waiting for command...")
        if self.game.settings.get("vim_mode"):
            self.quote = "HOW DO I QUIT VIM?"
        else:
            import random
            self.quote = random.choice(self.quotes)

        if not pygame.mixer.music.get_busy():
            self.game.play_menu_bgm()
        
        # Check for updates logic moved to main.py global updater

        
        # Auto-convert MP3s to TUR on title screen entry
        self._start_auto_convert()

    def _start_auto_convert(self):
        """Check for and convert any MP3s without .tur files"""
        import threading
        def convert_thread():
            self.converting = True
            
            def progress_callback(status, pct):
                self.convert_status = status
                self.convert_pct = pct
                
            try:
                from core.song_converter import auto_convert_songs
                auto_convert_songs("songs", "MEDIUM", callback=progress_callback)
            except Exception as e:
                print(f"Auto-convert error: {e}")
            finally:
                self.converting = False
                # Refresh cache after auto-convert
                try:
                    from core.song_converter import preload_all_songs
                    self.game.song_cache = preload_all_songs("songs")
                except: pass
        
        threading.Thread(target=convert_thread, daemon=True).start()

    def update(self):
        super().update()
        
        # Check global updater status
        if hasattr(self.game, 'updater') and self.game.updater.update_available:
            # Add option if missing
            if "SYSTEM UPDATE" not in self.menu_items:
                # Insert before "SUPPORT" if present, else append before EXIT
                if "SUPPORT" in self.menu_items:
                    idx = self.menu_items.index("SUPPORT")
                    self.menu_items.insert(idx, "SYSTEM UPDATE")
                else:
                    # Insert before EXIT (last item)
                    self.menu_items.insert(len(self.menu_items)-1, "SYSTEM UPDATE")


    def draw(self, surface):
        theme = self.game.renderer.get_theme()
        
        # 1. Background Grid Effect
        t = pygame.time.get_ticks()
        
        # Get actual screen dimensions
        sw = surface.get_width()
        sh = surface.get_height()
        
        # Draw BG
        surface.fill(theme["bg"])
        
        grid_offset_y = (t * 0.1) % 40
        grid_col = theme["grid"]
        
        # Horizontal
        for y in range(0, sh + 40, 40):
            line_y = y + grid_offset_y - 40
            pygame.draw.line(surface, grid_col, (0, line_y), (sw, line_y))
            
        # Vertical
        for x in range(0, sw, 40):
            pygame.draw.line(surface, grid_col, (x, 0), (x, sh))

        # 2. Main Title (ASCII TUR)
        # Menu Music is 100 BPM -> 600ms per beat
        beat_dur = 600 
        beat_prog = (t % beat_dur) / beat_dur
        pulse = pow(1.0 - beat_prog, 3) 
        
        # TUR ASCII
        tur_art = [
            "████████╗██╗   ██╗██████╗ ",
            "╚══██╔══╝██║   ██║██╔══██╗",
            "   ██║   ██║   ██║██████╔╝",
            "   ██║   ██║   ██║██╔══██╗",
            "   ██║   ╚██████╔╝██║  ██║",
            "   ╚═╝    ╚═════╝ ╚═╝  ╚═╝"
        ]
        
        # Pulse for color intensity (0.5 to 1.0)
        color_pulse = 0.6 + (pulse * 0.4)
        
        # Helper to scale color
        def scale_col(color, factor):
            return (
                min(255, int(color[0] * factor)),
                min(255, int(color[1] * factor)),
                min(255, int(color[2] * factor))
            )

        start_y = 100
        
        for i, line in enumerate(tur_art):
            # Alternate primary/secondary colors
            base_c = theme["primary"] if i % 2 == 0 else theme["secondary"]
            c = scale_col(base_c, color_pulse) 
            
            font = self.game.renderer.ascii_font 
            w, h = font.size(line)
            x = (SCREEN_WIDTH - w) // 2
            
            # Draw (No bounce, just color pulse)
            self.game.renderer.draw_text(surface, line, x, start_y + i * 20, c, font)

        # Draw Quote - BRIGHTER color for readability
        quote_color = theme["secondary"] if not self.game.settings.get("vim_mode") else theme["primary"]
        quote_text = f"> {self.quote} <" if not self.game.settings.get("vim_mode") else self.quote
        q_surf = self.game.renderer.font.render(quote_text, False, quote_color)
        q_rect = q_surf.get_rect(center=(sw//2, 280))
        surface.blit(q_surf, q_rect)
        
        # Controller Detection UI
        joy_count = pygame.joystick.get_count()
        if joy_count > 0:
            joy_name = pygame.joystick.Joystick(0).get_name()
            # Truncate
            if len(joy_name) > 15: joy_name = joy_name[:15] + "..."
            
            # Blink if just connected? For now just static display
            c_text = f"GAMEPAD: {joy_name}"
            # Draw top right
            c_w, c_h = self.game.renderer.font.size(c_text)
            
            # panel
            pygame.draw.rect(surface, (20, 20, 20), (SCREEN_WIDTH - c_w - 40, 10, c_w + 30, 40))
            pygame.draw.rect(surface, theme["secondary"], (SCREEN_WIDTH - c_w - 40, 10, c_w + 30, 40), 1)
            self.game.renderer.draw_text(surface, c_text, SCREEN_WIDTH - c_w - 25, 20, theme["secondary"])

        # 3. Interactive Menu Box - responsive to screen height
        # Calculate available space for menu
        menu_top_margin = 310
        menu_bottom_margin = 50
        available_h = sh - menu_top_margin - menu_bottom_margin
        
        # Calculate button height to fit all items
        num_items = len(self.menu_items)
        header_h = 35
        btn_spacing = min(38, (available_h - header_h) // num_items)  # Cap at 38, shrink if needed
        
        menu_w = 380
        menu_h = num_items * btn_spacing + header_h + 25
        menu_x = (sw - menu_w) // 2
        menu_start_y = menu_top_margin
        
        # Use new styled panel
        self.game.renderer.draw_panel(surface, menu_x, menu_start_y, menu_w, menu_h, "MENU")
        
        current_y = menu_start_y + 45 # Increased padding from 40
        for i, item in enumerate(self.menu_items):
             is_selected = (i == self.selected_index)
             
             # Special handling for "NEW" badge on update
             display_text = get_text(self.game, item)
             if item == "SYSTEM UPDATE" and self.game.updater.update_available:
                 display_text += " [NEW!]"
             
             # Draw using new button style with reduced height
             h = self.game.renderer.draw_button(surface, display_text, menu_x + 15, current_y, is_selected, width=menu_w - 30, height=btn_spacing - 4)
             current_y += btn_spacing
            
        # 4. User Info / Auth UI (Simple bottom text - no panel)
        name = self.game.settings.get('name')
        account_type = self.game.settings.get('account_type')
        
        if account_type == "GUEST":
            self.game.renderer.draw_text(surface, f"GUEST  |  [L] Login  [R] Register  |  {VERSION}", 20, sh - 50, theme["secondary"])
        else:
            self.game.renderer.draw_text(surface, f"◉ {name}  |  [P] Profile  [L] Logout  |  {VERSION}", 20, sh - 50, theme["primary"])
        
        if hasattr(self.game, 'current_bgm_title') and self.game.current_bgm_title:
             r_text = f"NOW PLAYING: {self.game.current_bgm_title}"
             lines = self.game.renderer.wrap_text(r_text, 35)
             
             start_y = 60
             for i, line in enumerate(lines):
                 lw, lh = self.game.renderer.font.size(line)
                 self.game.renderer.draw_text(surface, line, sw - lw - 20, start_y + i * 20, theme["secondary"], self.game.renderer.font)
             
             # Control hints
             ctrl_msg = "[S] SHUFFLE  [TAB] NEXT"
             cw, ch = self.game.renderer.font.size(ctrl_msg)
             self.game.renderer.draw_text(surface, ctrl_msg, sw - cw - 20, start_y + (len(lines)) * 20 + 5, (100, 100, 100), self.game.renderer.font)

        # 5. Exit Confirmation Overlay
        if self.show_exit_confirm:
            overlay = pygame.Surface((sw, sh))
            overlay.set_alpha(200)
            overlay.fill((0,0,0))
            surface.blit(overlay, (0,0))
            w, h = 500, 200
            x, y = (sw - w)//2, (sh - h)//2
            pygame.draw.rect(surface, theme["bg"], (x, y, w, h))
            pygame.draw.rect(surface, theme["error"], (x, y, w, h), 2)
            title = "TERMINATE SYSTEM?"
            sub = "[Y] Confirm  [N] Cancel"
            font = self.game.renderer.big_font
            tw, th = font.size(title)
            self.game.renderer.draw_text(surface, title, x + (w-tw)//2, y + 50, theme["error"], font)
            font_small = self.game.renderer.font
            sub_w, sub_h = font_small.size(sub)
            self.game.renderer.draw_text(surface, sub, x + (w-sub_w)//2, y + 120, theme["text"], font_small)

        # 6. Donate Confirmation
        if self.show_donate_confirm:
            overlay = pygame.Surface((sw, sh))
            overlay.fill((0,0,0))
            overlay.set_alpha(200)
            surface.blit(overlay, (0,0))
            w, h = min(650, sw - 50), 280
            x, y = (sw - w)//2, (sh - h)//2
            pygame.draw.rect(surface, theme["bg"], (x, y, w, h))
            pygame.draw.rect(surface, (255, 200, 0), (x, y, w, h), 2)
            title = "EXTERNAL LINK"
            url = "ko-fi.com/wyind"
            confirm = "[Y] Open  [N] Cancel"
            r = self.game.renderer
            
            def draw_centered(text, y_offset, color, font=r.font):
                tw, th = font.size(text)
                r.draw_text(surface, text, x + (w - tw)//2, y + y_offset, color, font)

            draw_centered(title, 30, (255, 200, 0), r.big_font)
            draw_centered("Open browser to:", 90, theme["text"])
            draw_centered(url, 125, (0, 255, 255), r.font)
            draw_centered(confirm, 200, theme["secondary"])

        # 7. Show converting status (FINAL LAYER - TOP PRIORITY)
        if self.converting:
            r = self.game.renderer
            overlay = pygame.Surface((sw, sh))
            overlay.set_alpha(200)
            overlay.fill((5, 5, 10))
            surface.blit(overlay, (0,0))
            
            box_w, box_h = min(600, sw - 40), 120
            bx, by = (sw - box_w)//2, (sh - box_h)//2 + 50
            
            pygame.draw.rect(surface, theme["bg"], (bx, by, box_w, box_h))
            pygame.draw.rect(surface, theme["primary"], (bx, by, box_w, box_h), 2)
            
            r.draw_text(surface, "INITIALIZING...", bx + 20, by + 15, theme["primary"])
            status_text = f"{self.convert_status}"
            if len(status_text) > 45: status_text = status_text[:42] + "..."
            r.draw_text(surface, status_text, bx + 20, by + 45, (255, 255, 255))
            
            bar_w = int((box_w - 40) * (self.convert_pct / 100))
            pygame.draw.rect(surface, (40, 40, 40), (bx + 20, by + 85, box_w - 40, 15))
            if bar_w > 0:
                pygame.draw.rect(surface, theme["secondary"], (bx + 20, by + 85, bar_w, 15))

    def handle_input(self, event):
        if self.converting: return # BLOCK ALL INPUT
        
        if self.show_exit_confirm:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_y or event.key == pygame.K_RETURN:
                    self.play_sfx("shutdown")
                    self.game.trigger_reboot() # Initiates fade out exit
                elif event.key == pygame.K_n or event.key == pygame.K_ESCAPE:
                    self.play_sfx("back")
                    self.show_exit_confirm = False
            return
            
        if self.show_donate_confirm:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_y or event.key == pygame.K_RETURN:
                    self.play_sfx("accept")
                    try:
                        url = "https://ko-fi.com/wyind"
                        print(f"Opening URL: {url}")
                        webbrowser.open(url)
                    except Exception as e:
                        print(f"Failed to open URL: {e}")
                    self.show_donate_confirm = False
                elif event.key == pygame.K_n or event.key == pygame.K_ESCAPE:
                    self.play_sfx("back")
                    self.show_donate_confirm = False
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_index = (self.selected_index - 1) % len(self.menu_items)
                self.play_sfx("blip")
            elif event.key == pygame.K_DOWN:
                self.selected_index = (self.selected_index + 1) % len(self.menu_items)
                self.play_sfx("blip")
            elif event.key == pygame.K_RETURN:
                self.play_sfx("accept")
                choice = self.menu_items[self.selected_index]
                if choice == "PLAY":
                    # Redirect to mode select
                    self.game.scene_manager.switch_to(PlayModeSelectScene)
                elif choice == "STORY CAMPAIGN":
                    from scenes.story_scene import StoryScene
                    self.game.scene_manager.switch_to(StoryScene)
                elif choice == "REPLAYS":
                    # ReplaySelectScene is defined in this file
                    self.game.scene_manager.switch_to(ReplaySelectScene)
                elif choice == "MULTIPLAYER":
                    # Require login for multiplayer
                    if self.game.settings.get("account_type") != "REGISTERED":
                        # Show login required message and redirect
                        self.play_sfx("error")
                        from scenes.auth_scene import AuthScene
                        self.game.scene_manager.switch_to(AuthScene)
                    else:
                        from scenes.lobby_scene import LobbyScene
                        self.game.scene_manager.switch_to(LobbyScene)
                elif choice == "HOW TO PLAY":
                    self.game.scene_manager.switch_to(HowToPlayScene)
                elif choice == "OPTIONS": 
                    self.game.scene_manager.switch_to(SettingsScene)
                elif choice == "CREDITS":
                    self.game.scene_manager.switch_to(CreditsScene)
                elif choice == "SYSTEM UPDATE":
                    from scenes.update_scene import UpdateScene
                    self.game.scene_manager.switch_to(UpdateScene)
                elif choice == "CONTROLLER CONFIG":
                    self.game.scene_manager.switch_to(ControllerConfigScene)
                elif choice == "SUPPORT":
                    self.show_donate_confirm = True
                elif choice == "EXIT":
                    self.show_exit_confirm = True
            
            # Auth Shortcuts
            elif event.key == pygame.K_l:
                # Login / Logout
                if self.game.settings.get("account_type") == "REGISTERED":
                    # Logout
                    self.play_sfx("shutdown")
                    self.game.settings.set("account_type", "GUEST")
                    self.game.settings.set("name", "ANON")
                else:
                    # Login
                    from scenes.auth_scene import AuthScene
                    self.game.scene_manager.switch_to(AuthScene)
            
            elif event.key == pygame.K_r:
                # Open register website
                self.play_sfx("accept")
                try:
                    webbrowser.open("https://wyind.dev/#account")
                except:
                    pass
            
            elif event.key == pygame.K_p:
                 # Profile Shortcut
                 from scenes.profile_scene import ProfileScene
                 self.game.scene_manager.switch_to(ProfileScene)
            
            # Music Hotkeys
            elif event.key == pygame.K_s:
                self.play_sfx("accept")
                self.game.shuffle_menu_playlist()
            elif event.key == pygame.K_TAB:
                self.play_sfx("blip")
                self.game.next_menu_track()




class PlayModeSelectScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.menu_items = ["FREEPLAY", "STORY CAMPAIGN", "BACK"]
        self.selected_index = 0

    def on_enter(self, params=None):
        self.game.discord.update("Choosing Mode", "In Menu")
        self.play_sfx("type")

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_index = (self.selected_index - 1) % len(self.menu_items)
                self.play_sfx("blip")
            elif event.key == pygame.K_DOWN:
                self.selected_index = (self.selected_index + 1) % len(self.menu_items)
                self.play_sfx("blip")
            elif event.key == pygame.K_ESCAPE:
                self.play_sfx("back")
                # Return to title
                self.game.scene_manager.switch_to(TitleScene)
            elif event.key == pygame.K_RETURN:
                self.play_sfx("accept")
                choice = self.menu_items[self.selected_index]
                if choice == "FREEPLAY":
                    self.game.scene_manager.switch_to(SongSelectScene, {'mode': 'single'})
                elif choice == "STORY CAMPAIGN":
                    from scenes.story_scene import StoryScene
                    self.game.scene_manager.switch_to(StoryScene)
                elif choice == "BACK":
                     self.game.scene_manager.switch_to(TitleScene)

    def draw(self, surface):
        r = self.game.renderer
        theme = r.get_theme()
        
        # Draw BG
        surface.fill(theme["bg"])
        
        # Draw Background Grid (reuse logic or simplify)
        self._draw_grid(surface, theme)
        
        # Center Panel
        sw, sh = surface.get_width(), surface.get_height()
        panel_w, panel_h = 400, 320
        px = (sw - panel_w) // 2
        py = (sh - panel_h) // 2
        
        r.draw_panel(surface, px, py, panel_w, panel_h, "SELECT_MODE")
        
        r.draw_text(surface, "Choose your path:", px + 20, py + 50, theme["secondary"])
        
        y = py + 100
        for i, item in enumerate(self.menu_items):
            selected = (i == self.selected_index)
            r.draw_button(surface, item, px + 40, y, selected, width=panel_w - 80)
            y += 60
            
        r.draw_text(surface, "[ENTER] Select  [ESC] Back", 50, sh - 50, (100, 100, 100))

    def _draw_grid(self, surface, theme):
        t = pygame.time.get_ticks()
        sw, sh = surface.get_width(), surface.get_height()
        grid_offset_y = (t * 0.1) % 40
        grid_col = theme["grid"]
        for y in range(0, sh + 40, 40):
            line_y = y + grid_offset_y - 40
            pygame.draw.line(surface, grid_col, (0, line_y), (sw, line_y))
        for x in range(0, sw, 40):
            pygame.draw.line(surface, grid_col, (x, 0), (x, sh))
class SongSelectScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.songs = []
        self.selected_index = 0
        self.difficulties = DIFFICULTIES
        self.diff_index = 1
        self.autoplay_enabled = False
        self.load_songs()

    def on_enter(self, params=None):
        self.game.discord.update("Selecting Song", "In Menu")
        self.load_songs()
        self.mode = params.get('mode', 'single') if params else 'single'
        self.waiting_for_peer = False

    def update(self):
        if getattr(self, 'waiting_for_peer', False):
             if self.game.network.peer_has_song:
                 self._start_multiplayer_match()
                 
    def _start_multiplayer_match(self):
         self.waiting_for_peer = False
         song = self.songs[self.selected_index]
         diff = self.difficulties[self.diff_index]
         self.game.network.start_game_request()
         from scenes.game_scene import GameScene
         self.game.scene_manager.switch_to(GameScene, {
             'song': song,
             'difficulty': diff,
             'mode': 'multiplayer'
         })

    def load_songs(self):
        s_dir = "songs"
        if not os.path.exists(s_dir): os.makedirs(s_dir)
        
        # Use cache if available (from boot)
        if hasattr(self.game, 'song_cache') and self.game.song_cache:
            # Sort by title
            self.game.song_cache.sort(key=lambda x: x.get('title', '').lower())
            self.songs = [s['tur_file'] for s in self.game.song_cache]
        else:
            # Fallback to scanning dir
            self.songs = [f for f in os.listdir(s_dir) if f.lower().endswith('.tur')]
            self.songs.sort()
            
            # If no .tur files, look for audio (compatibility)
            if not self.songs:
                self.songs = [f for f in os.listdir(s_dir) if f.lower().endswith(('.mp3', '.wav', '.ogg'))]
                self.songs.sort()

    def draw(self, surface):
        r = self.game.renderer
        theme = r.get_theme()
        surface.fill(theme["bg"])
        
        # Header
        is_multi = getattr(self, 'mode', '') == 'multiplayer'
        title = "◉ MULTIPLAYER SELECT ◉" if is_multi else "◉ SELECT SONG ◉"
        r.draw_text(surface, title, 50, 30, theme["primary"], r.big_font)
        
        # Song count badge
        r.draw_text(surface, f"{len(self.songs)} songs", 900, 35, (80, 80, 80))
        
        # Song list panel - wider for song names
        # Use new styled panel with calculated height based on items
        panel_x = 40
        panel_y = 130
        panel_w = 550
        panel_h = 450
        
        r.draw_panel(surface, panel_x, panel_y, panel_w, panel_h, "AVAILABLE_SONGS")
        
        if not self.songs:
            r.draw_centered_text(surface, "No songs found!", panel_x + panel_w//2, panel_y + 100, theme["error"])
            r.draw_centered_text(surface, "Add .mp3/.wav/.ogg/.osz or .tur", panel_x + panel_w//2, panel_y + 130, (120, 120, 120))
            r.draw_centered_text(surface, "files to 'songs' folder", panel_x + panel_w//2, panel_y + 155, (120, 120, 120))
        else:
            visible_count = 8 # Reduced to fit panel (450h - 40header) / 44 = ~9.xx -> safe 8 or 9
            start_idx = max(0, self.selected_index - 4)
            # Ensure we don't restart too loosely
            if start_idx + visible_count > len(self.songs):
                 start_idx = max(0, len(self.songs) - visible_count)
            
            end_idx = min(len(self.songs), start_idx + visible_count)
            
            list_y = panel_y + 43 # Adjusted up 2px to prevent clipping
            
            for i in range(start_idx, end_idx):
                song = self.songs[i]
                
                # Get song name without extension
                name = os.path.splitext(song)[0]
                is_selected = (i == self.selected_index)
                
                suffix = ""
                if is_selected:
                    score_data = self.game.score_manager.get_score(song, self.difficulties[self.diff_index])
                    suffix = f" [{score_data['rank']}]" if score_data else ""
                
                # Truncate
                max_len = 38 # Reduced to prevent horizontal clipping
                display = name[:max_len] + "..." if len(name) > max_len else name
                display += suffix
                
                # Use Draw Button for song items too!
                # Adjust button Y slightly to center text vertically better
                r.draw_button(surface, display, panel_x + 20, list_y, is_selected, width=panel_w - 40)
                list_y += 44 # Button height + spacing
            
            # Scroll indicators
            if start_idx > 0:
                r.draw_text(surface, "↑", panel_x + panel_w - 30, panel_y + 10, theme["primary"])
            if end_idx < len(self.songs):
                r.draw_text(surface, "↓", panel_x + panel_w - 30, panel_y + panel_h - 25, theme["primary"])
        
        # Difficulty panel
        r.draw_panel(surface, 620, 130, 340, 140, "DIFFICULTY")
        
        # Difficulty
        diff = self.difficulties[self.diff_index]
        diff_color = theme["error"] if diff in ["HARD", "EXTREME", "FUCK YOU"] else theme["secondary"]
        
        # Center difficulty
        diff_text = f"< {diff} >"
        diff_w = r.big_font.size(diff_text)[0]
        r.draw_text(surface, diff_text, 620 + (340 - diff_w) // 2, 175, diff_color, r.big_font)
        r.draw_text(surface, "[←/→] to change", 720, 235, (80, 80, 80))
        
        # Controls panel
        # Increased height to 240 to prevent bottom text clipping
        r.draw_panel(surface, 620, 280, 340, 240, "CONTROLS")
        controls = [
            ("[↑/↓]", "Select Song"),
            ("[ENTER]", "Play"),
            ("[E]", "Beatmap Editor"),
            ("[S]", "Shuffle List"),
            ("[R]", "Random Song"),
            ("[F5]", "Reload List"),
            ("[F6]", "Regenerate Maps")
        ]
        y = 325 # Increased from 310 to clear title bar (280 + 32 + padding)
        for key, action in controls:
            r.draw_text(surface, key, 640, y, theme["secondary"], font=r.small_font)
            r.draw_text(surface, action, 720, y, theme["text"], font=r.small_font)
            y += 24
        
        # Download panel
        r.draw_panel(surface, 620, 560, 340, 80, "DOWNLOAD")
        r.draw_text(surface, "[D] Download Songs", 640, 600, theme["text"])
        
        # Autoplay toggle visualization in Controls or just below difficulty
        ap_col = theme["primary"] if self.autoplay_enabled else (100, 100, 100)
        ap_txt = "AUTOPLAY: ON" if self.autoplay_enabled else "AUTOPLAY: OFF"
        r.draw_text(surface, f"[A] {ap_txt}", 620, 535, ap_col, r.small_font)
        
        # Bottom bar
        pygame.draw.rect(surface, (15, 20, 25), (0, 700, 1024, 68))
        pygame.draw.line(surface, theme["grid"], (0, 700), (1024, 700), 2)
        r.draw_text(surface, "↑↓ Navigate", 80, 720, (100, 100, 100))
        r.draw_text(surface, "←→ Difficulty", 250, 720, (100, 100, 100))
        r.draw_text(surface, "ENTER Play", 430, 720, (100, 100, 100))
        r_col = theme["secondary"] if len(self.songs) > 0 else (100, 100, 100)
        r.draw_text(surface, "S Shuffle", 600, 720, r_col)
        r.draw_text(surface, "R Random", 730, 720, r_col)
        r.draw_text(surface, "ESC Back", 860, 720, (100, 100, 100))
        
        if getattr(self, 'waiting_for_peer', False):
             # Draw Waiting Overlay
             dim = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
             dim.fill((0, 0, 0, 180))
             surface.blit(dim, (0, 0))
             
             r.draw_panel(surface, 300, 300, 424, 150, "SYNCING")
             r.draw_text(surface, "Waiting for peer to download...", 330, 350, theme["primary"])
             
             # Show progress from NetworkManager
             status = self.game.network.status_message
             if status: r.draw_text(surface, status, 330, 390, theme["secondary"])

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.play_sfx("back")
                self.game.scene_manager.switch_to(TitleScene)
            elif event.key == pygame.K_F5:
                self.play_sfx("hdd")
                from core.song_converter import auto_convert_songs
                auto_convert_songs("songs", "MEDIUM", force_regen=False)
                
                # Clear cache
                if hasattr(self.game, 'song_cache'):
                    self.game.song_cache = []
                self.load_songs()
                
            elif event.key == pygame.K_F6:
                self.play_sfx("hdd")
                
                # Dynamic Loading Overlay
                r = self.game.renderer
                theme = r.get_theme()
                screen = pygame.display.get_surface()
                
                # Snapshot background for clean redraws (optional, or just clear panel area)
                # Drawing over the same panel works if we clear the panel rect first.
                
                dim = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
                dim.fill((0, 0, 0, 200))
                screen.blit(dim, (0, 0))
                pygame.display.flip()
                
                panel_w = 600
                panel_h = 200
                sw, sh = screen.get_size()
                panel_x = (sw - panel_w) // 2
                panel_y = (sh - panel_h) // 2
                
                def regen_callback(text, progress):
                    # 1. Clear Panel Area inside dim (redrawing panel bg)
                    r.draw_panel(screen, panel_x, panel_y, panel_w, panel_h, "REGENERATING")
                    
                    # 2. Text Handling (Truncate)
                    max_chars = 45
                    display_text = text
                    if len(display_text) > max_chars:
                        display_text = display_text[:max_chars-3] + "..."
                    
                    # Draw Text Centered
                    font = r.fonts["default"]
                    text_w = font.size(display_text)[0]
                    t_x = panel_x + (panel_w - text_w) // 2
                    r.draw_text(screen, display_text, t_x, panel_y + 60, theme["text"])
                    
                    # 3. Progress Bar (Confined)
                    bar_x = panel_x + 30
                    bar_y = panel_y + 110
                    bar_w = panel_w - 60
                    bar_h = 40
                    
                    # Border
                    pygame.draw.rect(screen, theme["grid"], (bar_x, bar_y, bar_w, bar_h), 2)
                    
                    # Fill
                    fill_w = int((bar_w - 6) * (progress / 100))
                    if fill_w > 0:
                        pygame.draw.rect(screen, theme["primary"], (bar_x + 3, bar_y + 3, fill_w, bar_h - 6))
                        
                    # Percentage
                    r.draw_text(screen, f"{int(progress)}%", bar_x + bar_w // 2 - 20, bar_y + 8, theme["bg"])
                    
                    pygame.display.flip()
                    pygame.event.pump()
                
                # Run Logic
                from core.song_converter import auto_convert_songs
                auto_convert_songs("songs", "MEDIUM", force_regen=True, callback=regen_callback)
                
                if hasattr(self.game, 'song_cache'):
                    self.game.song_cache = []
                self.load_songs()
                
            elif event.key == pygame.K_UP:
                self.selected_index = (self.selected_index - 1) % max(1, len(self.songs))
                self.play_sfx("blip")
            elif event.key == pygame.K_DOWN:
                self.selected_index = (self.selected_index + 1) % max(1, len(self.songs))
                self.play_sfx("blip")
            elif event.key == pygame.K_LEFT:
                self.diff_index = (self.diff_index - 1) % len(self.difficulties)
                self.play_sfx("blip")
            elif event.key == pygame.K_RIGHT:
                self.diff_index = (self.diff_index + 1) % len(self.difficulties)
                self.play_sfx("blip")
            elif event.key == pygame.K_RETURN:
                if self.songs:
                    self.play_sfx("accept")
                    # check if multiplayer (strict mode check)
                    is_multi = getattr(self, 'mode', 'single') == 'multiplayer'
                    if self.game.network.connected and is_multi:
                        # Send Proposal
                        song = self.songs[self.selected_index]
                        diff = self.difficulties[self.diff_index]
                        self.game.network.propose_song(song, diff)
                        
                        if self.game.network.is_host:
                            # Check if peer is connected (and not just "Waiting...")
                            has_peer = self.game.network.opponent_name != "Waiting..."
                            
                            if has_peer:
                                self.waiting_for_peer = True
                                self.game.network.peer_has_song = False
                            else:
                                self._start_multiplayer_match()
                    else:
                        from scenes.game_scene import GameScene
                        self.game.scene_manager.switch_to(GameScene, {
                            'song': self.songs[self.selected_index],
                            'difficulty': self.difficulties[self.diff_index],
                            'autoplay': self.autoplay_enabled
                        })
                else: 
                     self.play_sfx("back") # Error/Empty
            elif event.key == pygame.K_e:
                # EDITOR
                if self.songs:
                    self.play_sfx("accept")
                    from scenes.editor_scene import EditorScene
                    self.game.scene_manager.switch_to(EditorScene, {
                        'song': self.songs[self.selected_index],
                        'difficulty': self.difficulties[self.diff_index]
                    })
            elif event.key == pygame.K_d:
                 self.play_sfx("accept")
                 from scenes.download_scene import DownloadScene
                 self.game.scene_manager.switch_to(DownloadScene)
            elif event.key == pygame.K_s:
                # SHUFFLE
                if self.songs:
                    import random
                    random.shuffle(self.songs)
                    self.play_sfx("accept")
                    # Also shuffle cache for consistency if it exists
                    if hasattr(self.game, 'song_cache') and self.game.song_cache:
                        random.shuffle(self.game.song_cache)
            elif event.key == pygame.K_a:
                # Toggle Autoplay
                self.autoplay_enabled = not self.autoplay_enabled
                if self.autoplay_enabled:
                     self.play_sfx("type")
                else:
                     self.play_sfx("back")
                     
            elif event.key == pygame.K_r:
                # RANDOM
                if self.songs:
                    import random
                    self.selected_index = random.randint(0, len(self.songs) - 1)
                    self.play_sfx("accept")

class SettingsScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.last_joy_count = -1
        self.menu_items = []
        self.resolutions = [[1024, 768], [1280, 720], [1366, 768], [1600, 900], [1920, 1080], [2560, 1440]]
        self.index = 0
        self.scroll_offset = 0
        self.visible_items = 9
        self.show_regen_confirm = False
        
        self.tabs = ["AUDIO", "VIDEO", "GAMEPLAY", "INPUT", "THEMES"]
        self.current_tab = 0
        
        # Keybind mode
        self.binding_mode = False
        self.binding_step = 0
        self.temp_binds = []
        
        # Hot-Reload State
        self.reloading = False
        self.reload_msg = ""
        self.regen_start_time = 0
        self.regen_current_item = 0
        self.regen_total_items = 0
        self.regen_cancel_requested = False
        
        # Theme sharing state
        self.share_code_display = ""
        self.share_code_input = ""
        self.showing_share_code = False
        self.entering_share_code = False
        self.theme_message = ""
        self.regen_current_item = 0
        self.regen_total_items = 0
        self.regen_cancel_requested = False
        
        # Vim command buffer
        self.cmd_buffer = ""
        
        # Initial Build
        self.update_menu_items()
        
    def on_enter(self, params=None):
        self.game.discord.update("Configuring stuff", "Settings")

    def update_menu_items(self):
        # dynamic rebuild
        joy_count = pygame.joystick.get_count()
        if joy_count == self.last_joy_count and hasattr(self, 'all_items'):
            return
            
        self.last_joy_count = joy_count
        
        self.all_items = {
            "AUDIO": ["VOLUME", "MUSIC_VOLUME", "SFX_VOLUME", "OFFSET", "HIT SOUNDS"],
            "VIDEO": ["RESOLUTION", "FULLSCREEN", "V-SYNC", "CRT FILTER", "THEME", "VISUAL FX", "POST EFFECTS", "SHOW FPS", "BG DIM"],
            "GAMEPLAY": ["SPEED", "UPSCROLL", "SCREEN SHAKE", "NOTE STYLE", "RE-GEN MAPS", "LANGUAGE", "VIM BINDINGS"],
            "INPUT": ["KEYBINDS", "DEADZONE"],
            "THEMES": [
                "-- PRIMARY --", "PRIMARY R", "PRIMARY G", "PRIMARY B",
                "-- SECONDARY --", "SECONDARY R", "SECONDARY G", "SECONDARY B", 
                "-- BACKGROUND --", "BG R", "BG G", "BG B",
                "-- TEXT --", "TEXT R", "TEXT G", "TEXT B",
                "-- NOTE COLORS --", "NOTE1 R", "NOTE1 G", "NOTE1 B",
                "NOTE2 R", "NOTE2 G", "NOTE2 B",
                "RESET COLORS", "EXPORT THEME", "SHARE CODE", "ENTER CODE"
            ]
        }
        
        if joy_count > 0:
            self.all_items["INPUT"].append("CONTROLLER CONFIG")
            
        # Add BACK to Gameplay or as a global? Let's add it to every list effectively via draw, 
        # or just put it in Gameplay for now. Actually, let's just make it a dedicated index or something.
        # Better: Add to last category or separate navigation.
        # Standard: Add to the bottom of the list.
        # "BACK" removed from list to avoid redundancy with ESC footer
        # for cat in self.all_items:
        #     self.all_items[cat].append("BACK")
            
        self.refresh_current_items()

    def refresh_current_items(self):
        cat = self.tabs[self.current_tab]
        self.menu_items = self.all_items[cat]
        # Reset index if out of bounds
        if self.index >= len(self.menu_items):
            self.index = 0
        
    def update(self):
        self.update_menu_items()
        
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
        r.draw_text(surface, "◉ SYSTEM CONFIGURATION ◉", 50, 30, theme["primary"], r.big_font)
        
        if self.binding_mode:
            r.draw_panel(surface, 200, 250, 600, 200, "KEYBIND_SETUP")
            cur_key = ["LANE 1", "LANE 2", "LANE 3", "LANE 4"][self.binding_step]
            r.draw_text(surface, f"PRESS KEY FOR: {cur_key}", 350, 320, theme["secondary"], r.big_font)
            r.draw_text(surface, "[ESC] Cancel", 420, 400, (100, 100, 100))
            return

        # 2. Draw Tabs (Category Navigation)
        tab_x = 70
        tab_y = 100
        for i, tab in enumerate(self.tabs):
            tab_text = get_text(self.game, tab)
            is_active = (i == self.current_tab)
            # Use BG color for text on active tab to contrast with Primary highlight
            col = theme["bg"] if is_active else (150, 150, 150)
            
            # Highlight Active Tab
            if is_active:
                tw, th = r.font.size(tab_text)
                # Adjusted padding for better vertical centering
                # Y moved up (y-7), Height increased (th+14)
                pygame.draw.rect(surface, (*theme["primary"], 50), (tab_x - 10, tab_y - 7, tw + 20, th + 14), 0)
                pygame.draw.rect(surface, theme["primary"], (tab_x - 10, tab_y - 7, tw + 20, th + 14), 1)
                
            r.draw_text(surface, tab_text, tab_x, tab_y, col)
            tab_x += r.font.size(tab_text)[0] + 40

        # Settings panel - (Title removed to avoid redundancy with tabs)
        r.draw_panel(surface, 50, 150, 550, 460, None)  # No title in header
        
        # Fetch Data
        s = self.game.settings
        vol = s.get("volume")
        speed = s.get("speed")
        upscroll = s.get("upscroll")
        offset = s.get("audio_offset")
        theme_name = s.get("theme")
        res = s.get("resolution")
        fs = s.get("fullscreen")
        hit_sounds = s.get("hit_sounds") or True
        visual_fx = s.get("visual_effects") or True
        note_style = s.get("note_shape") or "BAR"
        hit_sounds = s.get("hit_sounds")
        visual_fx = s.get("visual_effects")
        show_fps = s.get("show_fps")
        bg_dim = s.get("bg_dim")
        
        # FPS Mode: 0=OFF, 1=SIMPLE, 2=DETAILED
        show_fps = s.get("show_fps") or 0
        fps_str = "OFF"
        if show_fps == 1: fps_str = "SIMPLE"
        elif show_fps == 2: fps_str = "DETAILED"
        
        bg_dim = s.get("bg_dim") or 0.5
        binds = s.get("keybinds")
        bind_names = ", ".join([pygame.key.name(k).upper() for k in binds])

        # Format note colors for display
        col1 = s.get("note_col_1") or [50, 255, 50]
        col2 = s.get("note_col_2") or [255, 180, 50]
        
        # Get current custom theme colors (or defaults from current theme)
        custom_primary = s.get("custom_primary") or list(theme["primary"])
        custom_secondary = s.get("custom_secondary") or list(theme["secondary"])
        custom_bg = s.get("custom_bg") or list(theme["bg"])
        custom_text = s.get("custom_text") or list(theme["text"])

        items_map = {
            "VOLUME": f"< {int(s.get('volume')*100)}% >",
            "MUSIC_VOLUME": f"< {int(s.get('music_volume')*100)}% >",
            "SFX_VOLUME": f"< {int(s.get('sfx_volume')*100)}% >",
            "SPEED": f"< {speed} >",
            "UPSCROLL": f"< {'ON' if upscroll else 'OFF'} >",
            "OFFSET": f"< {offset}ms >",
            "THEME": f"< {theme_name} >",
            "RESOLUTION": f"< {res[0]}x{res[1]} >",
            "FULLSCREEN": f"< {'ON' if fs else 'OFF'} >",
            "V-SYNC": f"< {'ON' if s.get('vsync') else 'OFF'} >",
            "CRT FILTER": f"< {'ON' if s.get('crt_filter') else 'OFF'} >",
            "HIT SOUNDS": f"< {'ON' if hit_sounds else 'OFF'} >",
            "VISUAL FX": f"< {'ON' if visual_fx else 'OFF'} >",
            "POST EFFECTS": f"< {'ON' if s.get('post_effects') else 'OFF'} >",
            "SCREEN SHAKE": f"< {int(s.get('screen_shake')*100)}% >",
            "NOTE STYLE": f"< {note_style} >",
            "SHOW FPS": f"< {fps_str} >",
            "BG DIM": f"< {int(bg_dim*100)}% >",
            "KEYBINDS": f"[{bind_names}]",
            "DEADZONE": f"< {int(s.get('joy_deadzone')*100)}% >",
            "RE-GEN MAPS": f"[{get_text(self.game, 'ACTIVE') if s.get('auto_recreate_beatmaps') else get_text(self.game, 'PRESS ENTER')}]",
            "LANGUAGE": f"< {s.get('language')} >",
            "VIM BINDINGS": f"< {'ON' if s.get('vim_mode') else 'OFF'} >",
            "UPDATE SOURCE": f"< {self._get_update_source_display(s.get('update_source'))} >",
            "CONTROLLER CONFIG": ">",
            # Theme color sections (headers)
            "-- PRIMARY --": "",
            "-- SECONDARY --": "",
            "-- BACKGROUND --": "",
            "-- TEXT --": "",
            "-- NOTE COLORS --": "",
            # RGB sliders
            "PRIMARY R": f"< {custom_primary[0]} >",
            "PRIMARY G": f"< {custom_primary[1]} >",
            "PRIMARY B": f"< {custom_primary[2]} >",
            "SECONDARY R": f"< {custom_secondary[0]} >",
            "SECONDARY G": f"< {custom_secondary[1]} >",
            "SECONDARY B": f"< {custom_secondary[2]} >",
            "BG R": f"< {custom_bg[0]} >",
            "BG G": f"< {custom_bg[1]} >",
            "BG B": f"< {custom_bg[2]} >",
            "TEXT R": f"< {custom_text[0]} >",
            "TEXT G": f"< {custom_text[1]} >",
            "TEXT B": f"< {custom_text[2]} >",
            "NOTE1 R": f"< {col1[0]} >",
            "NOTE1 G": f"< {col1[1]} >",
            "NOTE1 B": f"< {col1[2]} >",
            "NOTE2 R": f"< {col2[0]} >",
            "NOTE2 G": f"< {col2[1]} >",
            "NOTE2 B": f"< {col2[2]} >",
            "RESET COLORS": "[RESET TO THEME]",
            "EXPORT THEME": "[SAVE TO FILE]",
            "SHARE CODE": "[GENERATE]",
            "ENTER CODE": "[INPUT CODE]",
            "BACK": ""
        }
        
        items = []
        for key in self.menu_items:
            items.append((key, items_map.get(key, "")))
        
        # Scroll handling
        if self.index < self.scroll_offset:
            self.scroll_offset = self.index
        elif self.index >= self.scroll_offset + self.visible_items:
            self.scroll_offset = self.index - self.visible_items + 1

        y = 165
        for i in range(self.scroll_offset, min(self.scroll_offset + self.visible_items, len(items))):
            item_data = items[i]
            label = item_data[0]
            value = item_data[1]
            
            selected = (i == self.index)
            color = theme["secondary"] if selected else theme["text"]
            
            if selected:
                # Match button style for selected row
                # Increased X from 55 to 65 for better padding against panel border (X=50)
                # Adjusted Y to y-6 to center text vertically in the 35px box
                row_rect = pygame.Rect(65, y - 6, 530, 35)
                # Pulse effect
                pulse_val = (pygame.time.get_ticks() % 1000) / 1000.0
                bg_c = theme["grid"]
                bg_c = (
                    min(255, bg_c[0] + int(20 * pulse_val)),
                    min(255, bg_c[1] + int(20 * pulse_val)),
                    min(255, bg_c[2] + int(20 * pulse_val))
                )
                
                pygame.draw.rect(surface, bg_c, row_rect)
                pygame.draw.rect(surface, theme["primary"], row_rect, 2)
            
            # Label
            display_label = get_text(self.game, label)
            prefix = "◉ " if selected else "  "
            r.draw_text(surface, f"{prefix}{display_label}", 80, y, color) # Increased X from 70
            
            if value:
                val_col = theme["secondary"] if selected else (120, 120, 150)
                
                # Truncate long values to prevent left-side overflow
                max_w = 260
                vw = r.font.size(value)[0]
                if vw > max_w:
                    while len(value) > 3 and r.font.size(value + "..")[0] > max_w:
                         value = value[:-1]
                    value += ".."
                    vw = r.font.size(value)[0]

                # Align at 350 for short text, right-align for longer text (up to label collision around 300)
                target_x = 580 - vw
                if target_x > 350: target_x = 350
                r.draw_text(surface, value, target_x, y, val_col)
            y += 44

        # Scroll indicators (positioned inside panel bounds)
        if self.scroll_offset > 0:
            r.draw_text(surface, "▲ MORE", 280, 153, (100, 100, 100))
        if self.scroll_offset + self.visible_items < len(items):
            r.draw_text(surface, "▼ MORE", 280, 585, (100, 100, 100))

        # Help panel (Right side, standardized position)
        # Moved X from 600 to 620 to add gap from main window (ends at 600)
        panel_x_right = 620
        r.draw_panel(surface, panel_x_right, 125, 380, 240, "CONTROLS") 
        
        # Content shifted +20 (620 -> 640)
        txt_x = panel_x_right + 20
        r.draw_text(surface, "[↑/↓] Navigate", txt_x, 165, theme["text"])
        r.draw_text(surface, "[Q/E] Switch Tabs", txt_x, 195, theme["secondary"])
        r.draw_text(surface, "[←/→] Adjust", txt_x, 230, theme["text"])
        r.draw_text(surface, "[SHIFT] Fast Adjust", txt_x, 260, theme["text"])
        r.draw_text(surface, "[ENTER] Select", txt_x, 290, theme["text"])
        r.draw_text(surface, "[ESC] Back", txt_x, 320, theme["text"])
        
        # Theme preview (Right side, standardized position)
        r.draw_panel(surface, panel_x_right, 380, 380, 180, "THEME_PREVIEW")
        # Shifted Y down by 20px to clear title bar
        # Shifted X to match new panel pos
        pygame.draw.rect(surface, theme["primary"], (txt_x, 425, 40, 25))
        r.draw_text(surface, "Primary", txt_x + 50, 428, theme["text"])
        pygame.draw.rect(surface, theme["secondary"], (txt_x, 460, 40, 25))
        r.draw_text(surface, "Secondary", txt_x + 50, 463, theme["text"])
        pygame.draw.rect(surface, theme["bg"], (txt_x, 495, 40, 25))
        pygame.draw.rect(surface, theme["grid"], (txt_x, 495, 40, 25), 1)
        r.draw_text(surface, "Background", txt_x + 50, 498, theme["text"])

        # Confirmation Overlay for RE-GEN MAPS
        if self.show_regen_confirm:
            # Dim background
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(200)
            overlay.fill((0,0,0))
            surface.blit(overlay, (0,0))
            
            # Popup Box
            w, h = 600, 250
            x, y = (SCREEN_WIDTH - w)//2, (SCREEN_HEIGHT - h)//2
            
            pygame.draw.rect(surface, theme["bg"], (x, y, w, h))
            pygame.draw.rect(surface, theme["error"], (x, y, w, h), 2)
            
            # Text
            title = get_text(self.game, "DANGER: RE-GENERATE")
            msg1 = get_text(self.game, "This will OVERWRITE existing maps")
            msg2 = get_text(self.game, "with new patterns. Are you sure?")
            confirm = get_text(self.game, "[Y] CONFIRM   [N] CANCEL")
            
            # Draw centered
            r.draw_text(surface, title, x + (w - r.big_font.size(title)[0])//2, y + 40, theme["error"], r.big_font)
            r.draw_text(surface, msg1, x + (w - r.font.size(msg1)[0])//2, y + 100, theme["text"])
            r.draw_text(surface, msg2, x + (w - r.font.size(msg2)[0])//2, y + 130, theme["text"])
            r.draw_text(surface, confirm, x + (w - r.font.size(confirm)[0])//2, y + 190, theme["secondary"])

        # Reloading Overlay (Standardized Centered Look - FINAL LAYER)
        if self.reloading:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(220)
            overlay.fill((5, 10, 15))
            surface.blit(overlay, (0,0))
            
            # Progress Box (Using styled panel)
            box_w, box_h = 700, 150
            bx, by = (SCREEN_WIDTH - box_w)//2, (SCREEN_HEIGHT - box_h)//2
            r.draw_panel(surface, bx, by, box_w, box_h, "SYSTEM BUSY", color=(20, 20, 30))
            
            # Header
            r.draw_text(surface, "RE-GENERATING ALL PATTERNS", bx + 20, by + 15, theme["primary"])
            
            # Status message (Truncate to fit box)
            msg = self.reload_msg or "SCANNING FILE SYSTEM..."
            max_chars = 55
            if len(msg) > max_chars:
                msg = msg[:max_chars - 3] + "..."
            r.draw_text(surface, f"STATUS: {msg}", bx + 20, by + 45, (200, 200, 200))
            
            # Progress bar with bounds checking
            pct = 0.0
            try:
                if self.reload_msg and '(' in self.reload_msg and '%' in self.reload_msg:
                    pct_str = self.reload_msg.split('(')[-1].split('%')[0]
                    if pct_str.isdigit():
                        pct = min(1.0, max(0.0, int(pct_str) / 100))
            except:
                pass
            
            # Calculate ETA
            eta_str = "--:--"
            if pct > 0.05 and self.regen_start_time > 0:
                import time
                elapsed = time.time() - self.regen_start_time
                if pct > 0:
                    total_est = elapsed / pct
                    remaining = total_est - elapsed
                    if remaining > 0 and remaining < 3600:
                        mins = int(remaining // 60)
                        secs = int(remaining % 60)
                        eta_str = f"{mins:02d}:{secs:02d}"
            
            # Progress info line
            pct_display = int(pct * 100)
            progress_text = f"{pct_display}% COMPLETE  |  ETA: {eta_str}"
            r.draw_text(surface, progress_text, bx + 20, by + 75, theme["secondary"])
            
            # Progress bar
            bar_max = box_w - 40
            bar_w = int(bar_max * pct) if pct > 0 else int(bar_max * ((pygame.time.get_ticks() // 10 % 100) / 100))
            pygame.draw.rect(surface, (40, 40, 40), (bx + 20, by + 110, bar_max, 18))
            if bar_w > 0:
                pygame.draw.rect(surface, theme["secondary"], (bx + 20, by + 110, bar_w, 18))
            
            # Cancel hint
            r.draw_text(surface, "[ESC] Cancel", bx + box_w - 130, by + 15, (100, 100, 100))

        # Share code display overlay
        if self.showing_share_code:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(200)
            overlay.fill((0, 0, 0))
            surface.blit(overlay, (0, 0))
            
            w, h = 600, 200
            x, y = (SCREEN_WIDTH - w) // 2, (SCREEN_HEIGHT - h) // 2
            pygame.draw.rect(surface, theme["bg"], (x, y, w, h))
            pygame.draw.rect(surface, theme["primary"], (x, y, w, h), 2)
            
            r.draw_text(surface, "YOUR SHARE CODE", x + 200, y + 20, theme["primary"], r.big_font)
            r.draw_text(surface, self.share_code_display, x + 50, y + 80, theme["secondary"], r.big_font)
            r.draw_text(surface, "[ENTER] Close   [CTRL+C] Copy", x + 150, y + 160, (100, 100, 100))

        # Share code input overlay
        if self.entering_share_code:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(200)
            overlay.fill((0, 0, 0))
            surface.blit(overlay, (0, 0))
            
            w, h = 600, 200
            x, y = (SCREEN_WIDTH - w) // 2, (SCREEN_HEIGHT - h) // 2
            pygame.draw.rect(surface, theme["bg"], (x, y, w, h))
            pygame.draw.rect(surface, theme["primary"], (x, y, w, h), 2)
            
            r.draw_text(surface, "ENTER SHARE CODE", x + 180, y + 20, theme["primary"], r.big_font)
            
            # Input box
            pygame.draw.rect(surface, (20, 20, 20), (x + 50, y + 70, 500, 40))
            pygame.draw.rect(surface, theme["secondary"], (x + 50, y + 70, 500, 40), 2)
            display_code = self.share_code_input + ("_" if pygame.time.get_ticks() % 1000 < 500 else "")
            r.draw_text(surface, display_code, x + 60, y + 78, theme["text"])
            
            r.draw_text(surface, "[ENTER] Apply   [ESC] Cancel", x + 170, y + 160, (100, 100, 100))

        # Theme message display (bottom of screen)
        if self.theme_message:
            msg_w = r.font.size(self.theme_message)[0] + 40
            msg_x = (SCREEN_WIDTH - msg_w) // 2
            pygame.draw.rect(surface, theme["bg"], (msg_x, 650, msg_w, 30))
            pygame.draw.rect(surface, theme["secondary"], (msg_x, 650, msg_w, 30), 1)
            r.draw_text(surface, self.theme_message, msg_x + 20, 655, theme["secondary"])

    def handle_input(self, event):
        if self.show_regen_confirm:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_y or event.key == pygame.K_RETURN:
                    self.play_sfx("accept")
                    self.game.settings.set("auto_recreate_beatmaps", True)
                    self.game.settings.save()
                    self.show_regen_confirm = False
                    
                    # Trigger Hot-Reload
                    self.reloading = True
                    self.reload_msg = "INITIALIZING..."
                    self.regen_cancel_requested = False
                    import time
                    self.regen_start_time = time.time()
                    import threading
                    
                    # Pass cancel check function to converter
                    def check_cancel():
                        return self.regen_cancel_requested
                    
                    def reload_thread():
                        try:
                            from core.song_converter import auto_convert_songs, preload_all_songs
                            def update_status(msg, pct=0):
                                self.reload_msg = f"{msg} ({pct}%)"
                            
                            auto_convert_songs("songs", callback=update_status, cancel_check=check_cancel)
                            
                            if not self.regen_cancel_requested:
                                songs = preload_all_songs("songs", callback=update_status)
                                self.game.song_cache = songs
                        except Exception as e:
                            print(f"Hot-Reload Error: {e}")
                        finally:
                            self.reloading = False
                            self.regen_cancel_requested = False
                    
                    threading.Thread(target=reload_thread, daemon=True).start()
                    
                elif event.key == pygame.K_n or event.key == pygame.K_ESCAPE:
                    self.play_sfx("back")
                    self.show_regen_confirm = False
            return

        # Share code display - ESC to close
        if self.showing_share_code:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN:
                    self.play_sfx("back")
                    self.showing_share_code = False
                elif event.key == pygame.K_c and (event.mod & pygame.KMOD_CTRL):
                    # Copy to clipboard (if pygame supports it)
                    try:
                        import pyperclip
                        pyperclip.copy(self.share_code_display)
                        self.theme_message = "Copied to clipboard!"
                    except:
                        self.theme_message = "Copy manually: " + self.share_code_display[:20]
            return

        # Share code input mode
        if self.entering_share_code:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.play_sfx("back")
                    self.entering_share_code = False
                elif event.key == pygame.K_RETURN:
                    if self.share_code_input:
                        from core.theme_manager import apply_share_code
                        success, msg = apply_share_code(self.game.settings, self.share_code_input)
                        self.theme_message = msg
                        if success:
                            self.play_sfx("accept")
                        else:
                            self.play_sfx("error")
                    self.entering_share_code = False
                elif event.key == pygame.K_BACKSPACE:
                    self.share_code_input = self.share_code_input[:-1]
                elif event.unicode.isalnum() or event.unicode in '-_':
                    if len(self.share_code_input) < 100:
                        self.share_code_input += event.unicode.upper()
            return

        if self.reloading:
            # Allow cancelling with ESC
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.regen_cancel_requested = True
                self.reload_msg = "Cancelling..."
            return

        if self.binding_mode:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.play_sfx("back")
                    self.binding_mode = False
                    return
                # Accept key
                self.play_sfx("accept")
                self.temp_binds.append(event.key)
                self.binding_step += 1
                if self.binding_step >= 4:
                    self.game.settings.set("keybinds", self.temp_binds)
                    self.binding_mode = False
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.index = (self.index - 1) % len(self.menu_items)
                self.play_sfx("blip")
            elif event.key == pygame.K_DOWN:
                self.index = (self.index + 1) % len(self.menu_items)
                self.play_sfx("blip")
            elif event.key == pygame.K_q or event.key == pygame.K_PAGEUP:
                self.current_tab = (self.current_tab - 1) % len(self.tabs)
                self.refresh_current_items()
                self.play_sfx("type")
            elif event.key == pygame.K_e or event.key == pygame.K_PAGEDOWN:
                self.current_tab = (self.current_tab + 1) % len(self.tabs)
                self.refresh_current_items()
                self.play_sfx("type")
            
            # Vim Bindings
            if self.game.settings.get("vim_mode"):
                if event.key == pygame.K_j:
                    self.index = (self.index + 1) % len(self.menu_items)
                    self.play_sfx("blip")
                elif event.key == pygame.K_k:
                    self.index = (self.index - 1) % len(self.menu_items)
                    self.play_sfx("blip")
                elif event.key == pygame.K_h:
                    if self.adjust(-1): self.play_sfx("blip")
                elif event.key == pygame.K_l:
                    if self.adjust(1): self.play_sfx("blip")
                
                # Command Buffer for :wq
                name = pygame.key.name(event.key)
                if event.mod & pygame.KMOD_SHIFT and event.key == pygame.K_SEMICOLON:
                    self.cmd_buffer = ":" 
                elif self.cmd_buffer.startswith(":"):
                    self.cmd_buffer += name
                    if self.cmd_buffer == ":wq":
                        self.play_sfx("accept")
                        self.game.scene_manager.switch_to(TitleScene)
                    elif len(self.cmd_buffer) > 3:
                        self.cmd_buffer = ""
            
            if event.key == pygame.K_LEFT:
                fast = hasattr(event, 'mod') and (event.mod & pygame.KMOD_SHIFT)
                if self.adjust(-1, fast):
                     self.play_sfx("blip")
            elif event.key == pygame.K_RIGHT:
                fast = hasattr(event, 'mod') and (event.mod & pygame.KMOD_SHIFT)
                if self.adjust(1, fast):
                     self.play_sfx("blip")
            elif event.key == pygame.K_RETURN:
                self.play_sfx("accept")
                sel = self.menu_items[self.index]
                if sel == "BACK":
                    self.game.scene_manager.switch_to(TitleScene)
                elif sel == "KEYBINDS":
                    self.binding_mode = True
                    self.binding_step = 0
                    self.temp_binds = []
                elif sel == "CONTROLLER CONFIG":
                    self.game.scene_manager.switch_to(ControllerConfigScene)
                elif sel == "RE-GEN MAPS":
                    if not self.game.settings.get("auto_recreate_beatmaps"):
                        self.show_regen_confirm = True
                    else:
                        self.play_sfx("back")
                        self.game.settings.set("auto_recreate_beatmaps", False)
                elif sel == "EXPORT THEME":
                    from core.theme_manager import export_theme_to_file
                    filepath = export_theme_to_file(self.game.settings, "custom_theme")
                    self.theme_message = f"Saved to {os.path.basename(filepath)}"
                elif sel == "SHARE CODE":
                    from core.theme_manager import generate_share_code
                    code = generate_share_code(self.game.settings)
                    self.share_code_display = code
                    self.showing_share_code = True
                elif sel == "ENTER CODE":
                    self.entering_share_code = True
                    self.share_code_input = ""
            elif event.key == pygame.K_ESCAPE:
                self.play_sfx("back")
                self.game.scene_manager.switch_to(TitleScene)
        
        # Controller Tab Switching
        if event.type == pygame.JOYBUTTONDOWN:
            if event.button == 4: # L1
                self.current_tab = (self.current_tab - 1) % len(self.tabs)
                self.refresh_current_items()
                self.play_sfx("type")
            elif event.button == 5: # R1
                self.current_tab = (self.current_tab + 1) % len(self.tabs)
                self.refresh_current_items()
                self.play_sfx("type")

    def adjust(self, direction, fast=False):
        item = self.menu_items[self.index]
        s = self.game.settings
        
        if item == "SPEED":
            cur = s.get("speed")
            cur += direction * (50 if not fast else 200)
            s.set("speed", max(100, min(2000, cur)))
        elif item == "VOLUME":
            cur = s.get("volume")
            cur += direction * 0.1
            cur = max(0.0, min(1.0, cur))
            s.set("volume", cur)
            pygame.mixer.music.set_volume(cur)
        elif item == "THEME":
            themes_list = list(THEMES.keys())
            cur = s.get("theme")
            try:
                idx = themes_list.index(cur)
            except:
                idx = 0
            new_idx = (idx + direction) % len(themes_list)
            new_theme = themes_list[new_idx]
            s.set("theme", new_theme)
            
            # Clear all custom color overrides so new theme takes effect
            t_data = THEMES[new_theme]
            s.set("custom_primary", None)
            s.set("custom_secondary", None)
            s.set("custom_bg", None)
            s.set("custom_text", None)
            s.set("note_col_1", list(t_data["primary"]))
            s.set("note_col_2", list(t_data["secondary"]))
            
        elif item == "OFFSET":
            cur = s.get("audio_offset")
            cur += direction * 5
            s.set("audio_offset", max(-200, min(200, cur)))
        elif item == "UPSCROLL":
            s.set("upscroll", not s.get("upscroll"))
        elif item == "RESOLUTION":
            cur_res = s.get("resolution")
            try:
                idx = self.resolutions.index(cur_res)
            except:
                idx = 0
            new_idx = (idx + direction) % len(self.resolutions)
            new_res = self.resolutions[new_idx]
            s.set("resolution", new_res)
            # Apply resolution
            if not s.get("fullscreen"):
                pygame.display.set_mode(new_res, pygame.RESIZABLE)
        elif item == "FULLSCREEN":
            fs = not s.get("fullscreen")
            s.set("fullscreen", fs)
            res = s.get("resolution")
            if fs:
                pygame.display.set_mode(res, pygame.FULLSCREEN)
            else:
                pygame.display.set_mode(res, pygame.RESIZABLE)
        elif item == "NOTE STYLE":
             styles = ["BAR", "ARROW", "CIRCLE"]
             cur = s.get("note_shape") or "BAR"
             try:
                 idx = styles.index(cur)
             except: idx = 0
             idx = (idx + direction) % len(styles)
             s.set("note_shape", styles[idx])
        elif item == "HIT SOUNDS":
            s.set("hit_sounds", not s.get("hit_sounds"))
        elif item == "VISUAL FX":
            s.set("visual_effects", not s.get("visual_effects"))
        elif item == "POST EFFECTS":
            s.set("post_effects", not s.get("post_effects"))
        elif item == "SHOW FPS":
            # 0=OFF, 1=SIMPLE, 2=DETAILED
            cur = s.get("show_fps") or 0
            if isinstance(cur, bool): cur = 1 if cur else 0 # Migration safety
            
            if direction > 0:
                cur = (cur + 1) % 3
            else:
                cur = (cur - 1) % 3
            s.set("show_fps", cur)
            
        elif item == "BG DIM":
            cur = s.get("bg_dim") or 0.5
            cur += direction * (0.05 if not fast else 0.2)
            s.set("bg_dim", max(0.0, min(1.0, cur)))
            
        elif item == "VIM BINDINGS":
            s.set("vim_mode", not s.get("vim_mode"))
        elif item == "MUSIC_VOLUME":
            cur = s.get("music_volume")
            cur += direction * 0.05
            cur = max(0.0, min(1.0, cur))
            s.set("music_volume", cur)
            # update mixer
            self.game.audio.update_volumes()
        elif item == "SFX_VOLUME":
            cur = s.get("sfx_volume")
            cur += direction * 0.05
            cur = max(0.0, min(1.0, cur))
            s.set("sfx_volume", cur)
            self.game.audio.update_volumes()
        elif item == "V-SYNC":
            s.set("vsync", not s.get("vsync"))
        elif item == "CRT FILTER":
            s.set("crt_filter", not s.get("crt_filter"))
        elif item == "SCREEN SHAKE":
            cur = s.get("screen_shake") or 1.0
            cur += direction * 0.1
            s.set("screen_shake", max(0.0, min(2.0, cur)))
        elif item == "DEADZONE":
            cur = s.get("joy_deadzone") or 0.2
            cur += direction * 0.05
            s.set("joy_deadzone", max(0.0, min(0.5, cur)))
        elif item == "LANGUAGE":
            langs = ["EN", "ES", "FR", "JP"]
            try:
                idx = langs.index(s.get("language"))
            except:
                idx = 0
            new_idx = (idx + direction) % len(langs)
            s.set("language", langs[new_idx])
        elif item == "BG DIM":
            cur = s.get("bg_dim")
            cur += direction * 0.1
            s.set("bg_dim", max(0.0, min(1.0, cur)))
        
        # RGB component handlers - adjust values by 5 (or 10 with shift)
        # Primary color RGB
        if item == "PRIMARY R":
            step = 10 if pygame.key.get_mods() & pygame.KMOD_SHIFT else 5
            cur = s.get("custom_primary") or list(self.game.renderer.get_theme()["primary"])
            cur[0] = max(0, min(255, cur[0] + direction * step))
            s.set("custom_primary", cur)
            self._apply_custom_theme()
        elif item == "PRIMARY G":
            step = 10 if pygame.key.get_mods() & pygame.KMOD_SHIFT else 5
            cur = s.get("custom_primary") or list(self.game.renderer.get_theme()["primary"])
            cur[1] = max(0, min(255, cur[1] + direction * step))
            s.set("custom_primary", cur)
            self._apply_custom_theme()
        elif item == "PRIMARY B":
            step = 10 if pygame.key.get_mods() & pygame.KMOD_SHIFT else 5
            cur = s.get("custom_primary") or list(self.game.renderer.get_theme()["primary"])
            cur[2] = max(0, min(255, cur[2] + direction * step))
            s.set("custom_primary", cur)
            self._apply_custom_theme()
        
        # Secondary color RGB
        elif item == "SECONDARY R":
            step = 10 if pygame.key.get_mods() & pygame.KMOD_SHIFT else 5
            cur = s.get("custom_secondary") or list(self.game.renderer.get_theme()["secondary"])
            cur[0] = max(0, min(255, cur[0] + direction * step))
            s.set("custom_secondary", cur)
            self._apply_custom_theme()
        elif item == "SECONDARY G":
            step = 10 if pygame.key.get_mods() & pygame.KMOD_SHIFT else 5
            cur = s.get("custom_secondary") or list(self.game.renderer.get_theme()["secondary"])
            cur[1] = max(0, min(255, cur[1] + direction * step))
            s.set("custom_secondary", cur)
            self._apply_custom_theme()
        elif item == "SECONDARY B":
            step = 10 if pygame.key.get_mods() & pygame.KMOD_SHIFT else 5
            cur = s.get("custom_secondary") or list(self.game.renderer.get_theme()["secondary"])
            cur[2] = max(0, min(255, cur[2] + direction * step))
            s.set("custom_secondary", cur)
            self._apply_custom_theme()
        elif item == "SECONDARY G":
            cur = s.get("custom_secondary") or list(self.game.renderer.get_theme()["secondary"])
            cur[1] = max(0, min(255, cur[1] + direction * step))
            s.set("custom_secondary", cur)
            self._apply_custom_theme()
        elif item == "SECONDARY B":
            cur = s.get("custom_secondary") or list(self.game.renderer.get_theme()["secondary"])
            cur[2] = max(0, min(255, cur[2] + direction * step))
            s.set("custom_secondary", cur)
            self._apply_custom_theme()
        
        # Background color RGB
        elif item == "BG R":
            step = 10 if pygame.key.get_mods() & pygame.KMOD_SHIFT else 5
            cur = s.get("custom_bg") or list(self.game.renderer.get_theme()["bg"])
            cur[0] = max(0, min(255, cur[0] + direction * step))
            s.set("custom_bg", cur)
            self._apply_custom_theme()
        elif item == "BG G":
            step = 10 if pygame.key.get_mods() & pygame.KMOD_SHIFT else 5
            cur = s.get("custom_bg") or list(self.game.renderer.get_theme()["bg"])
            cur[1] = max(0, min(255, cur[1] + direction * step))
            s.set("custom_bg", cur)
            self._apply_custom_theme()
        elif item == "BG B":
            step = 10 if pygame.key.get_mods() & pygame.KMOD_SHIFT else 5
            cur = s.get("custom_bg") or list(self.game.renderer.get_theme()["bg"])
            cur[2] = max(0, min(255, cur[2] + direction * step))
            s.set("custom_bg", cur)
            self._apply_custom_theme()
        
        # Text color RGB
        elif item == "TEXT R":
            step = 10 if pygame.key.get_mods() & pygame.KMOD_SHIFT else 5
            cur = s.get("custom_text") or list(self.game.renderer.get_theme()["text"])
            cur[0] = max(0, min(255, cur[0] + direction * step))
            s.set("custom_text", cur)
            self._apply_custom_theme()
        elif item == "TEXT G":
            step = 10 if pygame.key.get_mods() & pygame.KMOD_SHIFT else 5
            cur = s.get("custom_text") or list(self.game.renderer.get_theme()["text"])
            cur[1] = max(0, min(255, cur[1] + direction * step))
            s.set("custom_text", cur)
            self._apply_custom_theme()
        elif item == "TEXT B":
            step = 10 if pygame.key.get_mods() & pygame.KMOD_SHIFT else 5
            cur = s.get("custom_text") or list(self.game.renderer.get_theme()["text"])
            cur[2] = max(0, min(255, cur[2] + direction * step))
            s.set("custom_text", cur)
            self._apply_custom_theme()
        
        # Note color 1 RGB
        elif item == "NOTE1 R":
            step = 10 if pygame.key.get_mods() & pygame.KMOD_SHIFT else 5
            cur = s.get("note_col_1") or [50, 255, 50]
            cur[0] = max(0, min(255, cur[0] + direction * step))
            s.set("note_col_1", cur)
        elif item == "NOTE1 G":
            step = 10 if pygame.key.get_mods() & pygame.KMOD_SHIFT else 5
            cur = s.get("note_col_1") or [50, 255, 50]
            cur[1] = max(0, min(255, cur[1] + direction * step))
            s.set("note_col_1", cur)
        elif item == "NOTE1 B":
            step = 10 if pygame.key.get_mods() & pygame.KMOD_SHIFT else 5
            cur = s.get("note_col_1") or [50, 255, 50]
            cur[2] = max(0, min(255, cur[2] + direction * step))
            s.set("note_col_1", cur)
        
        # Note color 2 RGB
        elif item == "NOTE2 R":
            step = 10 if pygame.key.get_mods() & pygame.KMOD_SHIFT else 5
            cur = s.get("note_col_2") or [255, 180, 50]
            cur[0] = max(0, min(255, cur[0] + direction * step))
            s.set("note_col_2", cur)
        elif item == "NOTE2 G":
            step = 10 if pygame.key.get_mods() & pygame.KMOD_SHIFT else 5
            cur = s.get("note_col_2") or [255, 180, 50]
            cur[1] = max(0, min(255, cur[1] + direction * step))
            s.set("note_col_2", cur)
        elif item == "NOTE2 B":
            step = 10 if pygame.key.get_mods() & pygame.KMOD_SHIFT else 5
            cur = s.get("note_col_2") or [255, 180, 50]
            cur[2] = max(0, min(255, cur[2] + direction * step))
            s.set("note_col_2", cur)
        
        # Reset colors to current theme defaults
        elif item == "RESET COLORS":
            base_theme_name = s.get("theme")
            if base_theme_name and base_theme_name in THEMES:
                base = THEMES[base_theme_name]
                # Clear custom overrides so base theme shows through
                s.set("custom_primary", None)
                s.set("custom_secondary", None)
                s.set("custom_bg", None)
                s.set("custom_text", None)
                # Reset note colors to theme defaults
                s.set("note_col_1", list(base["primary"]))
                s.set("note_col_2", list(base["secondary"]))

        s.save()
        return True
    
    def _get_update_source_display(self, source):
        """Get display name for update source"""
        from core.updater import UPDATE_SOURCE_GITHUB, UPDATE_SOURCE_ITCHIO, UPDATE_SOURCE_DISABLED
        if source == UPDATE_SOURCE_ITCHIO:
            return "ITCH.IO"
        elif source == UPDATE_SOURCE_DISABLED:
            return "DISABLED"
        else:
            return "GITHUB"
    
    def _apply_custom_theme(self):
        """Apply custom colors to the active theme"""
        s = self.game.settings
        base_name = s.get("theme")
        
        # Get base theme or current
        if base_name and base_name in THEMES:
            base = dict(THEMES[base_name])
        else:
            base = dict(self.game.renderer.get_theme())
        
        # Override with custom values if set
        if s.get("custom_primary"):
            base["primary"] = tuple(s.get("custom_primary"))
        if s.get("custom_secondary"):
            base["secondary"] = tuple(s.get("custom_secondary"))
        if s.get("custom_bg"):
            base["bg"] = tuple(s.get("custom_bg"))
        if s.get("custom_text"):
            base["text"] = tuple(s.get("custom_text"))
        
        # Apply to renderer
        self.game.renderer.current_theme = base

class ControllerConfigScene(Scene):
    def on_enter(self, params):
        self.rebind_mode = False
        self.rebind_step = 0
        self.temp_joy_binds = [0, 0, 0, 0] # Temp storage
        
        # Load asset
        try:
            img_path = os.path.join("assets", "controller.png")
            if os.path.exists(img_path):
                self.controller_img = pygame.image.load(img_path)
            else:
                self.controller_img = None
        except:
            self.controller_img = None

    def draw(self, surface):
        theme = self.game.renderer.get_theme()
        surface.fill(theme["bg"])
        self.game.renderer.draw_text(surface, "CONTROLLER PROTOCOL", 100, 50, theme["primary"], self.game.renderer.big_font)
        
        if self.controller_img:
            rect = self.controller_img.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50))
            # Darker if rebinding
            if self.rebind_mode:
                self.controller_img.set_alpha(100)
            else:
                self.controller_img.set_alpha(255)
            surface.blit(self.controller_img, rect)
        
        if self.rebind_mode:
            self.game.renderer.draw_text(surface, f"REBINDING LANE {self.rebind_step}...", SCREEN_WIDTH//2 - 150, 400, (255, 255, 0), self.game.renderer.big_font)
            self.game.renderer.draw_text(surface, "PRESS A CONTROLLER BUTTON OR AXIS (TRIGGER)", SCREEN_WIDTH//2 - 200, 460, (255, 255, 255))
        else:
            self.game.renderer.draw_text(surface, "PRESS [ENTER] TO REBIND ALL LANES", SCREEN_WIDTH//2 - 180, 500, (200, 200, 200))
            
            # Show Binds
            binds = self.game.settings.get("joy_binds")
            for i, b in enumerate(binds):
                txt = "UNBOUND"
                if isinstance(b, int): txt = f"BTN {b}" # Legacy
                elif isinstance(b, dict):
                    if b['type'] == 'btn': txt = f"BTN {b['value']}"
                    elif b['type'] == 'axis': 
                        d = "+" if b['dir'] > 0 else "-"
                        txt = f"AXIS {b['axis']} {d}"
                
                self.game.renderer.draw_text(surface, f"LANE {i}: {txt}", 400, 550 + i * 30, theme["primary"])

        self.game.renderer.draw_text(surface, "[ESC] BACK", 100, 700, theme["secondary"])

    def handle_input(self, event):
        if self.rebind_mode:
            bind = None
            if event.type == pygame.JOYBUTTONDOWN:
                bind = {'type': 'btn', 'value': event.button}
            elif event.type == pygame.JOYAXISMOTION:
                if abs(event.value) > 0.7: # Higher threshold for distinct input
                    direction = 1 if event.value > 0 else -1
                    bind = {'type': 'axis', 'axis': event.axis, 'dir': direction}
            
            if bind:
                self.play_sfx("accept")
                self.temp_joy_binds[self.rebind_step] = bind
                self.rebind_step += 1
                pygame.time.wait(200) # Debounce
                pygame.event.clear() # Clear queue to prevent skip
                
                if self.rebind_step >= 4:
                    self.game.settings.set("joy_binds", self.temp_joy_binds)
                    self.rebind_mode = False
            
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.rebind_mode = False
            return


        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.play_sfx("back")
                self.game.scene_manager.switch_to(TitleScene)
            elif event.key == pygame.K_RETURN:
                self.rebind_mode = True
                self.rebind_step = 0
                self.play_sfx("accept")

    def update(self):
        # Auto-exit if controller disconnected
        if pygame.joystick.get_count() == 0:
            self.game.scene_manager.switch_to(TitleScene)



class ReplaySelectScene(Scene):
    def on_enter(self, params=None):
        self.replays = []
        self.selected_index = 0
        self.scroll_offset = 0
        self.visible_items = 10
        self.load_replays()
        
    def load_replays(self):
        replay_dir = "replays"
        if not os.path.exists(replay_dir):
            os.makedirs(replay_dir)
            
        import json
        files = [f for f in os.listdir(replay_dir) if f.endswith('.turr')]
        files.sort(key=lambda x: os.path.getmtime(os.path.join(replay_dir, x)), reverse=True)
        
        self.replays = []
        for f in files:
            try:
                path = os.path.join(replay_dir, f)
                with open(path, 'r') as file:
                    data = json.load(file)
                    # Check if song exists (basic check)
                    is_corrupted = False
                    song_name = data.get('song', 'Unknown')
                    # This check is tricky effectively because we don't know the exact folder structure 
                    # from just the song name if it wasn't stored fully. 
                    # But user wants "corrupted" if something is wrong.
                    
                    self.replays.append({
                        'filename': f,
                        'song': song_name,
                        'score': data.get('score', 0),
                        'max_score': data.get('max_score', 0),
                        'timestamp': data.get('timestamp', 0),
                        'difficulty': data.get('difficulty', 'MEDIUM'),
                        'full_data': data,
                        'corrupted': is_corrupted
                    })
            except Exception as e:
                print(f"Failed to load replay {f}: {e}")
                # Add as corrupted entry so user can delete it
                self.replays.append({
                    'filename': f,
                    'song': "Unknown (Corrupted)",
                    'score': 0,
                    'timestamp': 0,
                    'difficulty': "???",
                    'corrupted': True
                })
                
    def draw(self, surface):
        r = self.game.renderer
        theme = r.get_theme()
        surface.fill(theme["bg"])
        
        # Header
        r.draw_text(surface, "REPLAYS", 50, 50, theme["primary"], r.big_font)
        
        # Panel
        panel_x, panel_y = 50, 100
        panel_w, panel_h = 600, 550
        r.draw_panel(surface, panel_x, panel_y, panel_w, panel_h, "SAVED GAMES")
        
        if not self.replays:
            r.draw_centered_text(surface, "No replays found.", panel_x + panel_w//2, panel_y + 100, (150, 150, 150))
            r.draw_text(surface, "[ESC] BACK", 50, 700, theme["secondary"])
            return

        # List
        visible_count = 10
        start_idx = self.scroll_offset
        end_idx = min(len(self.replays), start_idx + visible_count)
        
        y = panel_y + 43 # Matched offset with SongSelectScene to prevent clipping
        for i in range(start_idx, end_idx):
            item = self.replays[i]
            is_selected = (i == self.selected_index)
            
            # Draw Item
            bg_col = (40, 40, 40) if is_selected else (20, 20, 20)
            if is_selected:
                r.draw_styled_rect(surface, panel_x + 10, y, panel_w - 20, 50, theme["grid"], theme["primary"], 2)
            else:
                r.draw_styled_rect(surface, panel_x + 10, y, panel_w - 20, 50, bg_col)

            # Details
            col = theme["text"] if is_selected else (200, 200, 200)
            
            # Format Date
            date_str = "Unknown Date"
            try:
                ts = float(item.get('timestamp', 0))
                date_str = time.strftime('%Y-%m-%d %H:%M', time.localtime(ts))
            except:
                pass
            
            # Check for missing song
            song_path = os.path.join("songs", item.get('song_filename', ''))
            # Try legacy 'song' field if song_filename missing (older replays might store just name)
            if not os.path.exists(song_path):
                 # Try to assume folder name = song name
                 song_path = os.path.join("songs", item.get('song', ''), "audio.mp3") 
            
            # Song Title
            if item.get('corrupted', False):
                 r.draw_text(surface, f"⚠ CORRUPTED REPLAY", panel_x + 20, y + 15, theme["error"], r.font)
            else:
                 r.draw_text(surface, f"{item['song']} [{item['difficulty']}]", panel_x + 20, y + 15, col, r.font)
            
            # Score
            score_txt = f"{item['score']:,}"
            r.draw_text(surface, score_txt, panel_x + 400, y + 15, theme["secondary"])
            
            # Date
            r.draw_text(surface, date_str, panel_x + 20, y - 10, (100, 100, 100), r.small_font)
            
            y += 55

        # Controls Hint
        r.draw_text(surface, "[ENTER] WATCH   [DEL] DELETE   [ESC] BACK", 50, 700, theme["secondary"])

        # Scrollbar logic would go here if needed
        if start_idx > 0:
            r.draw_text(surface, "▲", panel_x + panel_w - 30, panel_y + 10, theme["primary"])
        if end_idx < len(self.replays):
            r.draw_text(surface, "▼", panel_x + panel_w - 30, panel_y + panel_h - 25, theme["primary"])

    def handle_input(self, event):
        if event.type != pygame.KEYDOWN:
            return
            
        if event.key == pygame.K_UP:
            if self.selected_index > 0:
                self.selected_index -= 1
                if self.selected_index < self.scroll_offset:
                    self.scroll_offset = self.selected_index
                self.play_sfx("blip")
        elif event.key == pygame.K_DOWN:
            if self.selected_index < len(self.replays) - 1:
                self.selected_index += 1
                if self.selected_index >= self.scroll_offset + self.visible_items:
                    self.scroll_offset = self.selected_index - self.visible_items + 1
                self.play_sfx("blip")
        elif event.key == pygame.K_RETURN:
            if self.replays:
                self.play_replay(self.replays[self.selected_index])
        elif event.key == pygame.K_DELETE:
            if self.replays:
                self.delete_replay(self.selected_index)
        elif event.key == pygame.K_ESCAPE:
            self.game.scene_manager.switch_to(TitleScene)

    def play_replay(self, replay_meta):
        from scenes.game_scene import GameScene
        data = replay_meta['full_data']
        
        params = {
            'song': data.get('song'), # Filename or path
            'difficulty': data.get('difficulty'),
            'mode': 'single', # Replay is essentially single player view
            'replay_mode': True,
            'replay_data': data,
            'autoplay': False
        }
        self.game.scene_manager.switch_to(GameScene, params)
    
    def delete_replay(self, index):
        item = self.replays[index]
        try:
            os.remove(os.path.join("replays", item['filename']))
            self.replays.pop(index)
            if self.selected_index >= len(self.replays):
                self.selected_index = max(0, len(self.replays) - 1)
            self.play_sfx("back")
        except Exception as e:
            print(f"Error deleting replay: {e}")

class CreditsScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.wyind_url = "https://ko-fi.com/wyind"
        self.ryan_url = "https://ryanpc.org"
        
        # Link Rects for mouse interaction (initialized in draw)
        self.link1_rect = None
        self.link2_rect = None

    def draw(self, surface):
        theme = self.game.renderer.get_theme()
        r = self.game.renderer
        sw = surface.get_width()
        sh = surface.get_height()

        # 1. Background (Grid)
        t = pygame.time.get_ticks()
        surface.fill(theme["bg"])
        grid_offset_y = (t * 0.1) % 40
        grid_col = theme["grid"]
        
        for y in range(0, sh + 40, 40):
            line_y = y + grid_offset_y - 40
            pygame.draw.line(surface, grid_col, (0, line_y), (sw, line_y))
        for x in range(0, sw, 40):
            pygame.draw.line(surface, grid_col, (x, 0), (x, sh))
            
        # Header
        r.draw_text(surface, "DEVELOPER CREDITS", 50, 50, theme["primary"], r.big_font)
        
        # Developer Cards
        
        # Card 1: Wyind (Frontend)
        card1_x = sw // 2 - 350
        card1_y = 150
        r.draw_panel(surface, card1_x, card1_y, 700, 180, "DEV_01")
        
        r.draw_text(surface, "WYIND", card1_x + 30, card1_y + 40, theme["primary"], r.big_font)
        r.draw_text(surface, "LEAD FRONTEND DEV", card1_x + 30, card1_y + 90, theme["secondary"])
        r.draw_text(surface, "Engine Core • UI/UX Implementation • Audio System", card1_x + 30, card1_y + 125, theme["text"])
        
        # Link 1
        link1_text = f"[1] {self.wyind_url.replace('https://', '')}"
        link1_surf = r.font.render(link1_text, True, (100, 200, 255))
        self.link1_rect = link1_surf.get_rect(topleft=(card1_x + 450, card1_y + 40))
        surface.blit(link1_surf, self.link1_rect)

        # Card 2: Ryan (Backend & Design)
        card2_x = sw // 2 - 350
        card2_y = 360
        r.draw_panel(surface, card2_x, card2_y, 700, 180, "DEV_02")
        
        r.draw_text(surface, "RYAN", card2_x + 30, card2_y + 40, theme["primary"], r.big_font)
        r.draw_text(surface, "BACKEND & DESIGN LEAD", card2_x + 30, card2_y + 90, theme["secondary"])
        r.draw_text(surface, "Server Architecture • Game Design • Database • Security", card2_x + 30, card2_y + 125, theme["text"])
        
        # Link 2
        link2_text = f"[2] {self.ryan_url.replace('https://', '')}"
        link2_surf = r.font.render(link2_text, True, (100, 200, 255))
        self.link2_rect = link2_surf.get_rect(topleft=(card2_x + 450, card2_y + 40))
        surface.blit(link2_surf, self.link2_rect)

        # Footer (Interact Hint)
        r.draw_text(surface, "Click links or press [1]/[2] to open", sw//2 - 180, 600, (80, 80, 80))
        r.draw_text(surface, "[ESC] RETURN", 50, sh - 50, theme["secondary"])

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN:
                self.play_sfx("back")
                self.game.scene_manager.switch_to(TitleScene)
            
            elif event.key == pygame.K_1 or event.key == pygame.K_KP1:
                self._open_url(self.wyind_url)
            elif event.key == pygame.K_2 or event.key == pygame.K_KP2:
                self._open_url(self.ryan_url)
                
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Left click
                pos = event.pos
                if self.link1_rect and self.link1_rect.collidepoint(pos):
                    self._open_url(self.wyind_url)
                elif self.link2_rect and self.link2_rect.collidepoint(pos):
                    self._open_url(self.ryan_url)

    def _open_url(self, url):
        self.play_sfx("accept")
        try:
            print(f"Opening URL: {url}")
            webbrowser.open(url)
        except Exception as e:
            print(f"Failed to open URL: {e}")
class HowToPlayScene(Scene):
    def on_enter(self, params=None):
        self.game.discord.update("Reading Instructions", "How to Play")
        
    def draw(self, surface):
        r = self.game.renderer
        theme = r.get_theme()
        
        # Get actual screen dimensions
        sw = surface.get_width()
        sh = surface.get_height()
        
        surface.fill(theme["bg"])
        
        # Header
        r.draw_text(surface, "◉ HOW TO PLAY ◉", 50, 30, theme["primary"], r.big_font)
        
        # Content Panel - adjust for screen size
        margin = 50
        panel_x = margin
        panel_y = 100
        panel_w = min(900, sw - margin * 2)  # Cap width for ultra-wide
        panel_h = sh - 150
        
        r.draw_panel(surface, panel_x, panel_y, panel_w, panel_h, "INSTRUCTIONS")
        
        # Determine current keybinds for display
        binds = self.game.settings.get("keybinds")
        keys = [pygame.key.name(k).upper() for k in binds]
        
        # 1. The Basics
        y = panel_y + 45
        x = panel_x + 30
        
        r.draw_text(surface, "OBJECTIVE", x, y, theme["secondary"])
        y += 30
        r.draw_text(surface, "Hit notes as they reach the receptors.", x, y, theme["text"])
        y += 25
        r.draw_text(surface, "Sync your key presses with the music!", x, y, theme["text"])
        
        y += 45
        r.draw_text(surface, "CONTROLS", x, y, theme["secondary"])
        y += 30
        
        # Draw keybind boxes
        key_x = x
        for i, k in enumerate(keys):
            pygame.draw.rect(surface, theme["grid"], (key_x, y, 50, 50))
            pygame.draw.rect(surface, theme["primary"], (key_x, y, 50, 50), 2)
            # Center vertically better (50px box, ~40px font -> 5px padding)
            r.draw_centered_text(surface, k, key_x + 25, y + 5, theme["primary"], r.big_font, shadow=False)
            
            # Label
            r.draw_centered_text(surface, f"L{i+1}", key_x + 25, y + 55, (150, 150, 150), r.small_font, shadow=False)
            key_x += 65
            
        y += 85
        r.draw_text(surface, "TIPS", x, y, theme["secondary"])
        y += 28
        tips = [
            "• Watch your HEALTH bar!",
            "• Hold notes must be released on time.",
            "• Adjust SCROLL SPEED in options.",
            "• Use OFFSET if audio feels off."
        ]
        for tip in tips:
            r.draw_text(surface, tip, x, y, theme["text"])
            y += 24
        
        # Interactive Visual (Right Side) - only if screen is wide enough
        if panel_w > 600:
            vis_x = panel_x + panel_w - 220
            vis_y = panel_y + 100
            
            # Draw a little fake lane
            pygame.draw.rect(surface, (20, 20, 20), (vis_x, vis_y, 180, 250))
            pygame.draw.rect(surface, theme["grid"], (vis_x, vis_y, 180, 250), 1)
            
            # Draw receptors (at top)
            pygame.draw.rect(surface, (50, 50, 50), (vis_x + 10, vis_y + 20, 35, 10))
            pygame.draw.rect(surface, (50, 50, 50), (vis_x + 50, vis_y + 20, 35, 10))
            
            # Draw a note approaching (Upscroll: Move Up)
            # Start at bottom (220), end at top (20)
            anim_pct = (pygame.time.get_ticks() % 1000 / 1000.0)
            note_y = (vis_y + 220) - (anim_pct * 200) # Move up 200px
            
            pygame.draw.rect(surface, theme["primary"], (vis_x + 50, int(note_y), 35, 10))
            
            # Explanation arrow (At top receptor)
            r.draw_text(surface, "<- HIT!", vis_x + 95, vis_y + 15, theme["primary"], r.small_font)
        
        r.draw_text(surface, "[ESC] BACK", 50, sh - 40, (150, 150, 150))

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN:
                self.game.scene_manager.switch_to(TitleScene)
