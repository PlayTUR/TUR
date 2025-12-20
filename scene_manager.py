import pygame

class Scene:
    def __init__(self, game):
        self.game = game
        self.manager = game
        self.next_scene = None # If set, manager switches to this

    def handle_input(self, event):
        pass

    def update(self):
        pass

    def draw(self, surface):
        pass

    def on_enter(self, params=None):
        pass

    def on_exit(self):
        pass

class SceneManager:
    def __init__(self, game):
        self.game = game 
        self.current_scene = None
        
        # Transition State
        self.overlay = pygame.Surface((1024, 768)) # Hardcoded size matching config
        self.overlay.fill((0,0,0))
        self.transition_alpha = 0
        self.transitioning = False
        self.next_scene_class = None
        self.next_params = None

    def switch_to(self, scene_class, params=None):
        # Start Fade Out
        self.transitioning = True
        self.next_scene_class = scene_class
        self.next_params = params
        self.transition_alpha = 0

    def handle_input(self, event):
        if self.current_scene and not self.transitioning:
            self.current_scene.handle_input(event)

    def update(self):
        if self.transitioning:
            self.transition_alpha += 10
            if self.transition_alpha >= 255:
                # Swap
                self.transition_alpha = 255
                if self.current_scene: self.current_scene.on_exit()
                self.current_scene = self.next_scene_class(self.game)
                self.current_scene.on_enter(self.next_params)
                self.transitioning = False
                # Do we fade in? For now just snap or fade logic needs state machine.
                # Simple Fade Out then Snap in.
        else:
             if self.transition_alpha > 0:
                 self.transition_alpha -= 10
             
        if self.current_scene:
            self.current_scene.update()

    def draw(self, surface):
        if self.current_scene:
            self.current_scene.draw(surface)
            
        if self.transition_alpha > 0:
            self.overlay.set_alpha(self.transition_alpha)
            surface.blit(self.overlay, (0,0))
