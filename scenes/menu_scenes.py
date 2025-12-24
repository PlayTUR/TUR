import pygame
from core.scene_manager import Scene
from core.config import *
import os
import math
import webbrowser
from core.localization import get_text

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
        self.menu_items = ["SINGLE PLAYER", "STORY CAMPAIGN", "MULTIPLAYER", "OPTIONS", "CREDITS", "SYSTEM UPDATE"]
        if pygame.joystick.get_count() > 0:
            self.menu_items.insert(5, "CONTROLLER CONFIG")
        self.menu_items.append("SUPPORT")
        self.menu_items.append("EXIT")
        
        self.selected_index = 0
        self.show_exit_confirm = False
        self.show_donate_confirm = False
        
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

    def draw(self, surface):
        theme = self.game.renderer.get_theme()
        
        # 1. Background Grid Effect
        t = pygame.time.get_ticks()
        
        # Draw BG
        surface.fill(theme["bg"])
        
        grid_offset_y = (t * 0.1) % 40
        grid_col = theme["grid"]
        
        # Horizontal
        for y in range(0, SCREEN_HEIGHT + 40, 40):
            line_y = y + grid_offset_y - 40
            pygame.draw.line(surface, grid_col, (0, line_y), (SCREEN_WIDTH, line_y))
            
        # Vertical
        for x in range(0, SCREEN_WIDTH, 40):
            pygame.draw.line(surface, grid_col, (x, 0), (x, SCREEN_HEIGHT))

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
        q_rect = q_surf.get_rect(center=(SCREEN_WIDTH//2, 280))
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

        # 3. Interactive Menu Box
        menu_start_y = 350
        menu_h = len(self.menu_items) * 40 + 40 # Compact spacing
        menu_w = 400 # Smaller width
        menu_x = (SCREEN_WIDTH - menu_w) // 2
        
        # Draw Window Border
        pygame.draw.rect(surface, theme["bg"], (menu_x, menu_start_y, menu_w, menu_h))
        pygame.draw.rect(surface, theme["grid"], (menu_x, menu_start_y, menu_w, menu_h), 2)
        pygame.draw.rect(surface, theme["grid"], (menu_x, menu_start_y-30, menu_w, 30))
        self.game.renderer.draw_text(surface, "SYSTEM//MENU", menu_x + 10, menu_start_y - 25, theme["text"])
        
        for i, item in enumerate(self.menu_items):
            color = theme["primary"] if i == self.selected_index else theme["text"]
            
            # Special color for Support
            if item == "SUPPORT":
                color = (255, 200, 0) if i == self.selected_index else (200, 150, 0)
                
            prefix = " > " if i == self.selected_index else "   "
            
            # Translate item
            display_item = get_text(self.game, item)
            txt = f"{prefix}{display_item}"
            x = menu_x + 40
            # Use normal font instead of big_font for smaller look
            self.game.renderer.draw_text(surface, txt, x, menu_start_y + 20 + i * 40, color, self.game.renderer.font)
            
        # 4. User Info / Auth UI (Simple bottom text - no panel)
        name = self.game.settings.get('name')
        account_type = self.game.settings.get('account_type')
        
        if account_type == "GUEST":
            self.game.renderer.draw_text(surface, "GUEST MODE  |  [L] LOGIN  [R] REGISTER  [P] PROFILE", 20, SCREEN_HEIGHT - 30, theme["secondary"])
        else:
            self.game.renderer.draw_text(surface, f"◉ {name}  |  [L] LOGOUT  [P] PROFILE", 20, SCREEN_HEIGHT - 30, theme["primary"])
        
        if hasattr(self.game, 'current_bgm_title') and self.game.current_bgm_title:
             r_text = f"NOW PLAYING: {self.game.current_bgm_title}"
             max_w = 400
             lines = self.game.renderer.wrap_text(r_text, 40)
             
             start_y = 60
             for i, line in enumerate(lines):
                 lw, lh = self.game.renderer.font.size(line)
                 self.game.renderer.draw_text(surface, line, SCREEN_WIDTH - lw - 20, start_y + i * 20, theme["secondary"], self.game.renderer.font)
             
             # Control hints
             ctrl_msg = "[S] SHUFFLE  [TAB] NEXT"
             cw, ch = self.game.renderer.font.size(ctrl_msg)
             self.game.renderer.draw_text(surface, ctrl_msg, SCREEN_WIDTH - cw - 20, start_y + (len(lines)) * 20 + 5, (100, 100, 100), self.game.renderer.font)

        # 5. Exit Confirmation Overlay
        if self.show_exit_confirm:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(200)
            overlay.fill((0,0,0))
            surface.blit(overlay, (0,0))
            w, h = 600, 250
            x, y = (SCREEN_WIDTH - w)//2, (SCREEN_HEIGHT - h)//2
            pygame.draw.rect(surface, theme["bg"], (x, y, w, h))
            pygame.draw.rect(surface, theme["error"], (x, y, w, h), 2)
            title = "TERMINATE SYSTEM?"
            sub = "CONFIRM SHUTDOWN [Y/N]"
            font = self.game.renderer.big_font
            tw, th = font.size(title)
            self.game.renderer.draw_text(surface, title, x + (w-tw)//2, y + 60, theme["error"], font)
            font_small = self.game.renderer.font
            sw, sh = font_small.size(sub)
            self.game.renderer.draw_text(surface, sub, x + (w-sw)//2, y + 140, theme["text"], font_small)

        # 6. Donate Confirmation
        if self.show_donate_confirm:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.fill((0,0,0))
            overlay.set_alpha(200)
            surface.blit(overlay, (0,0))
            w, h = 700, 300
            x, y = (SCREEN_WIDTH - w)//2, (SCREEN_HEIGHT - h)//2
            pygame.draw.rect(surface, theme["bg"], (x, y, w, h))
            pygame.draw.rect(surface, (255, 200, 0), (x, y, w, h), 2)
            title = "EXTERNAL LINK WARNING"
            url = "https://ko-fi.com/wyind"
            msg1 = "This will open a web browser to:"
            msg2 = url
            confirm = "Proceed? [Y] Yes   [N] No"
            r = self.game.renderer
            
            # Helper for centering
            def draw_centered(text, y_offset, color, font=r.font):
                tw, th = font.size(text)
                r.draw_text(surface, text, x + (w - tw)//2, y + y_offset, color, font)

            draw_centered(title, 30, (255, 200, 0), r.big_font)
            draw_centered(msg1, 100, theme["text"])
            draw_centered(msg2, 140, (0, 255, 255), r.big_font)
            draw_centered(confirm, 220, theme["secondary"])

        # 7. Show converting status (FINAL LAYER - TOP PRIORITY)
        if self.converting:
            r = self.game.renderer
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(200)
            overlay.fill((5, 5, 10))
            surface.blit(overlay, (0,0))
            
            box_w, box_h = 640, 120
            bx, by = (SCREEN_WIDTH - box_w)//2, (SCREEN_HEIGHT - box_h)//2 + 50
            
            pygame.draw.rect(surface, theme["bg"], (bx, by, box_w, box_h))
            pygame.draw.rect(surface, theme["primary"], (bx, by, box_w, box_h), 2)
            
            r.draw_text(surface, "SYSTEM INITIALIZING DATA...", bx + 20, by + 15, theme["primary"])
            status_text = f"SYS//INIT: {self.convert_status}"
            if len(status_text) > 55: status_text = status_text[:52] + "..."
            r.draw_text(surface, status_text, bx + 20, by + 45, (255, 255, 255))
            
            bar_w = int((box_w - 40) * (self.convert_pct / 100))
            pygame.draw.rect(surface, (40, 40, 40), (bx + 20, by + 85, box_w - 40, 15))
            if bar_w > 0:
                pygame.draw.rect(surface, theme["secondary"], (bx + 20, by + 85, bar_w, 15))
                glow = pygame.Surface((bar_w, 15), pygame.SRCALPHA)
                glow.fill((*theme["secondary"], 100))
                surface.blit(glow, (bx + 20, by + 85))

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
                        webbrowser.open("https://ko-fi.com/wyind")
                    except:
                        pass
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
                if choice == "SINGLE PLAYER":
                    self.game.scene_manager.switch_to(SongSelectScene)
                elif choice == "STORY CAMPAIGN":
                    from scenes.story_scene import StoryScene
                    self.game.scene_manager.switch_to(StoryScene)
                elif choice == "MULTIPLAYER":
                    from scenes.lobby_scene import LobbyScene
                    self.game.scene_manager.switch_to(LobbyScene)
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
                    self.game.scene_manager.switch_to(AuthScene, {'mode': 'LOGIN'})
            
            elif event.key == pygame.K_r:
                # Register (Check Cooldown)
                import time
                last_change = self.game.settings.get("last_name_change") or 0
                now = time.time()
                days_passed = (now - last_change) / (60 * 60 * 24) if last_change > 0 else 999
                
                # Allow register if guest OR enough time passed
                if self.game.settings.get("account_type") == "GUEST" or days_passed >= 3:
                     from scenes.auth_scene import AuthScene
                     self.game.scene_manager.switch_to(AuthScene, {'mode': 'REGISTER'})
                else:
                     # Deny with SFX
                     self.play_sfx("error")
                     print(f"Cannot register yet. Wait {3-days_passed:.1f} more days.")
            
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




class SongSelectScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.songs = []
        self.selected_index = 0
        self.difficulties = DIFFICULTIES
        self.diff_index = 1
        self.load_songs()

    def on_enter(self, params=None):
        self.game.discord.update("Selecting Song", "In Menu")
        self.load_songs()
        self.mode = params.get('mode', 'single') if params else 'single'

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
        r.draw_panel(surface, 40, 100, 550, 480, "AVAILABLE_SONGS")
        
        if not self.songs:
            r.draw_text(surface, "No songs found!", 60, 130, theme["error"])
            r.draw_text(surface, "Add .mp3/.wav/.ogg/.osz or .tur files to 'songs' folder", 60, 165, (120, 120, 120))
        else:
            visible_count = 10
            start_idx = max(0, self.selected_index - 5)
            end_idx = min(len(self.songs), start_idx + visible_count)
            
            for i in range(start_idx, end_idx):
                song = self.songs[i]
                y_pos = 125 + (i - start_idx) * 44
                
                # Get song name without extension (cleaner display)
                name = os.path.splitext(song)[0]
                
                if i == self.selected_index:
                    score_data = self.game.score_manager.get_score(song, self.difficulties[self.diff_index])
                    suffix = f" [{score_data['rank']}]" if score_data else ""
                    
                    # Truncate to fit panel
                    max_len = 40 - len(suffix)
                    display = name[:max_len] + "..." if len(name) > max_len else name
                    
                    pygame.draw.rect(surface, theme["grid"], (45, y_pos - 3, 540, 40))
                    r.draw_text(surface, f"> {display}{suffix}", 55, y_pos + 5, theme["primary"])
                else:
                    display = name[:42] + "..." if len(name) > 42 else name
                    r.draw_text(surface, f"  {display}", 55, y_pos + 5, theme["text"])
            
            # Scroll indicators
            if start_idx > 0:
                r.draw_text(surface, "↑ more", 280, 108, (80, 80, 80))
            if end_idx < len(self.songs):
                r.draw_text(surface, "↓ more", 280, 555, (80, 80, 80))
        
        # Difficulty panel
        r.draw_panel(surface, 620, 100, 340, 140, "DIFFICULTY")
        
        # Difficulty
        diff = self.difficulties[self.diff_index]
        diff_color = theme["error"] if diff in ["HARD", "EXTREME", "FUCK YOU"] else theme["secondary"]
        
        # Center difficulty
        diff_text = f"< {diff} >"
        diff_w = r.big_font.size(diff_text)[0]
        r.draw_text(surface, diff_text, 620 + (340 - diff_w) // 2, 145, diff_color, r.big_font)
        r.draw_text(surface, "[←/→] to change", 720, 205, (80, 80, 80))
        
        # Controls panel
        r.draw_panel(surface, 620, 270, 340, 200, "CONTROLS")
        controls = [
            ("[↑/↓]", "Select Song"),
            ("[ENTER]", "Play"),
            ("[E]", "Beatmap Editor"),
            ("[S]", "Shuffle List"),
            ("[R]", "Random Song"),
            ("[F5]", "Refresh List"),
            ("[ESC]", "Back to Menu")
        ]
        y = 295
        for key, action in controls:
            r.draw_text(surface, key, 640, y, theme["secondary"])
            r.draw_text(surface, action, 720, y, theme["text"])
            y += 35
        
        # Download panel
        r.draw_panel(surface, 620, 500, 340, 80, "DOWNLOAD")
        r.draw_text(surface, "[D] Download Songs", 640, 525, theme["text"])
        
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

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.play_sfx("back")
                self.game.scene_manager.switch_to(TitleScene)
            elif event.key == pygame.K_F5:
                self.play_sfx("hdd") # "Reload" sound
                
                # Run conversion first to catch new MP3s
                from core.song_converter import auto_convert_songs
                auto_convert_songs("songs", "MEDIUM")
                
                # Clear cache to force rescan
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
                    # check if multiplayer
                    if self.game.network.connected:
                        # Send Proposal
                        song = self.songs[self.selected_index]
                        diff = self.difficulties[self.diff_index]
                        self.game.network.propose_song(song, diff)
                        # Show status "Waiting"
                    else:
                        from scenes.game_scene import GameScene
                        self.game.scene_manager.switch_to(GameScene, {
                            'song': self.songs[self.selected_index],
                            'difficulty': self.difficulties[self.diff_index]
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
            "GAMEPLAY": ["SPEED", "UPSCROLL", "NOTE STYLE", "SCREEN SHAKE", "RE-GEN MAPS", "LANGUAGE", "VIM BINDINGS"],
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
        for cat in self.all_items:
            self.all_items[cat].append("BACK")
            
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
            col = theme["primary"] if is_active else (150, 150, 150)
            
            # Highlight Active Tab
            if is_active:
                tw, th = r.font.size(tab_text)
                pygame.draw.rect(surface, (*theme["primary"], 50), (tab_x - 10, tab_y - 5, tw + 20, th + 10), 0)
                pygame.draw.rect(surface, theme["primary"], (tab_x - 10, tab_y - 5, tw + 20, th + 10), 1)
                
            r.draw_text(surface, tab_text, tab_x, tab_y, col)
            tab_x += r.font.size(tab_text)[0] + 40

        # Settings panel - draw title ABOVE the panel
        cat_title = get_text(self.game, self.tabs[self.current_tab])
        r.draw_text(surface, f"◉ {cat_title}", 55, 128, theme["secondary"])
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
            color = theme["primary"] if selected else theme["text"]
            
            if selected:
                pygame.draw.rect(surface, theme["grid"], (55, y - 2, 540, 32))
            
            # Label
            display_label = get_text(self.game, label)
            prefix = "◉ " if selected else "  "
            r.draw_text(surface, f"{prefix}{display_label}", 70, y, color)
            
            if value:
                val_col = theme["secondary"] if selected else (120, 120, 150)
                vw = r.font.size(value)[0]
                # Keep value inside panel bounds (panel ends at 600)
                r.draw_text(surface, value, min(580 - vw, 350), y, val_col)
            y += 44

        # Scroll indicators (positioned inside panel bounds)
        if self.scroll_offset > 0:
            r.draw_text(surface, "▲ MORE", 280, 153, (100, 100, 100))
        if self.scroll_offset + self.visible_items < len(items):
            r.draw_text(surface, "▼ MORE", 280, 595, (100, 100, 100))

        # Help panel (Right side, standardized position)
        r.draw_panel(surface, 600, 125, 380, 200, "CONTROLS")
        r.draw_text(surface, "[↑/↓] Navigate", 620, 150, theme["text"])
        r.draw_text(surface, "[Q/E] Switch Tabs", 620, 180, theme["secondary"])
        r.draw_text(surface, "[←/→] Adjust", 620, 215, theme["text"])
        r.draw_text(surface, "[SHIFT] Fast Adjust", 620, 245, theme["text"])
        r.draw_text(surface, "[ENTER] Select", 620, 275, theme["text"])
        r.draw_text(surface, "[ESC] Back", 620, 305, theme["text"])
        
        # Theme preview (Right side, standardized position)
        r.draw_panel(surface, 600, 355, 380, 180, "THEME_PREVIEW")
        pygame.draw.rect(surface, theme["primary"], (620, 380, 40, 25))
        r.draw_text(surface, "Primary", 670, 383, theme["text"])
        pygame.draw.rect(surface, theme["secondary"], (620, 415, 40, 25))
        r.draw_text(surface, "Secondary", 670, 418, theme["text"])
        pygame.draw.rect(surface, theme["bg"], (620, 450, 40, 25))
        pygame.draw.rect(surface, theme["grid"], (620, 450, 40, 25), 1)
        r.draw_text(surface, "Background", 670, 453, theme["text"])

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
            
            # Progress Box (Wider for long song names)
            box_w, box_h = 700, 150
            bx, by = (SCREEN_WIDTH - box_w)//2, (SCREEN_HEIGHT - box_h)//2
            pygame.draw.rect(surface, theme["bg"], (bx, by, box_w, box_h))
            pygame.draw.rect(surface, theme["primary"], (bx, by, box_w, box_h), 2)
            
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
            
        elif item == "NOTE STYLE":
            shapes = ["BAR", "CIRCLE", "ARROW"]
            cur = s.get("note_shape") or "BAR"
            try:
                idx = shapes.index(cur)
            except:
                idx = 0
            new_idx = (idx + direction) % len(shapes)
            s.set("note_shape", shapes[new_idx])
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
            self.game.renderer.draw_text(surface, "PRESS A CONTROLLER BUTTON", SCREEN_WIDTH//2 - 140, 460, (255, 255, 255))
        else:
            self.game.renderer.draw_text(surface, "PRESS [ENTER] TO REBIND ALL LANES", SCREEN_WIDTH//2 - 180, 500, (200, 200, 200))
            
            # Show Binds
            binds = self.game.settings.get("joy_binds")
            for i, b in enumerate(binds):
                self.game.renderer.draw_text(surface, f"LANE {i}: BTN {b}", 400, 550 + i * 30, theme["primary"])

        self.game.renderer.draw_text(surface, "[ESC] BACK", 100, 700, theme["secondary"])

    def handle_input(self, event):
        if self.rebind_mode:
            if event.type == pygame.JOYBUTTONDOWN:
                self.play_sfx("accept")
                self.temp_joy_binds[self.rebind_step] = event.button
                self.rebind_step += 1
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


class CreditsScene(Scene):
    def draw(self, surface):
        theme = self.game.renderer.get_theme()
        r = self.game.renderer

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
        r.draw_text(surface, "DEVELOPER CREDITS", 50, 50, theme["primary"], r.big_font)
        
        # Scroll Bar logic....game.renderer.big_font)
        
        # Wyind
        self.game.renderer.draw_text(surface, "WYIND - LEAD DEV", 150, 200, theme["secondary"], self.game.renderer.big_font)
        self.game.renderer.draw_text(surface, "ENGINE ARCHITECTURE / CORE SYSTEMS", 150, 240, theme["text"])
        
        self.game.renderer.draw_text(surface, "RYAN - LEAD DEV", 150, 350, theme["secondary"], self.game.renderer.big_font)
        self.game.renderer.draw_text(surface, "USER EXPERIENCE / FEATURE ENHANCEMENTS", 150, 390, theme["text"])
        
        self.game.renderer.draw_text(surface, "[ESC] RETURN", 100, 650, theme["secondary"])

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.play_sfx("back")
                self.game.scene_manager.switch_to(TitleScene)
