import pygame
from core.scene_manager import Scene
from core.config import *

class LeaderboardScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.rankings = []
        self.scroll_y = 0
        self.target_scroll_y = 0
        
    def on_enter(self, params=None):
        # Refresh rankings
        self.rankings = self.game.leaderboard_manager.get_rankings()
        self.target_scroll_y = 0
        self.scroll_y = 0
        
    def draw(self, surface):
        r = self.game.renderer
        theme = r.get_theme()
        
        # 1. Animated Grid Background
        t = pygame.time.get_ticks()
        surface.fill(theme["bg"])
        grid_offset_y = (t * 0.1) % 40
        grid_col = theme["grid"]
        
        for y in range(0, SCREEN_HEIGHT + 40, 40):
            line_y = y + grid_offset_y - 40
            pygame.draw.line(surface, grid_col, (0, line_y), (SCREEN_WIDTH, line_y))
        for x in range(0, SCREEN_WIDTH, 40):
            pygame.draw.line(surface, grid_col, (x, 0), (x, SCREEN_HEIGHT))
            
        # Draw Main Panel (Standardized dimensions)
        panel_w, panel_h = 900, 620
        panel_x = (SCREEN_WIDTH - panel_w) // 2
        panel_y = (SCREEN_HEIGHT - panel_h) // 2
        
        r.draw_panel(surface, panel_x, panel_y, panel_w, panel_h, "GLOBAL LEADERBOARD")
        
        # Sub-header (Aligned to panel)
        r.draw_text(surface, "TOP PLAYERS BY TOTAL SCORE", panel_x + 30, panel_y + 40, theme["secondary"])
        r.draw_text(surface, "[ESC] BACK", panel_x + panel_w - 120, panel_y + 40, theme["text"])
        
        # Rankings List Container
        start_y = panel_y + 80
        item_h = 45
        
        # Smooth Scroll
        self.scroll_y += (self.target_scroll_y - self.scroll_y) * 0.2
        
        # Column positions (Standardized)
        col_rank = panel_x + 40
        col_name = panel_x + 120
        col_stats = panel_x + 450
        
        # Draw items
        for i, entry in enumerate(self.rankings):
            y = start_y + i * item_h - self.scroll_y
            
            # Bounds check
            if y < panel_y + 75 or y > panel_y + panel_h - 45:
                continue
                
            rank = i + 1
            name = entry['name']
            score = entry['score']
            lvl = entry['level']
            acc = entry['accuracy']
            
            # Highlight User
            is_me = (name == self.game.settings.get("name"))
            
            col = theme["text"]
            if rank == 1: col = (255, 215, 0) # Gold
            elif rank == 2: col = (192, 192, 192) # Silver
            elif rank == 3: col = (205, 127, 50) # Bronze
            elif is_me: col = theme["primary"] # User
            
            # Draw Rank (Fixed width)
            r.draw_text(surface, f"#{rank:02d}", col_rank, y, col, r.big_font)
            
            # Draw Name (Truncate if too long)
            disp_name = name if len(name) <= 16 else name[:14] + ".."
            r.draw_text(surface, disp_name, col_name, y, col, r.big_font)
            
            # Draw Stats (Right aligned group)
            info = f"LVL {lvl}  |  {score:,} PTS  |  {acc:.1f}%"
            r.draw_text(surface, info, col_stats, y + 3, theme["secondary"])
            
            # Divider
            pygame.draw.line(surface, theme["grid"], (panel_x + 30, y + 38), (panel_x + panel_w - 30, y + 38))

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.play_sfx("back")
                # Return to previous scene? Usually Main Menu or Profile
                # Since we don't track history strictly, safer to go Title
                from scenes.menu_scenes import TitleScene
                self.game.scene_manager.switch_to(TitleScene)
                
            elif event.key == pygame.K_DOWN:
                self.target_scroll_y = min(self.target_scroll_y + 100, max(0, len(self.rankings) * 50 - 400))
            elif event.key == pygame.K_UP:
                self.target_scroll_y = max(0, self.target_scroll_y - 100)
            elif event.key == pygame.K_PAGEUP:
                self.target_scroll_y = max(0, self.target_scroll_y - 400)
            elif event.key == pygame.K_PAGEDOWN:
                self.target_scroll_y = min(self.target_scroll_y + 400, max(0, len(self.rankings) * 50 - 400))
