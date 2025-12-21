import pygame
from core.scene_manager import Scene
from core.config import *

class LobbyScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.state = "MENU" # MENU, HOSTING, JOINING, LOBBY
        self.ip_buffer = "127.0.0.1"
        self.password_buffer = ""
        self.room_name_buffer = "ROOM1"
        self.input_focus = 0 # 0=IP, 1=Pass
        self.status = ""

    def draw(self, surface):
        self.game.renderer.draw_text(surface, "NETWORK OPERATIONS", 50, 50, TERM_GREEN, self.game.renderer.big_font)
        
        if self.state == "MENU":
            self.game.renderer.draw_text(surface, "[1] HOST SERVER", 100, 200, TERM_WHITE)
            self.game.renderer.draw_text(surface, "[2] JOIN FREQUENCY", 100, 250, TERM_WHITE)
            self.game.renderer.draw_text(surface, "[ESC] ABORT", 100, 300, (100, 100, 100))
            
        elif self.state == "JOINING":
            self.game.renderer.draw_text(surface, "TARGET IP:", 100, 200, TERM_WHITE)
            col = TERM_AMBER if self.input_focus == 0 else TERM_WHITE
            self.game.renderer.draw_text(surface, f"> {self.ip_buffer}", 100, 230, col)
            
            self.game.renderer.draw_text(surface, "PASSWORD:", 100, 280, TERM_WHITE)
            col = TERM_AMBER if self.input_focus == 1 else TERM_WHITE
            self.game.renderer.draw_text(surface, f"> {self.password_buffer}", 100, 310, col)
            
            self.game.renderer.draw_text(surface, "[TAB] SWITCH | [ENTER] CONNECT", 100, 400, (100, 100, 100))
            self.game.renderer.draw_text(surface, f"STATUS: {self.status}", 100, 500, TERM_RED)

        elif self.state == "HOSTING":
             self.game.renderer.draw_text(surface, "HOSTING SERVER...", 100, 200, TERM_AMBER)
             self.game.renderer.draw_text(surface, "WAITING FOR CLIENTS...", 100, 230, TERM_WHITE)
             if self.game.network.connected:
                 self.game.renderer.draw_text(surface, f"CLIENT CONNECTED: {self.game.network.opponent_name}", 100, 300, TERM_GREEN)
                 self.game.renderer.draw_text(surface, "[ENTER] START GAME", 100, 400, TERM_WHITE)
             
             self.game.renderer.draw_text(surface, "[Q] DISCONNECT / CANCEL", 100, 600, (100, 100, 100))

        elif self.state == "CLIENT_LOBBY":
             self.game.renderer.draw_text(surface, f"CONNECTED TO HOST", 100, 200, TERM_GREEN)
             self.game.renderer.draw_text(surface, "WAITING FOR HOST TO START...", 100, 230, TERM_WHITE)
             
             if not self.game.network.connected:
                  self.game.renderer.draw_text(surface, "STATUS: DISCONNECTED", 100, 300, TERM_RED)
             
             self.game.renderer.draw_text(surface, "[Q] DISCONNECT", 100, 600, (100, 100, 100))

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if self.state == "MENU":
                if event.key == pygame.K_1:
                    self.state = "HOSTING"
                    # Default port, no pass for now in menu, could add pass input
                    self.game.network.host_game(password=self.password_buffer)
                elif event.key == pygame.K_2:
                    self.state = "JOINING"
                elif event.key == pygame.K_ESCAPE:
                    from scenes.menu_scenes import SongSelectScene
                    self.game.scene_manager.switch_to(SongSelectScene)

            elif self.state == "JOINING":
                if event.key == pygame.K_TAB:
                    self.input_focus = (self.input_focus + 1) % 2
                elif event.key == pygame.K_RETURN:
                    self.status = "CONNECTING..."
                    self.game.network.join_game(self.ip_buffer, self.password_buffer)
                    self.state = "CLIENT_LOBBY"
                elif event.key == pygame.K_BACKSPACE:
                    if self.input_focus == 0: self.ip_buffer = self.ip_buffer[:-1]
                    else: self.password_buffer = self.password_buffer[:-1]
                elif event.unicode.isprintable():
                    if self.input_focus == 0: self.ip_buffer += event.unicode
                    else: self.password_buffer += event.unicode
            
            elif self.state == "HOSTING": 
                if event.key == pygame.K_RETURN and self.game.network.is_host:
                     self.play_sfx("accept")
                     from scenes.menu_scenes import SongSelectScene
                     self.game.scene_manager.switch_to(SongSelectScene)
                elif event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                     self.play_sfx("back")
                     self.game.network.close()
                     self.state = "MENU"

            elif self.state == "CLIENT_LOBBY":
                if event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                     self.play_sfx("back")
                     self.game.network.close()
                     self.state = "MENU"
