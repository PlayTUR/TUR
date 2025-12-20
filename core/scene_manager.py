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
        self.overlay = pygame.Surface((1024, 768)) 
        self.overlay.fill((0,0,0))
        self.transition_alpha = 0
        self.transition_state = "IDLE" # IDLE, FADE_OUT, FADE_IN
        
        # Matrix Effects
        self.matrix_drops = []
        import random
        for i in range(200): # 200 drops
             self.matrix_drops.append({
                 'x': random.randint(0, 1024),
                 'y': random.randint(-800, 0),
                 'speed': random.randint(10, 30),
                 'char': chr(random.randint(33, 126)),
                 'len': random.randint(5, 15)
             })

    def switch_to(self, scene_class, params=None):
        if self.current_scene is None:
            self.current_scene = scene_class(self.game)
            self.current_scene.on_enter(params)
            self.transitioning = False
            return

        # Start Transition
        self.transitioning = True
        self.transition_state = "FADE_OUT"
        self.next_scene_class = scene_class
        self.next_params = params
        self.transition_alpha = 0 
        # Reset drops
        import random
        for d in self.matrix_drops:
            d['y'] = random.randint(-800, -100)

    def handle_input(self, event):
        if self.current_scene and not self.transitioning:
            self.current_scene.handle_input(event)

    def update(self):
        if self.transitioning:
            # Update drops (Visuals always run during transition)
            import random
            for d in self.matrix_drops:
                d['y'] += d['speed'] * 2 # Faster drops for intensity
                if d['y'] > 768:
                    d['y'] = random.randint(-100, 0)
                    d['x'] = random.randint(0, 1024)

            # State Machine
            if self.transition_state == "FADE_OUT":
                self.transition_alpha += 10
                if self.transition_alpha >= 255:
                    self.transition_alpha = 255
                    # Swap
                    if self.current_scene: self.current_scene.on_exit()
                    self.current_scene = self.next_scene_class(self.game)
                    self.current_scene.on_enter(self.next_params)
                    # Switch to Fade In
                    self.transition_state = "FADE_IN"
                    # Reset drops for the fade in part? 
                    # Keep them falling continuously for seamlessness

            elif self.transition_state == "FADE_IN":
                self.transition_alpha -= 10
                if self.transition_alpha <= 0:
                    self.transition_alpha = 0
                    self.transitioning = False
                    self.transition_state = "IDLE"

        if self.current_scene:
            self.current_scene.update()

    def draw(self, surface):
        if self.current_scene:
            self.current_scene.draw(surface)
            
        if self.transitioning:
            # Draw Matrix Rain Overlay
            fade = pygame.Surface((1024, 768))
            fade.set_alpha(self.transition_alpha)
            fade.fill(self.game.renderer.get_theme()["bg"]) # Use theme BG
            surface.blit(fade, (0, 0))
            
            drop_alpha_mult = self.transition_alpha / 255.0
            
            font = self.game.renderer.font
            
            # Theme colors
            theme = self.game.renderer.get_theme()
            prim = theme["primary"] 
            
            for d in self.matrix_drops:
                # Draw trail
                for i in range(d['len']):
                    y = d['y'] - i * 15
                    if y < 0 or y > 768: continue
                    
                    # Gradient based on primary color
                    if i == 0: 
                        # Head is bright white/tinted
                        base_col = (255, 255, 255)
                    else: 
                        # Trail fades to primary
                        factor = max(0, 1.0 - (i / d['len'])) # 1.0 to 0.0
                        base_col = (
                            int(prim[0] * factor), 
                            int(prim[1] * factor), 
                            int(prim[2] * factor)
                        )
                    
                    if max(base_col) < 20: continue
                    
                    if drop_alpha_mult < 0.1: continue
                    
                    txt = font.render(d['char'], False, base_col)
                    surface.blit(txt, (d['x'], int(y)))
