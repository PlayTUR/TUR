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
        # Linux/Tiling WM Stability: Set WM Class for rule matching rules
        os.environ['SDL_VIDEO_X11_WMCLASS'] = "terminalbeat"
        
        pygame.init()
        pygame.mixer.init()
        
        # Window setup
        # User requested "Force Floating" on TWMs. Making the window fixed-size (non-resizable)
        # is the standard way to signal TWMs to treat it as a dialog/float.
        # Windows/Mac get full Resizable support.
        self.flags = pygame.RESIZABLE
        if sys.platform.startswith("linux"):
            self.flags = 0 # Fixed size for Linux stability
            
        self.screen = pygame.display.set_mode((1024, 768), self.flags)
        pygame.display.set_caption("Terminal Beat [PYGAME]")
        
        # Virtual Resolution
        self.virtual_w = 1024
        self.virtual_h = 768
        self.virtual_surface = pygame.Surface((self.virtual_w, self.virtual_h))

        # Modules
        # Modules
        self.renderer = PygameRenderer(self.virtual_w, self.virtual_h)
        self.settings = SettingsManager()
        self.audio = AudioManager()
        self.score_manager = ScoreManager()
        self.generator = BeatmapGenerator()
        self.network = NetworkManager()
        self.scene_manager = SceneManager(self)
        self.audio = AudioManager()
        self.score_manager = ScoreManager()
        self.generator = BeatmapGenerator()
        self.network = NetworkManager()
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
                # --- JOY BUTTONS ---
                elif event.type == pygame.JOYBUTTONDOWN or event.type == pygame.JOYBUTTONUP:
                    is_down = (event.type == pygame.JOYBUTTONDOWN)
                    ev_type = pygame.KEYDOWN if is_down else pygame.KEYUP
                    btn = event.button
                    keys = self.settings.get("keybinds") 
                    sim_key = None

                    # Menu: A=Enter, B=Esc, Start=Enter
                    if is_down:
                        if btn == 0: sim_key = pygame.K_RETURN
                        elif btn == 1: sim_key = pygame.K_ESCAPE
                        elif btn == 7 or btn == 9: sim_key = pygame.K_RETURN # Start (9 on Xbox, 7 on PS4 sometimes)

                    # Gameplay Mappings
                    # User Request: LB, RB, LT, RT = 4 Lanes.
                    # Lane 0: LT (Axis Handle separately)
                    # Lane 1: LB (Btn 4)
                    # Lane 2: RB (Btn 5)
                    # Lane 3: RT (Axis Handle separately)
                    
                    if btn == 4: # LB -> Lane 1
                        sim_key = keys[1]
                    elif btn == 5: # RB -> Lane 2
                        sim_key = keys[2]
                        
                    # Fallback Face Buttons for convenience?
                    elif btn == 2: # X/Square -> Lane 0
                        sim_key = keys[0]
                    elif btn == 3: # Y/Triangle -> Lane 3
                        sim_key = keys[3]

                    if sim_key:
                        ev = pygame.event.Event(ev_type, {'key': sim_key})
                        self.handle_input(ev)

                # --- JOY AXES (Triggers) ---
                elif event.type == pygame.JOYAXISMOTION:
                    # Axis 2 = LT, Axis 5 = RT (Common)
                    # We need state tracking to avoid spamming KEYDOWN
                    # HACK: Using a static dict on self to track trigger state
                    if not hasattr(self, 'trigger_state'):
                        self.trigger_state = {2: False, 5: False}
                    
                    keys = self.settings.get("keybinds")
                    axis = event.axis
                    val = event.value
                    
                    # Threshold
                    triggered = val > 0.5
                    
                    if axis in [2, 5]: # LT or RT
                        if triggered and not self.trigger_state.get(axis, False):
                            # DOWN
                            self.trigger_state[axis] = True
                            k = keys[0] if axis == 2 else keys[3] # LT=Lane0, RT=Lane3
                            self.handle_input(pygame.event.Event(pygame.KEYDOWN, {'key': k}))
                            
                        elif not triggered and self.trigger_state.get(axis, False):
                            # UP
                            self.trigger_state[axis] = False
                            k = keys[0] if axis == 2 else keys[3]
                            self.handle_input(pygame.event.Event(pygame.KEYUP, {'key': k}))

                # --- JOY HAT (D-Pad) ---
                elif event.type == pygame.JOYHATMOTION:
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
            
            pygame.display.flip()
            
        pygame.quit()
        sys.exit()

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
