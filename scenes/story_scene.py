import pygame
from core.scene_manager import Scene
from core.config import *
from core.story_generator import StoryGenerator
from scenes.game_scene import GameScene

class StoryScene(Scene):
    def on_enter(self, params=None):
        if params is None: 
            params = {}
            
        self.campaign = params.get('campaign')
        if not self.campaign:
            gen = StoryGenerator()
            self.campaign = gen.generate_campaign()
            
        self.current_idx = params.get('index', 0)
        self.chapters = self.campaign['chapters']
        
        if self.current_idx >= len(self.chapters):
            self.state = "COMPLETE"
        else:
            self.state = "BRIEFING" 
            self.chapter = self.chapters[self.current_idx]

    def update(self):
        pass

    def draw(self, surface):
        theme = self.game.renderer.get_theme()
        
        # BG
        surface.fill(theme["bg"])
        
        if self.state == "COMPLETE":
            self.game.renderer.draw_text(surface, "CAMPAIGN COMPLETE", 300, 300, theme["primary"], self.game.renderer.big_font)
            self.game.renderer.draw_text(surface, "THE SYSTEM IS SECURE.", 350, 400, theme["text"])
            self.game.renderer.draw_text(surface, "[ESC] RETURN TO MENU", 350, 500, theme["secondary"])
            return

        # Briefing View
        self.game.renderer.draw_text(surface, f"CAMPAIGN: {self.campaign['title']}", 50, 50, theme["primary"])
        self.game.renderer.draw_text(surface, f"CHAPTER {self.current_idx + 1} / {len(self.chapters)}", 50, 100, theme["secondary"])
        
        # Details Box
        box_x, box_y = 50, 150
        box_w, box_h = 900, 400
        pygame.draw.rect(surface, theme["grid"], (box_x, box_y, box_w, box_h), 2)
        pygame.draw.rect(surface, theme["grid"], (box_x, box_y-30, box_w, 30))
        self.game.renderer.draw_text(surface, "MISSION_BRIEFING", box_x+10, box_y-25, theme["text"])
        
        y = box_y + 40
        x = box_x + 40
        self.game.renderer.draw_text(surface, f"MISSION: {self.chapter['title']}", x, y, theme["text"]); y+=40
        self.game.renderer.draw_text(surface, f"TARGET: {self.chapter['song']}", x, y, theme["text"]); y+=40
        c_diff = theme["error"] if self.chapter['difficulty'] in ["HARD", "EXTREME"] else theme["primary"]
        self.game.renderer.draw_text(surface, f"DIFFICULTY: {self.chapter['difficulty']}", x, y, c_diff); y+=40
        
        y += 40
        self.game.renderer.draw_text(surface, "INTEL:", x, y, theme["secondary"]); y+=30
        
        # Word wrap text approx
        txt = self.chapter['text']
        # Simple split for now
        lines = [txt[i:i+60] for i in range(0, len(txt), 60)]
        for line in lines:
            self.game.renderer.draw_text(surface, f"> {line}", x, y, (200, 255, 200)); y+=30
            
        # ASCII Art (Campaign specific or Generic?)
        art = self.chapter.get('art', [])
        if art:
            art_x = 600
            art_y = 200
            for i, line in enumerate(art):
                self.game.renderer.draw_text(surface, line, art_x, art_y + i*15, theme["primary"], font=self.game.renderer.font)
        
        self.game.renderer.draw_text(surface, "[ENTER] COMMENCE | [ESC] ABORT", 50, 600, theme["text"])

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                from scenes.menu_scenes import TitleScene
                self.game.scene_manager.switch_to(TitleScene)
                
            elif event.key == pygame.K_RETURN:
                if self.state == "BRIEFING":
                    # Launch Game
                    # Note: We need to hook into the result. 
                    # For now, let's assume if they finish the song, they pass.
                    # Ideally GameScene returns simple 'finished' state.
                    # We'll pass a special 'next_scene' param? No, GameScene goes to ResultScene.
                    # ResultScene needs to know to come BACK here.
                    
                    next_params = {
                        'campaign': self.campaign,
                        'index': self.current_idx + 1
                    }
                    
                    params = {
                        'song': self.chapter['song'],
                        'difficulty': self.chapter['difficulty'],
                        'mode': 'story',
                        'next_scene_class': StoryScene, # ResultScene will look for this
                        'next_scene_params': next_params
                    }
                    
                    self.game.scene_manager.switch_to(GameScene, params)
