import pygame

import os

class Scene:
    def __init__(self, game):
        self.game = game
        self.manager = game.scene_manager
        self.next_scene = None # If set, manager switches to this
        
        # Common SFX
        self.sfx_blip = None
        self.sfx_accept = None
        if os.path.exists("sfx/sfx_blip.wav"):
             self.sfx_blip = pygame.mixer.Sound("sfx/sfx_blip.wav")
             self.sfx_blip.set_volume(0.4)
        if os.path.exists("sfx/sfx_accept.wav"):
             self.sfx_accept = pygame.mixer.Sound("sfx/sfx_accept.wav")
             self.sfx_accept.set_volume(0.4)
        if os.path.exists("sfx/sfx_back.wav"):
             self.sfx_back = pygame.mixer.Sound("sfx/sfx_back.wav")
             self.sfx_back.set_volume(0.4)
        if os.path.exists("sfx/sfx_shutdown.wav"):
             self.sfx_shutdown = pygame.mixer.Sound("sfx/sfx_shutdown.wav")
             self.sfx_shutdown.set_volume(0.6)
             
        # New SFX (shared)
        self.sfx_type = pygame.mixer.Sound("sfx/sfx_type.wav") if os.path.exists("sfx/sfx_type.wav") else None
        if self.sfx_type: self.sfx_type.set_volume(0.3)
        self.sfx_hdd = pygame.mixer.Sound("sfx/sfx_hdd.wav") if os.path.exists("sfx/sfx_hdd.wav") else None
        if self.sfx_hdd: self.sfx_hdd.set_volume(0.3)
        self.sfx_success = pygame.mixer.Sound("sfx/sfx_success.wav") if os.path.exists("sfx/sfx_success.wav") else None
        if self.sfx_success: self.sfx_success.set_volume(0.5)

    def play_sfx(self, name):
        if name == "blip" and self.sfx_blip: self.sfx_blip.play()
        elif name == "accept" and self.sfx_accept: self.sfx_accept.play()
        elif name == "back" and hasattr(self, 'sfx_back') and self.sfx_back: self.sfx_back.play()
        elif name == "shutdown" and hasattr(self, 'sfx_shutdown') and self.sfx_shutdown: self.sfx_shutdown.play()
        elif name == "type" and hasattr(self, 'sfx_type') and self.sfx_type: self.sfx_type.play()
        elif name == "hdd" and hasattr(self, 'sfx_hdd') and self.sfx_hdd: self.sfx_hdd.play()
        elif name == "success" and hasattr(self, 'sfx_success') and self.sfx_success: self.sfx_success.play()

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
        self.scene_stack = [] # Stack for overlays (Admin, etc)
        
        # Transition State
        self.overlay = pygame.Surface((1024, 768)) 
        self.overlay.fill((0,0,0))
        self.transition_alpha = 0
        self.transition_state = "IDLE" # IDLE, FADE_OUT, FADE_IN
        self.transitioning = False
        
        # Matrix Effects (100 drops for full visual density)
        self.matrix_drops = []
        import random
        for i in range(100): # Original count for full effect
             self.matrix_drops.append({
                 'x': random.randint(0, 1024),
                 'y': random.randint(-800, 0),
                 'speed': random.randint(10, 30), # Original speed
                 'char': chr(random.randint(33, 126)),
                 'len': random.randint(8, 18) # Original trail length
             })
        
        # Pre-render character cache to FIX LAG
        self._char_cache = {}
        self._fade_surface = pygame.Surface((1024, 768)) # Cached surface for performance
        self._render_matrix_cache()

    def _render_matrix_cache(self):
        """Pre-render all matrix chars in varied transparencies to avoid font.render lag"""
        theme = self.game.renderer.get_theme()
        prim = theme["primary"]
        font = self.game.renderer.font
        
        # We cache: (char, color_index) -> Surface
        # color_index 0 = Head (White), 1..N = Fade trail
        for c_code in range(33, 127):
            char = chr(c_code)
            # Head
            self._char_cache[(char, 0)] = font.render(char, False, (255, 255, 255)).convert_alpha()
            
            # Trail (Pre-calculate 10 fade steps)
            for i in range(1, 11):
                factor = max(0.1, 1.0 - (i / 10))
                col = (int(prim[0] * factor), int(prim[1] * factor), int(prim[2] * factor))
                self._char_cache[(char, i)] = font.render(char, False, col).convert_alpha()

    def switch_to(self, scene_class, params=None):
        # Clear stack on full switch
        self.scene_stack = []
        
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

    def push_scene(self, scene_class, params=None):
        """Push a new scene on top of the current one (Pause current)"""
        if self.current_scene:
            self.scene_stack.append(self.current_scene)
        
        # No transition for push (instant overlay)
        self.current_scene = scene_class(self.game)
        self.current_scene.on_enter(params)
        
    def pop_scene(self):
        """Return to the previous scene in the stack"""
        if self.current_scene:
            self.current_scene.on_exit()
            
        if self.scene_stack:
            self.current_scene = self.scene_stack.pop()
            # self.current_scene.on_resume()? If we had it.
        else:
            # Fallback if empty
            from scenes.menu_scenes import TitleScene
            self.switch_to(TitleScene)

    def handle_input(self, event):
        if self.current_scene and not self.transitioning:
            self.current_scene.handle_input(event)

    def update(self):
        if self.transitioning:
            # Update drops
            import random
            for d in self.matrix_drops:
                d['y'] += d['speed'] * 2 # Original speed
                if d['y'] > 768:
                    d['y'] = random.randint(-100, 0)
                    d['x'] = random.randint(0, 1024)

            # State Machine
            if self.transition_state == "FADE_OUT":
                self.transition_alpha += 10 # Original fade rate
                if self.transition_alpha >= 255:
                    self.transition_alpha = 255
                    # Swap
                    if self.current_scene: self.current_scene.on_exit()
                    self.current_scene = self.next_scene_class(self.game)
                    self.current_scene.on_enter(self.next_params)
                    # Switch to Fade In
                    self.transition_state = "FADE_IN"

            elif self.transition_state == "FADE_IN":
                self.transition_alpha -= 10 # Original fade rate
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
            # OPTIMIZED: Reuse cached fade surface
            self._fade_surface.fill(self.game.renderer.get_theme()["bg"])
            self._fade_surface.set_alpha(self.transition_alpha)
            surface.blit(self._fade_surface, (0, 0))
            
            # Skip matrix if alpha too low (nothing visible anyway)
            if self.transition_alpha < 20:
                return
            
            # Draw matrix drops (OPTIMIZED: Skip off-screen early)
            for d in self.matrix_drops:
                base_y = d['y']
                # Early skip if entire trail is off-screen
                if base_y < -(d['len'] * 15) or base_y > 768 + 50:
                    continue
                    
                for i in range(d['len']):
                    y = base_y - i * 15
                    if y < -20 or y > 780: continue
                    
                    # Use Character Cache
                    cache_idx = 0 if i == 0 else min(10, i)
                    cache_key = (d['char'], cache_idx)
                    
                    if cache_key in self._char_cache:
                        surface.blit(self._char_cache[cache_key], (d['x'], int(y)))
