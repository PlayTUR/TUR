import pygame
import os
import time
from core.renderer import PygameRenderer
from core.scene_manager import SceneManager
from scenes.menu_scenes import TitleScene
from core.settings_manager import SettingsManager
from core.audio_manager import AudioManager
from core.beatmap_generator import BeatmapGenerator
from core.network_manager import NetworkManager
from core.score_manager import ScoreManager
from core.config import *
import sys

# Main Pygame Entry Point
class Game:
    def __init__(self):
        # Linux/Tiling WM Stability + Hyprland/NVIDIA Fixes (skip on Windows)
        if sys.platform != "win32":
            os.environ['SDL_VIDEO_X16_WMCLASS'] = "tur"
            
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
        self.audio = AudioManager()
        self.score_manager = ScoreManager()
        self.generator = BeatmapGenerator()
        self.network = NetworkManager()
        self.scene_manager = SceneManager(self)
        
        # Input: Controller
        pygame.joystick.init()
        self.joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
        for j in self.joysticks: j.init()
        print(f"DEBUG: Controllers Found: {len(self.joysticks)}")
        
        # Dependency Injection
        self.renderer.game = self
        
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
                    self.running = False
                elif event.type == pygame.VIDEORESIZE:
                    if self.flags & pygame.RESIZABLE:
                        self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F11:
                         pygame.display.toggle_fullscreen()
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
        if not os.path.exists(mm_dir): os.makedirs(mm_dir)
        
        mm_files = []
        if os.path.exists(mm_dir):
            mm_files = [os.path.join(mm_dir, f) for f in os.listdir(mm_dir) if f.lower().endswith(('.mp3', '.wav', '.ogg'))]
            mm_files.sort()
            
        song_files = []
        s_dir = "songs"
        if os.path.exists(s_dir):
            song_files = [os.path.join(s_dir, f) for f in os.listdir(s_dir) if f.lower().endswith(('.mp3', '.wav', '.ogg'))]
            song_files.sort()
            
        self.menu_playlist = mm_files + song_files
        self.playlist_index = 0
        
        if self.menu_playlist:
            self.play_playlist_track()
            
    def play_playlist_track(self):
        if not self.menu_playlist: return
        path = self.menu_playlist[self.playlist_index]
        self.audio.load_song(path)
        pygame.mixer.music.play(0) 
        self.playlist_index = (self.playlist_index + 1) % len(self.menu_playlist)

    def update_music(self):
        from scenes.game_scene import GameScene
        if isinstance(self.scene_manager.current_scene, GameScene): return

        if not pygame.mixer.music.get_busy():
            if self.menu_playlist:
                self.play_playlist_track()

if __name__ == "__main__":
    game = Game()
    game.run()
