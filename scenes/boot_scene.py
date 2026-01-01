"""
Boot Scene - BIOS-style startup with retro aesthetics
Press ENTER to skip at any time.
"""

import pygame
import os
from core.scene_manager import Scene
from core.config import *
import random


class BootScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.lines = []
        self.finished = False
        self.skipped = False
        
        # Load sounds (Lower Volume as requested)
        self.sfx_boot = self._load_sfx("sfx/sfx_boot.wav", 0.2)
        self.sfx_type = self._load_sfx("sfx/sfx_type.wav", 0.1)
        self.sfx_hdd = self._load_sfx("sfx/sfx_hdd.wav", 0.1)
        self.sfx_success = self._load_sfx("sfx/sfx_success.wav", 0.3)
        
        # RAM animation
        self.ram_kb = 0
        self.total_ram = 65536  # 64 MB
        
        # Boot sequence with timing (Reverted to original BIOS flow)
        self.boot_steps = [
            {"text": "", "delay": 20},
            {"text": "╔══════════════════════════════════════════════════════╗", "delay": 5, "color": "cyan"},
            {"text": "║          TUR BIOS v2.0.4 (c) 2024 TUR CORP            ║", "delay": 10, "color": "cyan"},
            {"text": "╚══════════════════════════════════════════════════════╝", "delay": 20, "color": "cyan"},
            {"text": "", "delay": 10},
            {"text": "CPU: Synthetic Neural Processor @ 4.0 GHz", "delay": 15, "sfx": "type"},
            {"text": "FPU: Integrated Rhythm Coprocessor", "delay": 10, "sfx": "type"},
            {"text": "", "delay": 5},
            {"text": "Testing Memory...", "action": "RAM", "delay": 2, "sfx": "hdd"},
            {"text": "", "delay": 20},
            {"text": "Detecting Storage...", "delay": 25, "sfx": "hdd"},
            {"text": "  ├─ /dev/tur0: TUR System Disk [128GB] ✓", "delay": 10, "color": "green"},
            {"text": "  └─ /dev/song0: Song Library [∞]    ✓", "delay": 15, "color": "green"},
            {"text": "", "delay": 10},
            {"text": "Initializing Subsystems...", "delay": 20, "sfx": "hdd"},
            {"text": "  ├─ Audio Engine.......... OK", "delay": 8, "color": "green"},
            {"text": "  ├─ Video Renderer........ OK", "delay": 8, "color": "green"},
            {"text": "  ├─ Input Handler......... OK", "delay": 8, "color": "green"},
            {"text": "  └─ Network Module........ OK", "delay": 12, "color": "green"},
            {"text": "", "delay": 10},
            {"text": "Loading Songs...", "action": "SONGS", "delay": 2, "sfx": "hdd"},
            {"text": "", "delay": 15},
            {"text": "════════════════════════════════════════════════════════", "delay": 10, "color": "dim"},
            {"text": "  BOOT SUCCESSFUL - LAUNCHING TUR SYSTEM", "delay": 20, "sfx": "success", "color": "primary"},
            {"text": "════════════════════════════════════════════════════════", "delay": 10, "color": "dim"},
            {"text": "", "delay": 40},
            {"text": "", "action": "DONE", "delay": 10}
        ]
        
        self.current_step_idx = 0
        self.wait_time = 0
        self.blink_timer = 0
        self.song_load_status = ""
        self.song_load_done = False
    
    def _load_sfx(self, path, volume):
        if os.path.exists(path):
            try:
                snd = pygame.mixer.Sound(path)
                snd.set_volume(volume)
                return snd
            except: return None
        return None

    def draw(self, surface):
        # Dark background with subtle gradient
        surface.fill((8, 12, 18))
        
        # Scanline effect
        for y in range(0, 768, 4):
            pygame.draw.line(surface, (5, 8, 12), (0, y), (1024, y))
        
        theme = self.game.renderer.get_theme()
        
        # Draw all lines with color
        y = 40
        for line_data in self.lines:
            if isinstance(line_data, dict):
                text = line_data.get("text", "")
                color_key = line_data.get("color", "text")
            else:
                text = line_data
                color_key = "text"
            
            # Color mapping
            if color_key == "cyan":
                color = (50, 200, 255)
            elif color_key == "green":
                color = (50, 255, 100)
            elif color_key == "dim":
                color = (80, 80, 80)
            elif color_key == "primary":
                color = theme["primary"]
            else:
                color = (180, 180, 180)
            
            self.game.renderer.draw_text(surface, text, 50, y, color)
            y += 28
        
        # RAM counter animation
        if self.current_step_idx < len(self.boot_steps):
            if self.boot_steps[self.current_step_idx].get("action") == "RAM":
                pct = int(100 * self.ram_kb / self.total_ram)
                bar_w = int(300 * self.ram_kb / self.total_ram)
                
                pygame.draw.rect(surface, (30, 30, 30), (50, y, 300, 20))
                pygame.draw.rect(surface, (50, 255, 100), (50, y, bar_w, 20))
                self.game.renderer.draw_text(surface, f"{self.ram_kb} KB [{pct}%]", 370, y, (150, 150, 150))
        
        # Song loading status
        if self.song_load_status:
            self.game.renderer.draw_text(surface, f"  {self.song_load_status}", 50, y - 30, (150, 200, 150))
        
        # Blinking cursor
        self.blink_timer = (self.blink_timer + 1) % 60
        if self.blink_timer < 30:
            pygame.draw.rect(surface, (200, 200, 200), (50, y + 10, 12, 22))
        
        # Skip hint
        from core.localization import get_text
        skip_txt = f"{get_text(self.game, '[ENTER] Skip')}"
        self.game.renderer.draw_text(surface, skip_txt, 850, 700, (60, 60, 80))

    def update(self):
        if self.finished:
            return
        
        item = self.boot_steps[self.current_step_idx]
        
        # RAM animation
        if item.get("action") == "RAM":
            self.ram_kb += 2048
            if self.ram_kb >= self.total_ram:
                self.lines.append({"text": f"Memory Test: {self.total_ram} KB OK", "color": "green"})
                self.advance_step()
            return
        
        # SONGS loading action
        if item.get("action") == "SONGS":
            if not self.song_load_done:
                self._start_song_loading()
                return
            else:
                # Done loading, show result
                self.lines.append({"text": f"  └─ Songs loaded: {self.songs_loaded} files", "color": "green"})
                self.advance_step()
                return
        
        # Delay
        self.wait_time += 1
        
        # Play boot sound on first step
        if self.current_step_idx == 0 and self.wait_time == 1:
            if self.sfx_boot:
                self.sfx_boot.play()
        
        if self.wait_time >= item["delay"]:
            if item.get("action") == "DONE":
                self.finish_boot()
            else:
                txt = item.get("text", "")
                color = item.get("color", "text")
                
                if txt:
                    self.lines.append({"text": txt, "color": color})
                    
                    sfx = item.get("sfx")
                    if sfx == "type" and self.sfx_type:
                        self.sfx_type.play()
                    elif sfx == "hdd" and self.sfx_hdd:
                        self.sfx_hdd.play()
                    elif sfx == "success" and self.sfx_success:
                        self.sfx_success.play()
                
                self.advance_step()

    def advance_step(self):
        self.current_step_idx += 1
        self.wait_time = 0
    
    def _start_song_loading(self):
        """Start song conversion and loading in background"""
        if hasattr(self, '_song_thread_started'):
            return
        self._song_thread_started = True
        self.songs_loaded = 0
        
        import threading
        def load_thread():
            try:
                from core.song_converter import auto_convert_songs, preload_all_songs
                
                # Convert audio and .osu files (callback takes msg and optional pct)
                def update_status(msg, pct=0):
                    self.song_load_status = msg
                
                auto_convert_songs("songs", "MEDIUM", callback=update_status)
                
                # Preload all .tur files
                songs = preload_all_songs("songs", callback=update_status)
                self.songs_loaded = len(songs)
                
                # Store in game for later use
                self.game.song_cache = songs
                
                # --- SESSION REFRESH ---
                # Check if we have a saved token and refresh profile while booting
                if self.game.master_client.logged_in:
                    update_status("Synchronizing uplink...")
                    profile = self.game.master_client.get_my_stats()
                    if profile:
                        self.game.settings.set("is_admin", profile.get("is_admin", False))
                        self.game.settings.set("username", profile.get("username", "User"))
                        # print(f"Session Refreshed: {profile.get('username')}")
                
            except Exception as e:
                print(f"Song loading error: {e}")
                import traceback
                traceback.print_exc()
                self.songs_loaded = 0
            
            self.song_load_done = True
            self.song_load_status = ""
        
        threading.Thread(target=load_thread, daemon=True).start()
    
    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.finish_boot()

    def finish_boot(self):
        if self.finished:
            return
        self.finished = True
        
        if not self.game.settings.get("eula_accepted"):
            from scenes.eula_scene import EULAScene
            self.game.scene_manager.switch_to(EULAScene)
            return

        from scenes.menu_scenes import TitleScene
        if not self.game.settings.get("setup_complete"):
            from scenes.setup_scene import SetupScene
            self.game.scene_manager.switch_to(SetupScene)
        else:
            self.game.scene_manager.switch_to(TitleScene)
            self.game.play_menu_bgm()
