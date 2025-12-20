import pygame

class AnimationUtils:
    @staticmethod
    def ease_out_quad(t):
        return t * (2 - t)

    @staticmethod
    def slide_in(surface, target_surf, direction='left', duration=0.5, progress=0.0):
        """
        Draws target_surf sliding into surface.
        Progress 0.0 -> 1.0
        """
        w, h = surface.get_size()
        offset = int(w * (1.0 - AnimationUtils.ease_out_quad(progress)))
        
        x = -offset if direction == 'left' else offset
        surface.blit(target_surf, (x, 0))

class Transition:
    def __init__(self, duration=30):
        self.duration = duration
        self.timer = 0
        self.active = False
        
    def start(self):
        self.active = True
        self.timer = 0
        
    def update(self):
        if self.active:
            self.timer += 1
            if self.timer >= self.duration:
                self.active = False
                return True
        return False
        
    def get_progress(self):
        return min(1.0, self.timer / self.duration)
