import pygame
import time

class AudioManager:
    def __init__(self):
        # frequency higher for lower latency potential
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        self.current_music_path = None
        self.start_time = 0
        self.paused_time = 0
        self.is_playing = False
        self.offset = 0.0 # Seconds

    def set_offset(self, ms):
        self.offset = ms / 1000.0

    def pause(self):
        pygame.mixer.music.pause()
        self.paused = True
        
    def unpause(self):
        pygame.mixer.music.unpause()
        self.paused = False

    def load_song(self, path):
        self.current_music_path = path
        pygame.mixer.music.load(path)

    def play(self):
        pygame.mixer.music.play()
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

    def set_volume(self, volume):
        pygame.mixer.music.set_volume(volume)

    def set_end_event(self, event_id):
        pygame.mixer.music.set_endevent(event_id)

