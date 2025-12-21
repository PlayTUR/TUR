import pygame
from core.scene_manager import Scene
from core.config import *
import os
import math

class TitleScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        import random
        self.quotes = [
            "INITIALIZING KERNEL...",
            "LOADING ASSETS... [||||||||||]",
            "ERROR 418: I'M A TEAPOT",
            "ALL YOUR BASE ARE BELONG TO US",
            "HACK THE PLANET",
            "IT WORKS ON MY MACHINE",
            "SUDO MAKE ME A SANDWICH",
            "INSERT COIN TO CONTINUE",
            "BUFFER OVERFLOW DETECTED"
        ]
        self.quote = random.choice(self.quotes)
        
        # Menu Options
        self.menu_items = ["SINGLE PLAYER", "STORY CAMPAIGN", "MULTIPLAYER", "OPTIONS", "SYSTEM UPDATE", "EXIT"]
        self.selected_index = 0
        self.show_exit_confirm = False

    def on_enter(self, params=None):
        if not pygame.mixer.music.get_busy():
            self.game.play_menu_bgm()

    def draw(self, surface):
        theme = self.game.renderer.get_theme()
        
        # 1. Background Grid Effect
        t = pygame.time.get_ticks()
        
        # Draw BG
        surface.fill(theme["bg"])
        
        grid_offset_y = (t * 0.1) % 40
        grid_col = theme["grid"]
        
        # Horizontal
        for y in range(0, SCREEN_HEIGHT + 40, 40):
            line_y = y + grid_offset_y - 40
            pygame.draw.line(surface, grid_col, (0, line_y), (SCREEN_WIDTH, line_y))
            
        # Vertical
        for x in range(0, SCREEN_WIDTH, 40):
            pygame.draw.line(surface, grid_col, (x, 0), (x, SCREEN_HEIGHT))

        # 2. Main Title (ASCII TUR)
        # Menu Music is 100 BPM -> 600ms per beat
        beat_dur = 600 
        beat_prog = (t % beat_dur) / beat_dur
        pulse = pow(1.0 - beat_prog, 3) 
        
        # TUR ASCII
        tur_art = [
            "████████╗██╗   ██╗██████╗ ",
            "╚══██╔══╝██║   ██║██╔══██╗",
            "   ██║   ██║   ██║██████╔╝",
            "   ██║   ██║   ██║██╔══██╗",
            "   ██║   ╚██████╔╝██║  ██║",
            "   ╚═╝    ╚═════╝ ╚═╝  ╚═╝"
        ]
        
        start_y = 100
        for i, line in enumerate(tur_art):
            c = theme["primary"] if i % 2 == 0 else theme["secondary"]
            c = theme["primary"]
            
            font = self.game.renderer.font 
            w, h = font.size(line)
            x = (SCREEN_WIDTH - w) // 2
            
            self.game.renderer.draw_text(surface, line, x+2, start_y + i * 20 + 2, theme["grid"])
            self.game.renderer.draw_text(surface, line, x, start_y + i * 20, c)

        # Draw Quote
        q_surf = self.game.renderer.font.render(f"> {self.quote} <", False, theme["grid"])
        q_rect = q_surf.get_rect(center=(SCREEN_WIDTH//2, 280))
        surface.blit(q_surf, q_rect)

        # 3. Interactive Menu Box
        menu_start_y = 350
        menu_h = len(self.menu_items) * 50 + 40
        menu_w = 500 
        menu_x = (SCREEN_WIDTH - menu_w) // 2
        
        # Draw Window Border
        pygame.draw.rect(surface, theme["bg"], (menu_x, menu_start_y, menu_w, menu_h))
        pygame.draw.rect(surface, theme["grid"], (menu_x, menu_start_y, menu_w, menu_h), 2)
        pygame.draw.rect(surface, theme["grid"], (menu_x, menu_start_y-30, menu_w, 30))
        self.game.renderer.draw_text(surface, "SYSTEM//MENU", menu_x + 10, menu_start_y - 25, theme["text"])
        
        for i, item in enumerate(self.menu_items):
            color = theme["primary"] if i == self.selected_index else theme["text"]
            prefix = " > " if i == self.selected_index else "   "
            
            txt = f"{prefix}{item}"
            x = menu_x + 40
            self.game.renderer.draw_text(surface, txt, x, menu_start_y + 20 + i * 50, color, self.game.renderer.big_font)
            
        # 4. User Info
        self.game.renderer.draw_text(surface, f"USER: {self.game.settings.get('name')}", 20, SCREEN_HEIGHT - 60, theme["secondary"])

    # 5. Exit Confirmation Overlay
        if self.show_exit_confirm:
            # Dim background
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(200)
            overlay.fill((0,0,0))
            surface.blit(overlay, (0,0))
            
            # Popup Box (Wider to fit text)
            w, h = 600, 250
            x, y = (SCREEN_WIDTH - w)//2, (SCREEN_HEIGHT - h)//2
            
            pygame.draw.rect(surface, theme["bg"], (x, y, w, h))
            pygame.draw.rect(surface, theme["error"], (x, y, w, h), 2)
            
            # Center Text
            title = "TERMINATE SYSTEM?"
            sub = "CONFIRM SHUTDOWN [Y/N]"
            
            font = self.game.renderer.big_font
            tw, th = font.size(title)
            self.game.renderer.draw_text(surface, title, x + (w-tw)//2, y + 60, theme["error"], font)
            
            font_small = self.game.renderer.font
            sw, sh = font_small.size(sub)
            self.game.renderer.draw_text(surface, sub, x + (w-sw)//2, y + 140, theme["text"], font_small)

    def handle_input(self, event):
        if self.show_exit_confirm:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_y or event.key == pygame.K_RETURN:
                    self.play_sfx("shutdown")
                    self.game.trigger_reboot() # Initiates fade out exit
                elif event.key == pygame.K_n or event.key == pygame.K_ESCAPE:
                    self.play_sfx("back")
                    self.show_exit_confirm = False
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_index = (self.selected_index - 1) % len(self.menu_items)
                self.play_sfx("blip")
            elif event.key == pygame.K_DOWN:
                self.selected_index = (self.selected_index + 1) % len(self.menu_items)
                self.play_sfx("blip")
            elif event.key == pygame.K_RETURN:
                self.play_sfx("accept")
                choice = self.menu_items[self.selected_index]
                if choice == "SINGLE PLAYER":
                    self.game.scene_manager.switch_to(SongSelectScene)
                elif choice == "STORY CAMPAIGN":
                    from scenes.story_scene import StoryScene
                    self.game.scene_manager.switch_to(StoryScene)
                elif choice == "MULTIPLAYER":
                    from scenes.lobby_scene import LobbyScene
                    self.game.scene_manager.switch_to(LobbyScene)
                elif choice == "OPTIONS": 
                    self.game.scene_manager.switch_to(SettingsScene)
                elif choice == "SYSTEM UPDATE":
                    from scenes.update_scene import UpdateScene
                    self.game.scene_manager.switch_to(UpdateScene)
                elif choice == "EXIT":
                    self.show_exit_confirm = True
            elif event.key == pygame.K_n:
                 self.game.scene_manager.switch_to(NameEntryScene)

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
                self.play_sfx("accept")
                if self.temp_name.strip():
                    self.game.settings.set("name", self.temp_name)
                self.game.scene_manager.switch_to(TitleScene)
            elif event.key == pygame.K_BACKSPACE:
                self.play_sfx("blip")
                self.temp_name = self.temp_name[:-1]
            elif len(self.temp_name) < 16 and event.unicode.isprintable():
                self.play_sfx("type") # Reuse type sound!
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
        self.songs.sort()
        print(f"DEBUG: Loaded songs: {self.songs}")

    def draw(self, surface):
        theme = self.game.renderer.get_theme()
        
        # BG
        surface.fill(theme["bg"])
        
        self.game.renderer.draw_text(surface, "SELECT_OPERATION", 50, 50, theme["primary"])
        
        # Window Frame for Song List
        list_x = 40
        list_y = 180
        list_w = 500
        list_h = 400
        pygame.draw.rect(surface, theme["grid"], (list_x, list_y, list_w, list_h), 2)
        # Header
        pygame.draw.rect(surface, theme["grid"], (list_x, list_y-30, list_w, 30))
        self.game.renderer.draw_text(surface, "AVAILABLE_PROGRAMS", list_x + 10, list_y - 25, theme["text"])
        
        # Song List (Inside Box)
        # Basic scroll logic: show neighbor items
        # Just show all for now, assuming list fits or user scrolls index
        # We should only draw visible range to fit in box
        
        visible_count = 9
        start_idx = max(0, self.selected_index - 4)
        end_idx = min(len(self.songs), start_idx + visible_count)
        
        for i in range(start_idx, end_idx):
            song = self.songs[i]
            y_pos = list_y + 20 + (i - start_idx) * 40
            
            if i == self.selected_index:
                color = theme["primary"]
                # Check for High Score
                score_data = self.game.score_manager.get_score(song, self.difficulties[self.diff_index])
                suffix = ""
                if score_data:
                    suffix = f" [{score_data['rank']}]"
                
                # Highlight logic
                # Draw selection bar
                pygame.draw.rect(surface, (theme["grid"][0]//2, theme["grid"][1]//2, theme["grid"][2]//2), (list_x+2, y_pos, list_w-4, 30))
                self.game.renderer.draw_text(surface, f"> {song}{suffix}", list_x + 10, y_pos + 5, color)
            else:
                color = theme["text"]
                self.game.renderer.draw_text(surface, f"  {song}", list_x + 10, y_pos + 5, color)

        # Difficulty
        diff = self.difficulties[self.diff_index]
        c = theme["error"] if diff == "FUCK YOU" else theme["secondary"]
        self.game.renderer.draw_text(surface, f"DIFFICULTY: < {diff} >", 600, 150, c)

        # Info
        self.game.renderer.draw_text(surface, "[ENTER] PLAY | [E] EDITOR | [M] MULTIPLAYER", 50, 600, theme["text"])
        self.game.renderer.draw_text(surface, "[F5] RELOAD | [ESC] BACK", 50, 650, (100, 100, 100))

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.play_sfx("back")
                self.game.scene_manager.switch_to(TitleScene)
            elif event.key == pygame.K_F5:
                self.play_sfx("hdd") # "Reload" sound
                self.load_songs()
            elif event.key == pygame.K_UP:
                self.selected_index = (self.selected_index - 1) % max(1, len(self.songs))
                self.play_sfx("blip")
            elif event.key == pygame.K_DOWN:
                self.selected_index = (self.selected_index + 1) % max(1, len(self.songs))
                self.play_sfx("blip")
            elif event.key == pygame.K_LEFT:
                self.diff_index = (self.diff_index - 1) % len(self.difficulties)
                self.play_sfx("blip")
            elif event.key == pygame.K_RIGHT:
                self.diff_index = (self.diff_index + 1) % len(self.difficulties)
                self.play_sfx("blip")
            elif event.key == pygame.K_RETURN:
                if self.songs:
                    self.play_sfx("accept")
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
                else: 
                     self.play_sfx("back") # Error/Empty
            elif event.key == pygame.K_e:
                # EDITOR
                if self.songs:
                    self.play_sfx("accept")
                    from scenes.editor_scene import EditorScene
                    self.game.scene_manager.switch_to(EditorScene, {
                        'song': self.songs[self.selected_index],
                        'difficulty': self.difficulties[self.diff_index]
                    })
            elif event.key == pygame.K_m:
                 self.play_sfx("accept")
                 from scenes.lobby_scene import LobbyScene
                 self.game.scene_manager.switch_to(LobbyScene)

class SettingsScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.menu_items = [
            "SPEED", "VOLUME", "THEME", "UPSCROLL", "OFFSET", 
            "COLOR1_R", "COLOR1_G", "COLOR1_B", 
            "KEYBINDS", "BACK"
        ]
        self.index = 0
        self.binding_mode = False
        self.binding_step = 0
        self.temp_binds = []
        
    def draw(self, surface):
        theme = self.game.renderer.get_theme()
        surface.fill(theme["bg"])
        
        self.game.renderer.draw_text(surface, "SYSTEM CONFIG", 100, 30, theme["primary"], self.game.renderer.big_font)
        
        if self.binding_mode:
            # Simple bind overlay
            cur_key = ["LANE 1", "LANE 2", "LANE 3", "LANE 4"][self.binding_step]
            self.game.renderer.draw_text(surface, f"PRESS KEY FOR: {cur_key}", 100, 300, theme["secondary"])
            return

        # Fetch Data
        s = self.game.settings
        speed = s.get("speed")
        vol = s.get("volume")
        theme_name = s.get("theme")
        upscroll = s.get("upscroll")
        offset = s.get("audio_offset")
        shape = s.get("note_shape")
        c1 = s.get("note_col_1")
        
        binds = s.get("keybinds")
        bind_names = ",".join([pygame.key.name(k) for k in binds])
        
        # Helper to make color preview
        def col_str(c): return f"({c[0]},{c[1]},{c[2]})"

        # List Items
        items = [
            f"SCROLL SPEED: < {speed} >",
            f"VOLUME: < {int(vol*100)}% >",
            f"THEME: < {theme_name} >",
            f"UPSCROLL: < {'ON' if upscroll else 'OFF'} >",
            f"OFFSET: < {offset}ms >",
            # Shape Removed
            f"INNER COLOR R: < {c1[0]} >",
            f"INNER COLOR G: < {c1[1]} >",
            f"INNER COLOR B: < {c1[2]} >",
            f"KEYBINDS: [{bind_names}]",
            "BACK"
        ]

        start_y = 100
        for i, item in enumerate(items):
            col = theme["secondary"] if i == self.index else theme["text"]
            y = start_y + i * 45
            self.game.renderer.draw_text(surface, item, 100, y, col)
            
            # Preview Color Square next to RGB controls
            if "INNER COLOR" in item:
                 pygame.draw.rect(surface, c1, (600, y, 40, 40))
                 pygame.draw.rect(surface, (255,255,255), (600, y, 40, 40), 2)

        self.game.renderer.draw_text(surface, "ARROWS: Adjust | ENTER: Select", 100, 700, (100, 100, 100))

    def handle_input(self, event):
        if self.binding_mode:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.play_sfx("back")
                    self.binding_mode = False
                    return
                # Accept key
                self.play_sfx("accept")
                self.temp_binds.append(event.key)
                self.binding_step += 1
                if self.binding_step >= 4:
                    self.game.settings.set("keybinds", self.temp_binds)
                    self.binding_mode = False
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.index = (self.index - 1) % len(self.menu_items)
                self.play_sfx("blip")
            elif event.key == pygame.K_DOWN:
                self.index = (self.index + 1) % len(self.menu_items)
                self.play_sfx("blip")
            elif event.key == pygame.K_LEFT:
                if self.adjust(-1, event.mod & pygame.KMOD_SHIFT):
                     self.play_sfx("blip")
            elif event.key == pygame.K_RIGHT:
                if self.adjust(1, event.mod & pygame.KMOD_SHIFT):
                     self.play_sfx("blip")
            elif event.key == pygame.K_RETURN:
                self.play_sfx("accept")
                if self.menu_items[self.index] == "BACK":
                    self.game.scene_manager.switch_to(TitleScene)
                elif self.menu_items[self.index] == "KEYBINDS":
                    self.binding_mode = True
                    self.binding_step = 0
                    self.temp_binds = []
            elif event.key == pygame.K_ESCAPE:
                self.play_sfx("back")
                self.game.scene_manager.switch_to(TitleScene)

    def adjust(self, direction, fast=False):
        item = self.menu_items[self.index]
        s = self.game.settings
        
        if item == "SPEED":
            cur = s.get("speed")
            cur += direction * (50 if not fast else 200)
            s.set("speed", max(100, min(2000, cur)))
        elif item == "VOLUME":
            cur = s.get("volume")
            cur += direction * 0.1
            cur = max(0.0, min(1.0, cur))
            s.set("volume", cur)
            pygame.mixer.music.set_volume(cur)
        elif item == "THEME":
            themes_list = list(THEMES.keys())
            cur = s.get("theme")
            try:
                idx = themes_list.index(cur)
            except:
                idx = 0
            new_idx = (idx + direction) % len(themes_list)
            new_theme = themes_list[new_idx]
            s.set("theme", new_theme)
            
            # Auto-apply theme colors to Note Colors
            t_data = THEMES[new_theme]
            s.set("note_col_1", list(t_data["primary"]))
            s.set("note_col_2", list(t_data["secondary"]))
            
        elif item == "UPSCROLL":
            s.set("upscroll", not s.get("upscroll"))
        elif item == "OFFSET":
            cur = s.get("audio_offset")
            cur += direction * 5
            s.set("audio_offset", max(-200, min(200, cur)))
        # SHAPE Removed
        elif item.startswith("COLOR1"):
            # RGB adjustment
            c1 = list(s.get("note_col_1"))
            idx = {"R":0, "G":1, "B":2}[item.split("_")[1]]
            c1[idx] = max(0, min(255, c1[idx] + direction * (10 if fast else 5)))
            s.set("note_col_1", c1)
            # Custom RGB edit implies partial deviation from theme, but that's fine.

        s.save()
        return True

