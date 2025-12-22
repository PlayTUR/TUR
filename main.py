import pygame
import os
import time
import sys
import platform
from core.renderer import PygameRenderer
from core.scene_manager import SceneManager
from scenes.menu_scenes import TitleScene
from core.settings_manager import SettingsManager
from core.audio_manager import AudioManager
from core.beatmap_generator import BeatmapGenerator
from core.network_manager import NetworkManager
from core.score_manager import ScoreManager
from core.config import *

# Platform-specific fixes BEFORE pygame.init()
if platform.system() == "Linux":
    # Fix for Hyprland/Wayland/tiling WM flickering
    # These environment variables help stabilize the window
    os.environ['SDL_VIDEO_X11_WMCLASS'] = "tur"
    os.environ['SDL_VIDEO_MINIMIZE_ON_FOCUS_LOSS'] = "0"
    
    # Check if running on Wayland with XWayland or native Wayland
    session_type = os.environ.get('XDG_SESSION_TYPE', '')
    if session_type == 'wayland':
        # Use X11 backend for better stability on Hyprland
        os.environ['SDL_VIDEODRIVER'] = 'x11'
    
    # Hyprland-specific: Request floating window via SDL hint
    # This prevents tiling issues and flickering
    os.environ['SDL_VIDEO_X11_NET_WM_BYPASS_COMPOSITOR'] = "0"

