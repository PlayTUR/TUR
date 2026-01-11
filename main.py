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
from core.master_client import get_master_client
from core.updater import get_updater
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


def create_linux_desktop_entry():
    """Create a .desktop entry for easy launching on Linux."""
    if platform.system() != "Linux":
        return
    
    # Check if we've already created it
    marker_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".desktop_created")
    if os.path.exists(marker_file):
        return
    
    try:
        # Get paths
        exe_path = os.path.abspath(sys.argv[0])
        exe_dir = os.path.dirname(exe_path)
        icon_path = os.path.join(exe_dir, "tur.ico")
        
        # Use XDG applications directory
        apps_dir = os.path.expanduser("~/.local/share/applications")
        os.makedirs(apps_dir, exist_ok=True)
        
        desktop_content = f"""[Desktop Entry]
Name=TUR
Comment=Terminal Underground Rhythm Game
Exec={exe_path}
Icon={icon_path}
Terminal=false
Type=Application
Categories=Game;
StartupWMClass=tur
"""
        
        desktop_path = os.path.join(apps_dir, "tur.desktop")
        with open(desktop_path, 'w') as f:
            f.write(desktop_content)
        
        # Make it executable
        os.chmod(desktop_path, 0o755)
        
        # Create marker file
        with open(marker_file, 'w') as f:
            f.write("1")
        
        print(f"Created desktop entry: {desktop_path}")
    except Exception as e:
        print(f"Failed to create desktop entry: {e}")


