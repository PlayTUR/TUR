import pygame
import time

class AudioManager:
    def __init__(self, game=None):
        # frequency higher for lower latency potential
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        self.game = game
        self.current_music_path = None
        self.start_time = 0
        self.paused_time = 0
        self.is_playing = False
        self.offset = 0.0 # Seconds

    def update_volumes(self):
        """Standardizes volume across music and SFX using master multiplier"""
        if not self.game: return
        s = self.game.settings
        master = s.get("volume")
        music = s.get("music_volume")
        
        # Apply to music
        pygame.mixer.music.set_volume(master * music)
        
        # SFX volume is handled per-sound, but we can store it here for reference
        self.sfx_vol = master * s.get("sfx_volume")

    def set_offset(self, ms):
        self.offset = ms / 1000.0

    def pause(self):
        pygame.mixer.music.pause()
        self.paused = True
        
    def unpause(self):
        pygame.mixer.music.unpause()
        self.paused = False

    def load_song(self, path):
        from core.utils import find_resource
        res_path = find_resource(path, hint_dirs=["songs", "mainmenu_music"])
        if not res_path:
            raise FileNotFoundError(f"Audio file not found: {path} (Searched everywhere)")
            
        self.current_music_path = res_path
        pygame.mixer.music.load(res_path)

    def play(self):
        pygame.mixer.music.play()
        self.update_volumes() # Ensure volumes are set on play
        self.start_time = time.time()
        self.is_playing = True

    def stop(self):
        pygame.mixer.music.stop()
        self.is_playing = False

    def get_position(self):
        """Returns current song position in seconds."""
        if not self.is_playing:
            return 0
        return time.time() - self.start_time + self.offset

    def set_volume(self, volume): # Legacy
        pygame.mixer.music.set_volume(volume)

    def set_end_event(self, event_id):
        pygame.mixer.music.set_endevent(event_id)
