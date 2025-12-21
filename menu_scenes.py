import pygame
from core.scene_manager import Scene
from core.config import *
import os

class TitleScene(Scene):
    def __init__(self, game):
        super().__init__(game)

    def draw(self, surface):
        if True: # Always GUI mode now
            import math
            time = pygame.time.get_ticks() / 500.0
            # Snappy Kick Drum Pulse: sin^20 makes it spiked
            pulse = abs(math.sin(time * 5)) ** 20 
            scale = 1.0 + 0.1 * pulse
            
            # We access the big_font from renderer directly (renderer.big_font)
            text_surf = self.game.renderer.big_font.render("TERMINAL BEAT V8.0", True, TERM_GREEN)
            w, h = text_surf.get_size()
            scaled_w = int(w * scale)
            scaled_h = int(h * scale)
            
            scaled_surf = pygame.transform.scale(text_surf, (scaled_w, scaled_h))
            
            rect = scaled_surf.get_rect(center=(SCREEN_WIDTH//2, 150))
            surface.blit(scaled_surf, rect)
        
        # Flashing text
        alpha = (pygame.time.get_ticks() % 1000) > 500
        if alpha:
            self.game.renderer.draw_text(surface, "PRESS ENTER TO INITIALIZE", SCREEN_WIDTH//2 - 150, 300, TERM_AMBER)
        
        # Show current user
        name = self.game.settings.get("name")
        self.game.renderer.draw_text(surface, f"USER: {name}", SCREEN_WIDTH//2 - 50, 500, TERM_WHITE)
        self.game.renderer.draw_text(surface, "[N] CHANGE NAME | [O] OPTIONS | [Q] QUIT", SCREEN_WIDTH//2 - 200, 600, (100, 100, 100))

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.game.scene_manager.switch_to(SongSelectScene)
            elif event.key == pygame.K_n:
                self.game.scene_manager.switch_to(NameEntryScene)
            elif event.key == pygame.K_q:
                pygame.quit()
                exit()
            elif event.key == pygame.K_o:
                self.game.scene_manager.switch_to(SettingsScene)

class NameEntryScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.temp_name = self.game.settings.get("name")

    def draw(self, surface):
        self.game.renderer.draw_text(surface, "UPDATE_USER_IDENTITY", 100, 100, TERM_GREEN, self.game.renderer.big_font)
        self.game.renderer.draw_text(surface, f"> {self.temp_name}_", 100, 300, TERM_WHITE, self.game.renderer.big_font)
        self.game.renderer.draw_text(surface, "ENTER to Confirm", 100, 500, TERM_AMBER)

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                if self.temp_name.strip():
                    self.game.settings.set("name", self.temp_name)
                self.game.scene_manager.switch_to(TitleScene)
            elif event.key == pygame.K_BACKSPACE:
                self.temp_name = self.temp_name[:-1]
            elif len(self.temp_name) < 16 and event.unicode.isprintable():
                self.temp_name += event.unicode.upper()

class SongSelectScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.songs = []
        self.selected_index = 0
        self.difficulties = DIFFICULTIES
        self.diff_index = 1
        self.load_songs()

    def on_enter(self, params=None):
        self.load_songs()

    def load_songs(self):
        s_dir = "songs"
        if not os.path.exists(s_dir): os.makedirs(s_dir)
        self.songs = [f for f in os.listdir(s_dir) if f.lower().endswith(('.mp3', '.wav', '.ogg'))]

    def draw(self, surface):
        self.game.renderer.draw_text(surface, "SELECT_OPERATION", 50, 50, TERM_GREEN)
        
        # Song List
        start_y = 200
        for i, song in enumerate(self.songs):
            if i == self.selected_index:
                color = TERM_GREEN
                # Check for High Score
                score_data = self.game.score_manager.get_score(song, self.difficulties[self.diff_index])
                suffix = ""
                if score_data:
                    suffix = f" [{score_data['rank']} - {score_data['score']}]"
                
                # Highlight logic
                self.game.renderer.draw_text(surface, f" >> {song}{suffix} << ", 50, start_y + i * 40, color)
            else:
                color = (60, 80, 60)
                self.game.renderer.draw_text(surface, f"    {song}", 50, start_y + i * 40, color)

        # Difficulty
        diff = self.difficulties[self.diff_index]
        c = TERM_RED if diff == "FUCK YOU" else TERM_AMBER
        self.game.renderer.draw_text(surface, f"DIFFICULTY: < {diff} >", 600, 150, c)

        # Info
        self.game.renderer.draw_text(surface, "[ENTER] PLAY | [E] EDITOR | [M] MULTIPLAYER", 50, 600, TERM_WHITE)
        self.game.renderer.draw_text(surface, "[ESC] BACK", 50, 650, (100, 100, 100))

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.scene_manager.switch_to(TitleScene)
            elif event.key == pygame.K_UP:
                self.selected_index = (self.selected_index - 1) % max(1, len(self.songs))
            elif event.key == pygame.K_DOWN:
                self.selected_index = (self.selected_index + 1) % max(1, len(self.songs))
            elif event.key == pygame.K_LEFT:
                self.diff_index = (self.diff_index - 1) % len(self.difficulties)
            elif event.key == pygame.K_RIGHT:
                self.diff_index = (self.diff_index + 1) % len(self.difficulties)
            elif event.key == pygame.K_RETURN:
                if self.songs:
                    # check if multiplayer
                    if self.game.network.connected:
                        # Send Proposal
                        song = self.songs[self.selected_index]
                        diff = self.difficulties[self.diff_index]
                        self.game.network.propose_song(song, diff)
                        # Show status "Waiting"
                    else:
                        from scenes.game_scene import GameScene
                        self.game.scene_manager.switch_to(GameScene, {
                            'song': self.songs[self.selected_index],
                            'difficulty': self.difficulties[self.diff_index]
                        })
            elif event.key == pygame.K_e:
                # EDITOR
                if self.songs:
                    from scenes.editor_scene import EditorScene
                    self.game.scene_manager.switch_to(EditorScene, {
                        'song': self.songs[self.selected_index],
                        'difficulty': self.difficulties[self.diff_index]
                    })
            elif event.key == pygame.K_m:
                 from scenes.lobby_scene import LobbyScene
                 self.game.scene_manager.switch_to(LobbyScene)

class SettingsScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.menu_items = ["SPEED", "VOLUME", "UPSCROLL", "OFFSET", "KEYBINDS", "BACK"]
        self.index = 0
        self.binding_mode = False
        self.binding_step = 0
        self.temp_binds = []
        
    def draw(self, surface):
        self.game.renderer.draw_text(surface, "SYSTEM CONFIG", 100, 50, TERM_GREEN, self.game.renderer.big_font)
        
        if self.binding_mode:
            # ... (keep existing)
            return

        speed = self.game.settings.get("speed")
        vol = self.game.settings.get("volume")
        upscroll = self.game.settings.get("upscroll")
        offset = self.game.settings.get("audio_offset")
        binds = self.game.settings.get("keybinds")
        bind_names = ",".join([pygame.key.name(k) for k in binds])
        
        items = [
            f"SCROLL SPEED: < {speed} >",
            f"VOLUME: < {int(vol*100)}% >",
            f"UPSCROLL: < {'ON' if upscroll else 'OFF'} >",
            f"OFFSET: < {offset}ms >",
            f"KEYBINDS: [{bind_names}]",
            "BACK"
        ]

        for i, item in enumerate(items):
            col = TERM_AMBER if i == self.index else TERM_WHITE
            self.game.renderer.draw_text(surface, item, 100, 200 + i*50, col)
            
        self.game.renderer.draw_text(surface, "Use ARROWS to adjust, ENTER to select", 100, 600, (100, 100, 100))

    def handle_input(self, event):
        if self.binding_mode:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.binding_mode = False
                    self.temp_binds = []
                    return
                    
                # Accept key
                self.temp_binds.append(event.key)
                self.binding_step += 1
                if self.binding_step >= 4:
                    self.game.settings.set("keybinds", self.temp_binds)
                    self.binding_mode = False
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.index = (self.index - 1) % len(self.menu_items)
            elif event.key == pygame.K_DOWN:
                self.index = (self.index + 1) % len(self.menu_items)
            elif event.key == pygame.K_LEFT:
                self.adjust(-1)
            elif event.key == pygame.K_RIGHT:
                self.adjust(1)
            elif event.key == pygame.K_RETURN:
                if self.menu_items[self.index] == "BACK":
                    self.game.scene_manager.switch_to(TitleScene)
                elif self.menu_items[self.index] == "KEYBINDS":
                    self.binding_mode = True
                    self.binding_step = 0
                    self.temp_binds = []
            elif event.key == pygame.K_ESCAPE:
                self.game.scene_manager.switch_to(TitleScene)

    def adjust(self, direction):
        if self.menu_items[self.index] == "SPEED":
            cur = self.game.settings.get("speed")
            cur += direction * 50
            cur = max(100, min(2000, cur))
            self.game.settings.set("speed", cur)
        elif self.menu_items[self.index] == "VOLUME":
            cur = self.game.settings.get("volume")
            cur += direction * 0.1
            cur = max(0.0, min(1.0, cur))
            self.game.settings.set("volume", cur)
            pygame.mixer.music.set_volume(cur)
        elif self.menu_items[self.index] == "UPSCROLL":
            # Toggle on any direction
            cur = self.game.settings.get("upscroll")
            self.game.settings.set("upscroll", not cur)
        elif self.menu_items[self.index] == "OFFSET":
            cur = self.game.settings.get("audio_offset")
            cur += direction * 5 # 5ms steps
            cur = max(-200, min(200, cur))
            self.game.settings.set("audio_offset", cur)