# Main Pygame Entry Point
class Game:
    def __init__(self):


        # Linux/Tiling WM Stability + Hyprland/NVIDIA Fixes
        if platform.system() == "Linux":
            os.environ['SDL_VIDEO_X11_WMCLASS'] = "tur"
            
            # Force X11 backend (more stable than Wayland for pygame)
            os.environ['SDL_VIDEODRIVER'] = "x11"
            
            # NVIDIA/Wayland compositor fixes
            os.environ['__GL_SYNC_TO_VBLANK'] = "1"
            os.environ['__GL_GSYNC_ALLOWED'] = "0"
            os.environ['__GL_VRR_ALLOWED'] = "0"
            
            # Disable compositor bypass (prevents flickering)
            os.environ['SDL_VIDEO_X11_NET_WM_BYPASS_COMPOSITOR'] = "0"
            
            # Double buffering for smoother rendering
            os.environ['SDL_RENDER_DRIVER'] = "opengl"
            os.environ['SDL_HINT_RENDER_VSYNC'] = "1"

        
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
        self.audio = AudioManager(self)
        self.score_manager = ScoreManager()
        from core.leaderboard_manager import LeaderboardManager
        self.leaderboard_manager = LeaderboardManager(self)
        from core.discord_manager import DiscordRPCManager
        self.discord = DiscordRPCManager(self)
        self.generator = BeatmapGenerator()
        self.network = NetworkManager()
        self.network.game = self
        self.master_client = get_master_client()
        self.master_client.start_monitoring()
        self.updater = get_updater()
        self.updater.check_for_updates_async()
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
        
        # Input State
        self.lane_state = [False] * 4
        self.axis_state = {}

    def get_virtual_pos(self, screen_pos):
        """Convert screen coordinates to virtual coordinates"""
        screen_w, screen_h = self.screen.get_size()
        scale = min(screen_w / self.virtual_w, screen_h / self.virtual_h)
        new_w = int(self.virtual_w * scale)
        new_h = int(self.virtual_h * scale)
        dest_x = (screen_w - new_w) // 2
        dest_y = (screen_h - new_h) // 2
        
        vx = (screen_pos[0] - dest_x) / scale
        vy = (screen_pos[1] - dest_y) / scale
        return vx, vy

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
                elif event.type == pygame.KEYDOWN or event.type == pygame.KEYUP:
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                         pygame.display.toggle_fullscreen()
                    else:
                        self.handle_input(event)
                
                elif event.type in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION, pygame.MOUSEWHEEL]:
                     self.handle_input(event)
                
                # Joystick Handling (Unified System)
                elif event.type in (pygame.JOYBUTTONDOWN, pygame.JOYBUTTONUP, pygame.JOYAXISMOTION, pygame.JOYHATMOTION):
                    self._handle_controller_event(event)
                    
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
            
        # Cleanup on exit
        self._cleanup()
        pygame.quit()
        sys.exit()
    
    def _cleanup(self):
        """Cleanup resources on exit"""
        
        # Close network
        if hasattr(self, 'network') and self.network:
            try:
                self.network.close()
            except:
                pass

    def trigger_reboot(self):
        # Starts exit sequence
        self.shutting_down = True
        self.shutdown_alpha = 0
            
    def handle_input(self, event):
        self.scene_manager.handle_input(event)

    def play_menu_bgm(self):
        from core.utils import resource_path
        
        # 1. Gather files - check both bundled and local paths
        mm_dir_local = "mainmenu_music"
        mm_dir_bundled = resource_path("mainmenu_music")
        s_dir_local = "songs"
        s_dir_bundled = resource_path("songs")
        
        # Determine which directories exist
        mm_dir = mm_dir_bundled if os.path.exists(mm_dir_bundled) else mm_dir_local
        s_dir = s_dir_bundled if os.path.exists(s_dir_bundled) else s_dir_local
        
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
        from scenes.editor_scene import EditorScene
        if isinstance(self.scene_manager.current_scene, (GameScene, EditorScene)): return

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

    def _handle_controller_event(self, event):
        """Unified controller event handling with proper state management"""
        now = pygame.time.get_ticks()
        
        # Initialize controller state if needed
        if not hasattr(self, 'ctrl_state'):
            self.ctrl_state = {
                'buttons': {},  # button_id -> is_down
                'axes': {},     # axis_id -> last_value
                'hat': (0, 0),  # last hat state
                'last_nav': 0,  # debounce timer for navigation
            }
            print("DEBUG: Controller State Initialized")
        
        # Debug raw events
        # print(f"DEBUG: JoyEvent {event.type}")        
        NAV_DEBOUNCE = 150  # ms between navigation repeats
        AXIS_DEADZONE = 0.5
        
        # === BUTTON EVENTS ===
        if event.type == pygame.JOYBUTTONDOWN:
            btn = event.button
            self.ctrl_state['buttons'][btn] = True
            
            # Menu navigation buttons (universal)
            if btn == 0:  # A / Cross
                self.handle_input(pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_RETURN}))
            elif btn == 1:  # B / Circle
                self.handle_input(pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_ESCAPE}))
            elif btn in (6, 7):  # Start/Select/Options
                self.handle_input(pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_ESCAPE}))
            elif btn == 4:  # LB / L1
                self.handle_input(pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_q}))
            elif btn == 5:  # RB / R1
                self.handle_input(pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_e}))
            
            # Gameplay lane bindings
            joy_binds = self.settings.get("joy_binds")
            keybinds = self.settings.get("keybinds")
            for i, bind in enumerate(joy_binds):
                if isinstance(bind, int) and bind == btn:
                    self.lane_state[i] = True
                    self.handle_input(pygame.event.Event(pygame.KEYDOWN, {'key': keybinds[i]}))
                elif isinstance(bind, dict) and bind.get('type') == 'btn' and bind.get('value') == btn:
                    self.lane_state[i] = True
                    self.handle_input(pygame.event.Event(pygame.KEYDOWN, {'key': keybinds[i]}))
        
        elif event.type == pygame.JOYBUTTONUP:
            btn = event.button
            self.ctrl_state['buttons'][btn] = False
            
            # Gameplay lane releases
            joy_binds = self.settings.get("joy_binds")
            keybinds = self.settings.get("keybinds")
            for i, bind in enumerate(joy_binds):
                if isinstance(bind, int) and bind == btn:
                    self.lane_state[i] = False
                    self.handle_input(pygame.event.Event(pygame.KEYUP, {'key': keybinds[i]}))
                elif isinstance(bind, dict) and bind.get('type') == 'btn' and bind.get('value') == btn:
                    self.lane_state[i] = False
                    self.handle_input(pygame.event.Event(pygame.KEYUP, {'key': keybinds[i]}))
        
        # === D-PAD (HAT) EVENTS ===
        elif event.type == pygame.JOYHATMOTION:
            val = event.value
            old = self.ctrl_state['hat']
            self.ctrl_state['hat'] = val
            
            # Only trigger on change with debounce
            if now - self.ctrl_state['last_nav'] > NAV_DEBOUNCE:
                if val[1] == 1 and old[1] != 1:
                    self.handle_input(pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_UP}))
                    self.ctrl_state['last_nav'] = now
                elif val[1] == -1 and old[1] != -1:
                    self.handle_input(pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_DOWN}))
                    self.ctrl_state['last_nav'] = now
                elif val[0] == -1 and old[0] != -1:
                    self.handle_input(pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_LEFT}))
                    self.ctrl_state['last_nav'] = now
                elif val[0] == 1 and old[0] != 1:
                    self.handle_input(pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_RIGHT}))
                    self.ctrl_state['last_nav'] = now
        
        # === AXIS EVENTS (Sticks & Triggers) ===
        elif event.type == pygame.JOYAXISMOTION:
            axis = event.axis
            val = event.value
            old_val = self.ctrl_state['axes'].get(axis, 0)
            self.ctrl_state['axes'][axis] = val
            
            # Left stick navigation (axes 0, 1)
            if axis in (0, 1):
                if now - self.ctrl_state['last_nav'] > NAV_DEBOUNCE:
                    if abs(val) > 0.6 and abs(old_val) <= 0.6:
                        # Just crossed threshold
                        if axis == 0:  # X axis
                            key = pygame.K_RIGHT if val > 0 else pygame.K_LEFT
                        else:  # Y axis
                            key = pygame.K_DOWN if val > 0 else pygame.K_UP
                        self.handle_input(pygame.event.Event(pygame.KEYDOWN, {'key': key}))
                        self.ctrl_state['last_nav'] = now
            
            # Axis-bound lanes (triggers, etc)
            joy_binds = self.settings.get("joy_binds")
            keybinds = self.settings.get("keybinds")
            for i, bind in enumerate(joy_binds):
                if isinstance(bind, dict) and bind.get('type') == 'axis' and bind.get('axis') == axis:
                    direction = bind.get('dir', 1)
                    is_active = (direction > 0 and val > AXIS_DEADZONE) or (direction < 0 and val < -AXIS_DEADZONE)
                    was_active = (direction > 0 and old_val > AXIS_DEADZONE) or (direction < 0 and old_val < -AXIS_DEADZONE)
                    
                    if is_active and not was_active:
                        self.lane_state[i] = True
                        self.handle_input(pygame.event.Event(pygame.KEYDOWN, {'key': keybinds[i]}))
                    elif not is_active and was_active:
                        self.lane_state[i] = False
                        self.handle_input(pygame.event.Event(pygame.KEYUP, {'key': keybinds[i]}))

if __name__ == "__main__":
    create_linux_desktop_entry()
    game = Game()
    game.run()
