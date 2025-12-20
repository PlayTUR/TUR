import pygame
from scene_manager import Scene
from config import *
import os

class GameScene(Scene):
    def on_enter(self, params):
        self.song_name = params['song']
        self.difficulty = params['difficulty']
        self.mode = params.get('mode', 'single') # single, multi
        
        path = os.path.join("songs", self.song_name)
        
        # Load map
        self.beatmap = self.game.generator.get_beatmap(path, self.difficulty)
        for note in self.beatmap: note['hit'] = False 
        
        self.game.audio.load_song(path)
        vol = self.game.settings.get("volume")
        self.game.audio.set_volume(vol)
        
        # Sync Logic
        self.waiting_for_sync = False
        if self.mode == 'multi':
            if self.game.network.is_host:
                self.start_time = self.game.network.start_game_request()
                self.waiting_for_sync = True
            else:
                self.start_time = self.game.network.start_timestamp
                self.waiting_for_sync = True
                if self.start_time == 0:
                     # Fallback if packet hasn't arrived (should have in song select)
                     # In robust system we wait indefinitely for START packet
                     self.waiting_for_sync = True
        else:
             self.game.audio.play()

        self.completed_notes = 0
        self.total_notes = len(self.beatmap)
        
        self.score = 0
        self.combo = 0
        self.max_combo = 0
        self.bads = 0
        self.goods = 0
        self.perfects = 0
        self.misses = 0
        
        self.finished = False

    def on_exit(self):
        self.game.audio.stop()
        self.game.play_menu_bgm()

    def update(self):
        # Sync Start Logic
        if self.waiting_for_sync:
            import time
            if self.start_time > 0 and time.time() >= self.start_time:
                self.game.audio.play()
                self.waiting_for_sync = False
            else:
                 # Check if client received start time late
                 if not self.game.network.is_host and self.game.network.start_timestamp > 0:
                      self.start_time = self.game.network.start_timestamp
                 return
                 
        if not self.game.audio.is_playing and not self.finished and not self.waiting_for_sync:
            self.finish_game()
            return
            
        current_time = self.game.audio.get_position()
        self.game.renderer.update_effects()
        
        # Miss Logic
        for note in self.beatmap:
            if not note['hit'] and (note['time'] - current_time) < -0.15:
                note['hit'] = True
                self.break_combo()
                self.misses += 1
                self.game.renderer.add_hit_effect("MISS", note['lane'])

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                from scenes.menu_scenes import SongSelectScene
                self.game.scene_manager.switch_to(SongSelectScene)
            else:
                self.handle_hit(event.key)
        elif event.type == pygame.KEYUP:
             self.update_key(event.key, False)

    def update_key(self, key, pressed):
        keys = self.game.settings.get("keybinds")
        if key in keys:
            lane = keys.index(key)
            self.game.renderer.key_states[lane] = pressed

    def handle_hit(self, key):
        keys = self.game.settings.get("keybinds")
        if key not in keys: return
        lane = keys.index(key)
        self.game.renderer.key_states[lane] = True
        
        current_time = self.game.audio.get_position()
        closest = None
        min_diff = 1.0
        
        # Simple search (opt: can optimize by window)
        for note in self.beatmap:
            if note['lane'] == lane and not note['hit']:
                diff = note['time'] - current_time
                if abs(diff) < min_diff:
                    min_diff = abs(diff)
                    closest = note
        
        if closest and min_diff < 0.15:
            closest['hit'] = True
            
            if min_diff < 0.05:
                self.score += 300
                self.perfects += 1
                self.game.renderer.add_hit_effect("PERFECT", lane)
                self.combo += 1
            elif min_diff < 0.1:
                self.score += 100
                self.goods += 1
                self.game.renderer.add_hit_effect("GREAT", lane)
                self.combo += 1
            else:
                self.score += 50
                self.bads += 1
                self.game.renderer.add_hit_effect("BAD", lane)
                self.combo = 0 # Bad breaks combo? user said mania style, mania doesn't break on 50 usually but keeps combo low. Let's break for strictness now.
            
            if self.combo > self.max_combo: self.max_combo = self.combo
            
    def break_combo(self):
        self.combo = 0

    def finish_game(self):
        self.finished = True
        from scenes.result_scene import ResultScene
        self.game.scene_manager.switch_to(ResultScene, {
            'score': self.score,
            'max_combo': self.max_combo,
            'perfects': self.perfects,
            'goods': self.goods,
            'misses': self.misses,
            'song': self.song_name,
            'difficulty': self.difficulty
        })

    def draw(self, surface):
        if self.waiting_for_sync:
             import time
             left = max(0, self.start_time - time.time())
             self.game.renderer.draw_text(surface, f"SYNCING... {left:.1f}", 400, 300, TERM_AMBER, self.game.renderer.big_font)
             return

        speed = self.game.settings.get("speed")
        upscroll = self.game.settings.get("upscroll")
        self.game.renderer.draw_lanes(surface, upscroll)
        self.game.renderer.draw_notes(surface, self.beatmap, self.game.audio.get_position(), speed, upscroll)
        self.game.renderer.draw_effects(surface)
        
        # HUD
        self.game.renderer.draw_text(surface, f"SCORE: {self.score}", 20, 20, TERM_WHITE)
        self.game.renderer.draw_text(surface, f"COMBO: {self.combo}", 20, 50, TERM_AMBER)
        
        if self.mode == 'multi':
             self.game.renderer.draw_text(surface, f"OPPONENT: {self.game.network.opponent_score}", 20, 80, TERM_RED)

        # Progress Bar
        if self.game.audio.start_time > 0:
            # Ideally audio manager gives us duration, but we can guess or use note completion
            # Hack: simple bar at bottom
            pass
