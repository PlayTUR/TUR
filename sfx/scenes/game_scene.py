import pygame
from core.scene_manager import Scene
from core.config import *
import os

class GameScene(Scene):
    def on_enter(self, params):
        self.song_name = params['song']
        self.difficulty = params['difficulty']
        self.mode = params.get('mode', 'single') # single, multi
        
        path = os.path.join("songs", self.song_name)
        
        # Load map
        map_data = self.game.generator.get_beatmap(path, self.difficulty)
        
        if isinstance(map_data, list):
            # Legacy fallback
            self.beatmap = map_data
            self.bpm = 120.0
            self.duration = 180.0
        else:
            self.beatmap = map_data['notes']
            self.bpm = map_data.get('bpm', 120.0)
            self.duration = map_data.get('duration', 180.0)

        for note in self.beatmap: note['hit'] = False 
        
        # Reactivity
        self.beat_pulse = 0.0
        
        self.game.audio.load_song(path)
        vol = self.game.settings.get("volume")
        self.game.audio.set_volume(vol)
        
        # Intro / Sync Logic
        self.waiting_for_sync = False
        self.intro_active = True
        self.intro_timer = 0.0
        self.intro_duration = 2.0 # Seconds of pixelation intro
        
        if self.mode == 'multi':
            self.intro_active = False # Skip intro for keep-in-sync (or sync intro?)
            # Simplified: Skip intro for multi for now to avoid desync
            if self.game.network.is_host:
                self.start_time = self.game.network.start_game_request()
                self.waiting_for_sync = True
            else:
                self.start_time = self.game.network.start_timestamp
                self.waiting_for_sync = True
                if self.start_time == 0:
                     self.waiting_for_sync = True
        else:
             # Single player: Do not play yet. Wait for intro.
             pass

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
        self.paused = False

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
        
        # Intro Logic
        if self.intro_active:
            self.intro_timer += 1.0 / 60.0  # Approx dt
            if self.intro_timer >= self.intro_duration:
                self.intro_active = False
                if not self.paused:
                    self.game.audio.play()
            return # Don't update game logic during intro (notes don't move)

        if self.paused: return

        if not self.game.audio.is_playing and not self.finished and not self.waiting_for_sync:
            self.finish_game()
            return
            
        current_time = self.game.audio.get_position()
        self.game.renderer.update_effects()
        
        # Pulse Calculation
        spb = 60.0 / self.bpm
        beat_prog = (current_time % spb) / spb 
        self.beat_pulse = pow(1.0 - beat_prog, 4) 
        
        # Miss Logic
        for note in self.beatmap:
            if not note['hit'] and (note['time'] - current_time) < -0.15:
                note['hit'] = True
                self.break_combo()
                self.misses += 1
                self.game.renderer.add_hit_effect("MISS", note['lane'])

    # ... (Keep handle_input, toggle_pause, etc same) ...
    # RE-INCLUDE THEM TO BE SAFE since I am replacing huge chunk?
    # Actually I should use StartLine/EndLine carefully or just replace draw and update separately?
    # The user request asks for animation.
    # The chunk replacement above covers on_enter and update.
    # I need to be careful not to delete handle_input etc.
    # I will split this into smaller edits.

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.paused:
                   # Resume or Quit? Double ESC to quit?
                   # Simple: Unpause if paused, or Quit if not?
                   # Let's say ESC toggles pause, or dedicated quit?
                   # Actually user wants pause.
                   from scenes.menu_scenes import SongSelectScene
                   self.game.scene_manager.switch_to(SongSelectScene)
                else:
                    self.toggle_pause()
            elif event.key == pygame.K_SPACE or event.key == pygame.K_p:
                self.toggle_pause()
            elif event.key == pygame.K_r:
                # Fast Restart
                # We can just re-enter the scene with same params
                params = {
                    'song': self.song_name,
                    'difficulty': self.difficulty,
                    'mode': self.mode
                }
                # Stop audio first
                self.game.audio.stop()
                self.on_enter(params) # Re-init state
                # Note: on_enter usually expects scene switch, but calling it manually resets vars
                # A Cleaner way is self.game.scene_manager.switch_to(GameScene, params)
                from scenes.game_scene import GameScene
                self.game.scene_manager.switch_to(GameScene, params)
                return
            elif event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:
                self.change_volume(0.1)
            elif event.key == pygame.K_MINUS:
                self.change_volume(-0.1)
            else:
                if not self.paused:
                    self.handle_hit(event.key)
        elif event.type == pygame.KEYUP:
             if not self.paused:
                 self.update_key(event.key, False)

    def toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            self.game.audio.pause()
        else:
            self.game.audio.unpause()

    def change_volume(self, change):
        vol = self.game.settings.get("volume")
        vol = max(0.0, min(1.0, vol + change))
        self.game.settings.set("volume", vol)
        self.game.audio.set_volume(vol)
        # Show volume overlay?
        self.game.renderer.draw_text(None, f"VOL: {int(vol*100)}%", 600, 50, TERM_GREEN)

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
            
            # Determine Color
            col_inner = self.game.settings.get("note_col_1")
            col_outer = self.game.settings.get("note_col_2")
            upscroll = self.game.settings.get("upscroll")
            
            hit_color = col_inner
            if lane in [0, 3]: hit_color = col_outer
            
            if min_diff < 0.05:
                self.score += 300
                self.perfects += 1
                self.game.renderer.add_hit_effect("PERFECT", lane, upscroll, hit_color)
                self.combo += 1
            elif min_diff < 0.1:
                self.score += 100
                self.goods += 1
                self.game.renderer.add_hit_effect("GREAT", lane, upscroll, hit_color)
                self.combo += 1
            else:
                self.score += 50
                self.bads += 1
                self.game.renderer.add_hit_effect("BAD", lane, upscroll, (255, 50, 50)) # Miss/Bad stays Red
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
             self.game.renderer.draw_text(surface, f"SYNCING... {left:.1f}", 400, 300, TERM_AMBER)
             return
             
        if self.paused:
            self.game.renderer.draw_text(surface, "PAUSED", 450, 300, TERM_RED)
            self.game.renderer.draw_text(surface, "PRESS SPACE TO RESUME", 380, 350, TERM_WHITE)
            self.game.renderer.draw_text(surface, "PRESS ESC TO QUIT", 400, 400, TERM_WHITE)
            return

        speed = self.game.settings.get("speed")
        upscroll = self.game.settings.get("upscroll")
        speed = self.game.settings.get("speed")
        upscroll = self.game.settings.get("upscroll")
        
        self.game.renderer.draw_lanes(surface, upscroll, pulse=self.beat_pulse)
        self.game.renderer.draw_notes(surface, self.beatmap, self.game.audio.get_position(), speed, upscroll)
        self.game.renderer.draw_effects(surface)
        
        # Progress Bar
        self.game.renderer.draw_progress(surface, self.game.audio.get_position(), self.duration)
        
        # HUD
        self.game.renderer.draw_text(surface, f"SCORE: {self.score}", 20, 20, TERM_WHITE)
        self.game.renderer.draw_text(surface, f"COMBO: {self.combo}", 20, 50, TERM_AMBER)
        
        # Draw Acc
        total_hits = self.perfects + self.goods + self.bads + self.misses
        if total_hits > 0:
            # Weighted: Perf=100, Good=75, Bad=50, Miss=0
            weighted = (self.perfects * 100 + self.goods * 75 + self.bads * 50)
            acc = weighted / (total_hits * 100) * 100
            self.game.renderer.draw_text(surface, f"ACC: {acc:.1f}%", 20, 80 if self.mode != 'multi' else 110, TERM_WHITE)
        
        if self.mode == 'multi':
             self.game.renderer.draw_text(surface, f"OPPONENT: {self.game.network.opponent_score}", 20, 80, TERM_RED)

        # Draw Song Info (Bottom Right)
        # Parse logic: "Artist - Title.mp3"
        display_name = self.song_name
        artist = "UNKNOWN ARTIST"
        title = display_name
        
        if " - " in display_name:
            parts = display_name.split(" - ", 1)
            artist = parts[0]
            title = parts[1].rsplit('.', 1)[0]
        else:
             title = display_name.rsplit('.', 1)[0]
             
        self.game.renderer.draw_text(surface, f"{title}", self.game.renderer.ref_w - 300, self.game.renderer.ref_h - 60, TERM_GREEN)
        self.game.renderer.draw_text(surface, f"{artist}", self.game.renderer.ref_w - 300, self.game.renderer.ref_h - 30, (100, 150, 100))

        # Progress Bar
        if self.game.audio.start_time > 0:
            # Ideally audio manager gives us duration, but we can guess or use note completion
            # Hack: simple bar at bottom
            pass
