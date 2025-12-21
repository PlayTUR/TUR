import pygame
from core.scene_manager import Scene
from core.config import *

class ResultScene(Scene):
    def on_enter(self, params):
        self.params = params
        self.rank = self.calculate_rank()
        self.next_scene_class = params.get('next_scene_class')
        self.next_scene_params = params.get('next_scene_params')
        
    # (calculate_rank and draw remain same)

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.play_sfx("accept")
                if self.next_scene_class:
                    self.game.scene_manager.switch_to(self.next_scene_class, self.next_scene_params)
                else:
                    from scenes.menu_scenes import SongSelectScene
                    self.game.scene_manager.switch_to(SongSelectScene)