# Main Pygame Entry Point
class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        
        # Debug Mode
        self.debug_mode = "-D" in sys.argv
        if self.debug_mode:
            print("DEBUG MODE ENABLED")
        
        # Settings First
        self.settings = SettingsManager()
        
        # Display Setup
        res = self.settings.get("resolution")
        fs = self.settings.get("fullscreen")
        self.flags = pygame.RESIZABLE if not fs else pygame.FULLSCREEN | pygame.RESIZABLE
        
        self.screen = pygame.display.set_mode(res, self.flags)
        pygame.display.set_caption("TUR [V8.0]")
        
        # Virtual Resolution
        self.virtual_w = 1024
        self.virtual_h = 768
        self.virtual_surface = pygame.Surface((self.virtual_w, self.virtual_h))

        # Modules
        self.renderer = PygameRenderer(self.virtual_w, self.virtual_h)
        self.renderer.game = self # Inject ASAP for theme access
        self.audio = AudioManager()
        self.score_manager = ScoreManager()
        from core.leaderboard_manager import LeaderboardManager
        self.leaderboard_manager = LeaderboardManager(self)
        from core.discord_manager import DiscordRPCManager
        self.discord = DiscordRPCManager(self)
        self.generator = BeatmapGenerator()
        self.network = NetworkManager()
        self.scene_manager = SceneManager(self)
        
        # Input: Controller
        pygame.joystick.init()
        self.joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
        for j in self.joysticks: j.init()
        print(f"DEBUG: Controllers Found: {len(self.joysticks)}")
        
        vol = self.settings.get("volume")
        pygame.mixer.music.set_volume(vol)
        
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Playlist logic
        self.menu_playlist = []
        self.playlist_index = 0
        
        # System State
        self.shutting_down = False
        self.shutdown_alpha = 0
        self.current_bgm_title = ""
        
        # Tools
        from core.performance_monitor import PerformanceMonitor
        self.monitor = PerformanceMonitor(self)

    def run(self):
        # Always Start with Boot Sequence
        from scenes.boot_scene import BootScene
        self.scene_manager.switch_to(BootScene)
        
        # Note: BootScene exits to Setup or Title automatically
        
        # Initial Check
        if self.flags & pygame.RESIZABLE:
            pygame.event.pump()
            win_w, win_h = pygame.display.get_window_size()
            if win_w > 200 and win_h > 200:
                 self.screen = pygame.display.set_mode((win_w, win_h), pygame.RESIZABLE)
        
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            
            # Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.discord.close()
                    self.running = False
                elif event.type == pygame.VIDEORESIZE:
                    if self.flags & pygame.RESIZABLE:
                        self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F11:
                         pygame.display.toggle_fullscreen()
                    elif event.key == pygame.K_a and (pygame.key.get_mods() & pygame.KMOD_CTRL) and (pygame.key.get_mods() & pygame.KMOD_SHIFT):
                         if self.settings.get("is_admin"):
                             from scenes.admin_scene import AdminScene
                             self.scene_manager.push_scene(AdminScene)
                    else:
                        self.handle_input(event) 
                
                # Joystick Mapping (Simulate Keys)
                elif event.type == pygame.JOYBUTTONDOWN or event.type == pygame.JOYBUTTONUP:
                    is_down = (event.type == pygame.JOYBUTTONDOWN)
                    ev_type = pygame.KEYDOWN if is_down else pygame.KEYUP
                    btn = event.button
                    keys = self.settings.get("keybinds") 
                    sim_key = None

                    if self.debug_mode:
                        print(f"DEBUG: Joy Button {btn} {'DOWN' if is_down else 'UP'}")

                    # --- UNIVERSAL MENU NAVIGATION ---
                    # Button 0 (A/Cross), 1 (B/Circle), 2 (X/Square), 3 (Y/Triangle)
                    # Button 6 (Options/Select), 7 (Start/Options)
                    
                    if is_down:
                        if btn == 0: sim_key = pygame.K_RETURN   # Select/Confirm
                        elif btn == 1: sim_key = pygame.K_ESCAPE  # Back/Cancel
                        elif btn == 7 or btn == 6: sim_key = pygame.K_ESCAPE # Pause/Menu
                        elif btn == 10: sim_key = pygame.K_UP    # L-Stick Click?
                        elif btn == 11: sim_key = pygame.K_DOWN

                    # --- GAMEPLAY MAPPING (LB, RB, Face Buttons) ---
                    # User Request: LB (4), RB (5). Face: X(2), Y(3)
                    joy_binds = self.settings.get("joy_binds")
                    if btn in joy_binds:
                        lane_idx = joy_binds.index(btn)
                        sim_key = keys[lane_idx]

                    if sim_key:
                        self.handle_input(pygame.event.Event(ev_type, {'key': sim_key}))

                elif event.type == pygame.JOYAXISMOTION:
                    if not hasattr(self, 'axis_state'): self.axis_state = {}
                    axis = event.axis
                    val = event.value
                    keys = self.settings.get("keybinds")
                    
                    # Triggers (Lane 0 and 3)
                    # LT is often Axis 4 or 2. RT is 5.
                    if axis in [2, 4, 5]:
                        triggered = val > 0.5
                        if triggered and not self.axis_state.get(axis, False):
                            self.axis_state[axis] = True
                            k = keys[0] if axis in [2, 4] else keys[3]
                            self.handle_input(pygame.event.Event(pygame.KEYDOWN, {'key': k}))
                        elif not triggered and self.axis_state.get(axis, False):
                            self.axis_state[axis] = False
                            k = keys[0] if axis in [2, 4] else keys[3]
                            self.handle_input(pygame.event.Event(pygame.KEYUP, {'key': k}))

                    # L-Stick Navigation (Axis 0, 1)
                    if abs(val) > 0.5:
                        if axis == 1: # Y Axis
                            k = pygame.K_DOWN if val > 0 else pygame.K_UP
                            if not self.axis_state.get(axis, False):
                                self.axis_state[axis] = True
                                self.handle_input(pygame.event.Event(pygame.KEYDOWN, {'key': k}))
                        elif axis == 0: # X Axis
                            k = pygame.K_RIGHT if val > 0 else pygame.K_LEFT
                            if not self.axis_state.get(axis, False):
                                self.axis_state[axis] = True
                                self.handle_input(pygame.event.Event(pygame.KEYDOWN, {'key': k}))
                    else:
                        self.axis_state[axis] = False

                elif event.type == pygame.JOYHATMOTION:
                    # D-Pad Navigation
                    val = event.value
                    if val[1] == 1: self.handle_input(pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_UP}))
                    elif val[1] == -1: self.handle_input(pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_DOWN}))
                    elif val[0] == -1: self.handle_input(pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_LEFT}))
                    elif val[0] == 1: self.handle_input(pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_RIGHT}))
                        
                else:
                    self.handle_input(event)
                    
            # Logic
            self.scene_manager.update()
            
            # Draw to Virtual Surface
            self.virtual_surface.fill((0, 0, 0)) # Pure black background
            self.scene_manager.draw(self.virtual_surface)
            
            # Scale to Window
            screen_w, screen_h = self.screen.get_size()
            scale = min(screen_w / self.virtual_w, screen_h / self.virtual_h)
            new_w = int(self.virtual_w * scale)
            new_h = int(self.virtual_h * scale)
            
            scaled_surf = pygame.transform.scale(self.virtual_surface, (new_w, new_h))
            
            # Center it (Letterbox)
            dest_x = (screen_w - new_w) // 2
            dest_y = (screen_h - new_h) // 2
            
            self.screen.fill((0, 0, 0)) # Clear borders
            self.screen.blit(scaled_surf, (dest_x, dest_y))
            
            # Shutdown Fade Logic
            if self.shutting_down:
                self.shutdown_alpha += 5
                if self.shutdown_alpha >= 255:
                     self.shutdown_alpha = 255
                     self.running = False
                
                fade = pygame.Surface((screen_w, screen_h))
                fade.fill((0,0,0))
                fade.set_alpha(self.shutdown_alpha)
                self.screen.blit(fade, (0,0))
            
            # Draw Performance Overlay
            self.monitor.update()
            self.monitor.draw(self.screen)
            
            # Universal music update
            self.update_music()
            
            pygame.display.flip()
            
        pygame.quit()
        sys.exit()

    def trigger_reboot(self):
        # Starts exit sequence
        self.shutting_down = True
        self.shutdown_alpha = 0
            
    def handle_input(self, event):
        self.scene_manager.handle_input(event)

    def play_menu_bgm(self):
        # 1. Gather files
        mm_dir = "mainmenu_music"
        s_dir = "songs"
        
        # Explicit priority themes
        themes = []
        possible_themes = ["song1.mp3", "song2.mp3"]
        
        for t in possible_themes:
            # Check songs dir first
            p = os.path.join(s_dir, t)
            if os.path.exists(p):
                themes.append(p)
            else:
                # Check mainmenu dir
                p = os.path.join(mm_dir, t)
                if os.path.exists(p):
                     themes.append(p)
        
        # Other menu music
        mm_files = []
        if os.path.exists(mm_dir):
            mm_files = [os.path.join(mm_dir, f) for f in os.listdir(mm_dir) 
                       if f.lower().endswith(('.mp3', '.wav', '.ogg')) and f.lower() not in possible_themes]
            mm_files.sort()
            
        # Other songs
        song_files = []
        if os.path.exists(s_dir):
            song_files = [os.path.join(s_dir, f) for f in os.listdir(s_dir) 
                         if f.lower().endswith(('.mp3', '.wav', '.ogg')) and f.lower() not in possible_themes]
            import random
            random.shuffle(song_files)
            
        self.menu_playlist = themes + mm_files + song_files
        self.playlist_index = 0
        
        if self.menu_playlist:
            # If we are already playing something from the list, don't restart
            # If we are already playing something from the list, don't restart
            if pygame.mixer.music.get_busy():
                 return
            self.play_playlist_track(fade_ms=2000)
            
    def play_playlist_track(self, fade_ms=0):
        if not self.menu_playlist: return
        path = self.menu_playlist[self.playlist_index]
        
        from core.utils import find_resource
        resolved_path = find_resource(path, hint_dirs=["mainmenu_music", "songs"])
        
        if not resolved_path:
            print(f"WARNING: Menu track not found: {path}. Skipping...")
            self.playlist_index = (self.playlist_index + 1) % len(self.menu_playlist)
            return

        self.audio.load_song(resolved_path)
        pygame.mixer.music.play(0, fade_ms=fade_ms) 
        
        # Determine Title
        visible_fname = os.path.basename(resolved_path)
        lower_fname = visible_fname.lower()
        
        if lower_fname == "song1.mp3":
            self.current_bgm_title = "TUR Main Menu Theme - Wyind"
        elif lower_fname == "song2.mp3":
            self.current_bgm_title = "TUR Main Menu Theme (ALT) - Wyind"
        elif lower_fname == "turtherhythm.mp3":
            self.current_bgm_title = "TUR The Rhythm! - Wyind"
        else:
            # Check if it's from 'songs' dir
            if "songs" in os.path.dirname(path):
                # Try to read metadata
                try:
                    import eyed3
                    audiofile = eyed3.load(path)
                    if audiofile and audiofile.tag:
                        artist = audiofile.tag.artist or "Unknown"
                        title = audiofile.tag.title or os.path.splitext(visible_fname)[0]
                        self.current_bgm_title = f"{title} - {artist}"
                    else:
                         self.current_bgm_title = os.path.splitext(visible_fname)[0]
                except:
                     self.current_bgm_title = os.path.splitext(visible_fname)[0]
            else:
                # Main menu music -> just filename
                self.current_bgm_title = os.path.splitext(visible_fname)[0]

        self.playlist_index = (self.playlist_index + 1) % len(self.menu_playlist)
        
    def update_music(self):
        from scenes.game_scene import GameScene
        if isinstance(self.scene_manager.current_scene, GameScene): return

        if not pygame.mixer.music.get_busy():
            if self.menu_playlist:
                self.play_playlist_track(fade_ms=0) # No fade for next tracks

    def next_menu_track(self):
        """Manually skip to next track"""
        if self.menu_playlist:
            # Note: play_playlist_track increments index AFTER loading
            # So if we want to SKIP, we just call it.
            self.play_playlist_track(fade_ms=500)

    def shuffle_menu_playlist(self):
        """Shuffle the current menu playlist and restart play"""
        if self.menu_playlist:
            import random
            random.shuffle(self.menu_playlist)
            self.playlist_index = 0
            self.play_playlist_track(fade_ms=500)

if __name__ == "__main__":
    game = Game()
    game.run()
