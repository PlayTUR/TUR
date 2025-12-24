import pygame
from core.scene_manager import Scene
from core.config import *
import os

class GameScene(Scene):
    def on_enter(self, params):
        self.song_name = params['song']
        self.difficulty = params['difficulty']
        self.mode = params.get('mode', 'single')
        self.audio_missing = False
        
        # Store for story continuation
        self.next_scene_class = params.get('next_scene_class')
        self.next_scene_params = params.get('next_scene_params')
        
        # Path handling: story mode passes full paths, single player just filename
        if self.mode == 'story' or os.path.exists(self.song_name):
            path = self.song_name
        else:
            path = os.path.join("songs", self.song_name)
        
        # Load map
        map_data = self.game.generator.get_beatmap(path, self.difficulty)
        
        if isinstance(map_data, list):
            self.beatmap = map_data
            self.events = []
            self.bpm = 120.0
            self.duration = 180.0
            audio_source = path
        else:
            self.beatmap = map_data.get('notes', [])
            self.events = map_data.get('events', [])
            # Sort events
            self.events.sort(key=lambda x: x['time'])
            self.bpm = map_data.get('bpm', 120.0)
            self.duration = map_data.get('duration', 180.0)
            audio_source = map_data.get('audio_path', path)

        for note in self.beatmap:
            note['hit'] = False
        
        self.beat_pulse = 0.0
        
        # Discord RPC
        title = os.path.basename(path)
        if isinstance(map_data, dict):
            title = map_data.get('title', title)
        
        from core.utils import find_resource
        resolved_audio = find_resource(audio_source, hint_dirs=["songs", os.path.dirname(path)])
        
        if resolved_audio:
            try:
                self.game.audio.load_song(resolved_audio)
                vol = self.game.settings.get("volume")
                self.game.audio.set_volume(vol)
            except Exception as e:
                print(f"ERROR: Could not load resolved audio {resolved_audio}: {e}")
                self.audio_missing = True
        else:
            print(f"CRITICAL: Audio file not found for {self.song_name}")
            self.audio_missing = True
        
        # Intro / Sync Logic
        self.waiting_for_sync = False
        self.intro_active = True
        self.intro_timer = 0.0
        self.intro_duration = 2.0
        
        if self.mode == 'multi':
            self.intro_active = False
            if self.game.network.is_host:
                self.start_time = self.game.network.start_game_request()
                self.waiting_for_sync = True
            else:
                self.start_time = self.game.network.start_timestamp
                self.waiting_for_sync = True
                if self.start_time == 0:
                    self.waiting_for_sync = True

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
        self.failed = False
        
        # Health System
        self.health = 100.0
        self.max_health = 100.0
        self.fail_anim = 0.0
        
        # Hold note tracking: {lane: {'note': note_obj, 'end_time': float}}
        self.active_holds = {}
        
        # Load hit sounds
        self.sfx_hit = self._load_sfx("sfx/sfx_hit.wav", 0.5)
        self.sfx_perfect = self._load_sfx("sfx/sfx_perfect.wav", 0.4)
        self.sfx_miss = self._load_sfx("sfx/sfx_miss.wav", 0.3)

        # Parse Metadata for RPC/Display
        self.display_artist = "Unknown Artist"
        self.display_title = self.song_name
        if " - " in self.song_name:
            parts = self.song_name.split(" - ", 1)
            self.display_artist = parts[0]
            self.display_title = parts[1].rsplit('.', 1)[0]
        else:
            self.display_title = self.song_name.rsplit('.', 1)[0]

        # Initial RPC Update
        self.game.discord.update(
            details=self.display_title,
            state=f"{self.display_artist} | {self.difficulty} | Score: 0"
        )
        self.rpc_timer = 0
        
        # Event system initialization
        self.event_index = 0
        self.song_time = 0.0
        self.base_scroll_speed = 500.0  # Base speed in pixels per second
        self.scroll_speed = self.base_scroll_speed
    
    def _load_sfx(self, path, volume):
        if os.path.exists(path):
            snd = pygame.mixer.Sound(path)
            snd.set_volume(volume)
            return snd
        return None

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
                if not self.game.network.is_host and self.game.network.start_timestamp > 0:
                    self.start_time = self.game.network.start_timestamp
                return
        
        # Intro Logic
        if self.intro_active:
            self.intro_timer += 1.0 / 60.0
            if self.intro_timer >= self.intro_duration:
                self.intro_active = False
                if not self.paused:
                    self.game.audio.play()
            return

        if self.paused:
            return

        # Check if song finished naturally
        music_playing = pygame.mixer.music.get_busy()
        if not music_playing and not self.finished and not self.waiting_for_sync and not self.intro_active:
            self.finish_game()
            return
        
        # In story mode, finish when all notes are done (don't wait for full song)
        if self.mode == 'story' and not self.finished:
            all_notes_done = all(n['hit'] for n in self.beatmap)
            if all_notes_done and self.beatmap:
                # Get the last note time and wait 2 seconds after it
                last_note_time = max(n.get('end_time', n['time']) for n in self.beatmap)
                current_time = self.game.audio.get_position()
                if current_time > last_note_time + 2.0:
                    self.finish_game()
                    return

        if self.failed:
            self.fail_anim += 1.0 / 60.0 * 2
            if self.fail_anim >= 1.0:
                self.finish_game(failed=True)
            return

        # RPC Update (Periodic)
        self.rpc_timer += 1
        if self.rpc_timer >= 600: # ~10 seconds
             self.rpc_timer = 0
             self.game.discord.update(
                details=self.display_title,
                state=f"{self.display_artist} | {self.difficulty} | Score: {int(self.score)}"
             )
            
        offset_ms = self.game.settings.get("audio_offset")
        current_time = self.game.audio.get_position() - (offset_ms / 1000.0)
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
                self.health -= 15.0
                self.game.renderer.add_hit_effect("MISS", note['lane'])

        # Fail Check
        if self.health <= 0:
            self.health = 0
            if not self.failed:
                self.failed = True
                self.game.audio.stop()
                if hasattr(self.game.renderer, 'play_sfx'):
                    self.game.renderer.play_sfx("error")

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.audio_missing:
                    from scenes.menu_scenes import SongSelectScene
                    self.game.scene_manager.switch_to(SongSelectScene)
                    return
                if self.paused:
                    from scenes.menu_scenes import SongSelectScene
                    self.game.scene_manager.switch_to(SongSelectScene)
                else:
                    self.toggle_pause()
            elif event.key == pygame.K_SPACE or event.key == pygame.K_p:
                self.toggle_pause()
            elif event.key == pygame.K_r:
                params = {
                    'song': self.song_name,
                    'difficulty': self.difficulty,
                    'mode': self.mode
                }
                self.game.audio.stop()
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

    def update_key(self, key, pressed):
        keys = self.game.settings.get("keybinds")
        if key in keys:
            lane = keys.index(key)
            self.game.renderer.key_states[lane] = pressed
            # Handle hold note release
            if not pressed:
                self.handle_release_lane(lane)

    def handle_hit(self, key):
        keys = self.game.settings.get("keybinds")
        if key not in keys:
            return
        lane = keys.index(key)
        self.handle_hit_lane(lane)

    def handle_hit_lane(self, lane, is_autoplay=False):
        self.game.renderer.key_states[lane] = True
        
        current_time = self.game.audio.get_position()
        offset_ms = self.game.settings.get("audio_offset") or 0
        current_time += offset_ms / 1000.0
        
        closest = None
        min_diff = 1.0
        
        for note in self.beatmap:
            if note['lane'] == lane and not note['hit']:
                diff = note['time'] - current_time
                if abs(diff) < min_diff:
                    min_diff = abs(diff)
                    closest = note
        
        if closest and min_diff < 0.20:
            closest['hit'] = True
            
            # Track hold notes for release scoring
            note_length = closest.get('length', 0)
            if note_length > 0:
                self.active_holds[lane] = {
                    'note': closest,
                    'end_time': closest['time'] + note_length
                }
            
            col_inner = self.game.settings.get("note_col_1")
            col_outer = self.game.settings.get("note_col_2")
            upscroll = self.game.settings.get("upscroll")
            hit_sounds_enabled = self.game.settings.get("hit_sounds")
            
            hit_color = col_inner
            if lane in [0, 3]:
                hit_color = col_outer
            
            # Get post-effects setting
            post_effects = self.game.settings.get("post_effects")
            
            if min_diff < 0.06:
                self.score += 300
                self.perfects += 1
                self.health = min(self.max_health, self.health + 5.0)
                self.game.renderer.add_hit_effect("PERFECT", lane, upscroll, hit_color)
                self.combo += 1
                if hit_sounds_enabled and self.sfx_perfect:
                    self.sfx_perfect.play()
            elif min_diff < 0.1:
                self.score += 100
                self.goods += 1
                self.health = min(self.max_health, self.health + 2.0)
                self.game.renderer.add_hit_effect("GREAT", lane, upscroll, hit_color)
                self.combo += 1
                if hit_sounds_enabled and self.sfx_hit:
                    self.sfx_hit.play()
            else:
                self.score += 50
                self.bads += 1
                self.health -= 5.0
                self.game.renderer.add_hit_effect("BAD", lane, upscroll, (255, 50, 50))
                self.combo = 0
                if hit_sounds_enabled and self.sfx_hit:
                    self.sfx_hit.play()
                # Post-effects removed for bad hits (flash can cause seizures)
            
            if self.combo > self.max_combo:
                self.max_combo = self.combo
    
    def handle_release_lane(self, lane):
        """Handle key release for hold notes - score based on release timing like osu"""
        if lane not in self.active_holds:
            return
        
        hold_info = self.active_holds.pop(lane)
        end_time = hold_info['end_time']
        
        current_time = self.game.audio.get_position()
        offset_ms = self.game.settings.get("audio_offset") or 0
        current_time += offset_ms / 1000.0
        
        # Calculate timing difference from hold end
        diff = abs(end_time - current_time)
        
        upscroll = self.game.settings.get("upscroll")
        col_inner = self.game.settings.get("note_col_1")
        col_outer = self.game.settings.get("note_col_2")
        hit_sounds_enabled = self.game.settings.get("hit_sounds")
        
        hit_color = col_inner if lane in [1, 2] else col_outer
        
        # Score the release timing (same windows as hit)
        if diff < 0.06:
            # Perfect release
            self.score += 150  # Bonus for perfect release
            self.perfects += 1
            self.health = min(self.max_health, self.health + 3.0)
            self.game.renderer.add_hit_effect("PERFECT", lane, upscroll, hit_color)
            self.combo += 1
            if hit_sounds_enabled and self.sfx_perfect:
                self.sfx_perfect.play()
        elif diff < 0.12:
            # Good release
            self.score += 75
            self.goods += 1
            self.health = min(self.max_health, self.health + 1.0)
            self.game.renderer.add_hit_effect("GREAT", lane, upscroll, hit_color)
            self.combo += 1
            if hit_sounds_enabled and self.sfx_hit:
                self.sfx_hit.play()
        elif diff < 0.20:
            # Early/late release - bad
            self.score += 25
            self.bads += 1
            self.health -= 3.0
            self.game.renderer.add_hit_effect("BAD", lane, upscroll, (255, 50, 50))
            self.combo = 0
        else:
            # Too early release - miss
            self.misses += 1
            self.health -= 10.0
            self.game.renderer.add_hit_effect("MISS", lane, upscroll)
            self.combo = 0
        
        if self.combo > self.max_combo:
            self.max_combo = self.combo
            
    def break_combo(self):
        self.combo = 0

    def finish_game(self, failed=False):
        self.finished = True
        from scenes.result_scene import ResultScene
        self.game.scene_manager.switch_to(ResultScene, {
            'score': self.score,
            'max_combo': self.max_combo,
            'perfects': self.perfects,
            'goods': self.goods,
            'bads': self.bads,
            'misses': self.misses,
            'song': self.song_name,
            'difficulty': self.difficulty,
            'failed': failed or self.failed,
            'mode': self.mode,
            'next_scene_class': self.next_scene_class,
            'next_scene_params': self.next_scene_params
        })

    def draw(self, surface):
        if self.audio_missing:
            surface.fill((0, 0, 0))
            self.game.renderer.draw_panel(surface, 300, 300, 400, 150, "SYSTEM ERROR")
            self.game.renderer.draw_text(surface, "AUDIO FILE NOT FOUND", 320, 340, (255, 50, 50))
            self.game.renderer.draw_text(surface, "[ESC] TO EXIT", 320, 380, (150, 150, 150))
            return

        r = self.game.renderer
        theme = r.get_theme()
        
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

        if self.failed:
            if (pygame.time.get_ticks() // 100) % 2 == 0:
                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                overlay.fill((255, 0, 0))
                overlay.set_alpha(100)
                surface.blit(overlay, (0, 0))
            self.game.renderer.draw_text(surface, "SYSTEM_FAILURE_DETECTION", 250, 300, (255, 50, 50), self.game.renderer.big_font)
            self.game.renderer.draw_text(surface, "KERNEL PANIC: UNRECOVERABLE_INPUT_DECAY", 270, 380, (255, 255, 255))
            return

        speed = self.game.settings.get("speed")
        upscroll = self.game.settings.get("upscroll")
        
        self.game.renderer.draw_lanes(surface, upscroll, pulse=self.beat_pulse)
        self.game.renderer.draw_notes(surface, self.beatmap, self.game.audio.get_position(), speed, upscroll)
        self.game.renderer.draw_effects(surface)
        
        # Apply post-processing effects (flash)
        if self.game.settings.get("post_effects"):
            self.game.renderer.apply_post_effects(surface)
        
        # Progress Bar
        self.game.renderer.draw_progress(surface, self.game.audio.get_position(), self.duration)
        
        # HUD
        self.game.renderer.draw_text(surface, f"SCORE: {self.score}", 20, 20, TERM_WHITE)
        self.game.renderer.draw_text(surface, f"COMBO: {self.combo}", 20, 50, TERM_AMBER)
        
        # Health Bar
        bar_w = 400
        bar_h = 10
        bar_x = (SCREEN_WIDTH - bar_w) // 2
        bar_y = 70
        pygame.draw.rect(surface, (50, 50, 50), (bar_x, bar_y, bar_w, bar_h))
        hp_color = (0, 255, 100) if self.health > 30 else (255, 180, 0) if self.health > 15 else (255, 50, 50)
        pygame.draw.rect(surface, hp_color, (bar_x, bar_y, int(bar_w * (self.health / 100.0)), bar_h))
        pygame.draw.rect(surface, (200, 200, 200), (bar_x, bar_y, bar_w, bar_h), 1)
        
        # Update song time for event processing
        self.song_time = self.game.audio.get_position()
        
        # Process Events
        while self.event_index < len(self.events):
            ev = self.events[self.event_index]
            if ev['time'] <= self.song_time:
                # Trigger Event
                if ev['type'] == EVENT_CAMERA_ZOOM:
                    self.game.renderer.trigger_zoom(ev.get('value', 1.0), ev.get('duration', 1.0))
                elif ev['type'] == EVENT_CAMERA_SHAKE:
                    self.game.renderer.trigger_shake(ev.get('intensity', 5.0))
                elif ev['type'] == EVENT_NOTE_GLOW:
                    self.game.renderer.trigger_glow(ev.get('color', (0, 255, 0)), ev.get('duration', 30))
                elif ev['type'] == EVENT_SPEED_CHANGE:
                    self.scroll_speed = self.base_scroll_speed * ev.get('multiplier', 1.0)
                
                self.event_index += 1
            else:
                break
        
        # Spawn Notes
        spawn_time = self.song_time + (SCREEN_HEIGHT / self.scroll_speed)
        
        # Draw Acc
        total_hits = self.perfects + self.goods + self.bads + self.misses
        if total_hits > 0:
            weighted = (self.perfects * 100 + self.goods * 75 + self.bads * 50)
            acc = weighted / (total_hits * 100) * 100
            self.game.renderer.draw_text(surface, f"ACC: {acc:.1f}%", 20, 80 if self.mode != 'multi' else 110, TERM_WHITE)
        
        if self.mode == 'multi':
            self.game.renderer.draw_text(surface, f"OPPONENT: {self.game.network.opponent_score}", 20, 80, TERM_RED)

        # Draw Song Info (Bottom Right)
        self.game.renderer.draw_text(surface, f"{self.display_title}", self.game.renderer.ref_w - 300, self.game.renderer.ref_h - 60, TERM_GREEN)
        self.game.renderer.draw_text(surface, f"{self.display_artist}", self.game.renderer.ref_w - 300, self.game.renderer.ref_h - 30, (100, 150, 100))
