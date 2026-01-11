import pygame
from core.scene_manager import Scene
from core.config import *
import os

class GameScene(Scene):
    def on_enter(self, params):
        # Reset input states to prevent stuck keys
        self.game.renderer.key_states = [False] * 4
        
        self.song_name = params['song']
        self.difficulty = params['difficulty']
        self.mode = params.get('mode', 'single')
        
        # Replay Init
        self.max_possible_score = 0
        self.replay_mode = params.get('replay_mode', False)
        self.replay_data = params.get('replay_data', None)
        self.replay_events = []
        import time
        self.start_time = time.time()
        self.audio_missing = False
        
        # Spectator mode - read-only watching
        self.is_spectator = getattr(self.game.network, 'is_spectator', False) if hasattr(self.game, 'network') else False
        
        # Autoplay mode
        self.autoplay = params.get('autoplay', False)
        
        # Max Score Calc
        self.max_possible_score = 0
        # Will calculate after loading beatmap
        
        # Replay Init
        self.replay_mode = params.get('replay_mode', False)
        self.replay_data = params.get('replay_data', None)
        self.replay_events = []
        if self.replay_mode and self.replay_data:
            self.replay_events = self.replay_data.get('events', [])
            # Sort just in case
            self.replay_events.sort(key=lambda x: x[0])
            self.replay_index = 0
            
        import time
        self.start_time = time.time()
        
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
            self.max_possible_score += 300
            if note.get('length', 0) > 0:
                self.max_possible_score += 150
        
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
        self.waiting_for_peer = False # Always init
        self.intro_active = True
        self.intro_timer = 0.0
        self.intro_duration = 2.0
        
        if self.mode == 'multiplayer':
            self.intro_active = False
            self.game.network.peer_finished = False # Reset peer state
            
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
        self.display_health = 100.0  # For smooth animation
        self.damage_health = 100.0   # For damage trail effect
        self.fail_anim = 0.0
        
        # HUD Visuals
        self.display_score = 0.0
        self.combo_scale = 1.0
        self.combo_color_timer = 0
        self.pause_selection = 0
        self.pause_menu = ["RESUME", "RESTART", "QUIT TO MENU"]
        
        # Hold note tracking: {lane: {'note': note_obj, 'end_time': float}}
        self.active_holds = {}
        
        # Load hit sounds
        self.sfx_hit = self._load_sfx("sfx/sfx_hit.wav", 0.5)
        self.sfx_perfect = self._load_sfx("sfx/sfx_perfect.wav", 0.4)
        self.sfx_miss = self._load_sfx("sfx/sfx_miss.wav", 0.3)

        # Parse Metadata for RPC/Display
        self.display_artist = "Unknown Artist"
        if params.get('song_title'):
             self.display_title = params.get('song_title')
             # Parse artist from title if possible, or leave as Unknown
             if " - " in self.display_title:
                 parts = self.display_title.split(" - ", 1)
                 # self.display_title is usually "Song - Artist" or "Artist - Song"?
                 # User format: "Neon Horizon - Wyind" (Title - Artist? or Song - Creator?)
                 # Let's assume the whole string is the title for display simplicity, unless split requested.
                 pass 
        else:
            self.display_title = os.path.basename(self.song_name)
            if " - " in self.display_title:
                parts = self.display_title.split(" - ", 1)
                self.display_artist = parts[0]
                self.display_title = parts[1].rsplit('.', 1)[0]
            else:
                self.display_title = self.display_title.rsplit('.', 1)[0]

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
    
    def _load_sfx(self, path, base_volume):
        if os.path.exists(path):
            snd = pygame.mixer.Sound(path)
            # Calculate final volume: Base Mix * Master * SFX
            master = self.game.settings.get("volume")
            sfx = self.game.settings.get("sfx_volume")
            final_vol = base_volume * master * sfx
            snd.set_volume(final_vol)
            return snd
        return None

    def on_exit(self):
        self.game.audio.stop()
        self.game.play_menu_bgm()
        if self.mode == 'multiplayer':
             self.game.network.start_timestamp = 0

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
            
        if self.mode == 'multiplayer' and self.rpc_timer % 10 == 0:
            self.game.network.send_score(int(self.score))
        
        # Multiplayer Finish Sync
        if self.waiting_for_peer:
            if not self.game.network.connected:
                # Disconnect -> Auto finish
                self.waiting_for_peer = False
                self.finish_game(failed=self.failed) # Re-call to proceed
                return
            
            if self.game.network.peer_finished:
                # Peer is done, we can proceed
                # Small delay to ensure they see our finished status too
                import time
                if time.time() - self.finish_time > 1.0:
                    self.waiting_for_peer = False
                    self.finish_game(failed=self.failed)
            return
            
        # --- Visual Polish Updates ---
        # 1. Rolling Score
        diff = self.score - self.display_score
        if abs(diff) > 0.1:
            self.display_score += diff * 0.2
        else:
            self.display_score = self.score
            
        # 2. Smooth Health & Damage Trail
        # Display health moves fast to target
        h_diff = self.health - self.display_health
        if abs(h_diff) > 0.1:
            self.display_health += h_diff * 0.2
        else:
            self.display_health = self.health
            
        # Damage health moves slower (trail effect)
        if self.damage_health > self.display_health:
            self.damage_health -= 0.5  # Linear decay
        elif self.damage_health < self.display_health:
            self.damage_health = self.display_health # Snap up immediately on heal
            
        # 3. Combo Pulse Decay
        if self.combo_scale > 1.0:
            self.combo_scale -= 0.05
        # -----------------------------
            
        offset_ms = self.game.settings.get("audio_offset")
        current_time = self.game.audio.get_position() - (offset_ms / 1000.0)
        self.game.renderer.update_effects()
        
        # Pulse Calculation
        spb = 60.0 / self.bpm
        beat_prog = (current_time % spb) / spb
        self.beat_pulse = pow(1.0 - beat_prog, 4)
        
        self.beat_pulse = pow(1.0 - beat_prog, 4)
        
        # Replay Playback Logic
        if self.replay_mode and not self.paused and not self.finished:
            # watermark
            self.game.renderer.draw_text(self.game.screen, "REPLAY MODE", 10, 10, (255, 0, 0))
            
            while self.replay_index < len(self.replay_events):
                evt = self.replay_events[self.replay_index]
                e_time, lane, state = evt[0], evt[1], evt[2]
                
                # Check if it's time (with small offset window)
                if e_time <= current_time:
                    # Execute
                    if state == 1: # Press
                         self.handle_hit_lane(lane, replay=True)
                         self.game.renderer.key_states[lane] = True
                    else: # Release
                         self.handle_release_lane(lane)
                         self.game.renderer.key_states[lane] = False
                    
                    self.replay_index += 1
                else:
                    break
        
        # Autoplay Logic
        if self.autoplay and not self.paused and not self.failed and not self.finished:
            for note in self.beatmap:
                if not note['hit']:
                    diff = note['time'] - current_time
                    # Hit slightly early for "perfect" feel or just on time
                    if diff <= 0.0:
                        self.handle_hit_lane(note['lane'], target_note=note)
                        # Release holds automatically
                        if note.get('length', 0) > 0:
                            # We need to simulate holding key
                            self.game.renderer.key_states[note['lane']] = True
        
        # Autoplay Hold Releases
        if self.autoplay:
             current_time = self.game.audio.get_position()
             offset_ms = self.game.settings.get("audio_offset") or 0
             current_time += offset_ms / 1000.0
             for lane, hold in list(self.active_holds.items()):
                 if current_time >= hold['end_time']:
                     self.handle_release_lane(lane)
                     self.game.renderer.key_states[lane] = False
                     
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
        # Ignore gameplay input if autoplay is on (but allow pause)
        if self.autoplay and event.type in [pygame.KEYDOWN, pygame.KEYUP]:
            if event.key not in [pygame.K_ESCAPE, pygame.K_UP, pygame.K_DOWN, pygame.K_RETURN, pygame.K_SPACE]:
                return

        if event.type == pygame.KEYDOWN:
            # Handle pause menu input when paused
            if self.paused:
                if event.key == pygame.K_UP:
                    self.pause_selection = (self.pause_selection - 1) % len(self.pause_menu)
                elif event.key == pygame.K_DOWN:
                    self.pause_selection = (self.pause_selection + 1) % len(self.pause_menu)
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    selected = self.pause_menu[self.pause_selection]
                    if selected == "RESUME":
                        self.toggle_pause()
                    elif selected == "RESTART":
                        params = {
                            'song': self.song_name,
                            'difficulty': self.difficulty,
                            'mode': self.mode
                        }
                        self.game.audio.stop()
                        from scenes.game_scene import GameScene
                        self.game.scene_manager.switch_to(GameScene, params)
                        return
                    elif selected == "QUIT TO MENU":
                        from scenes.menu_scenes import SongSelectScene
                        self.game.scene_manager.switch_to(SongSelectScene)
                        return
                elif event.key == pygame.K_ESCAPE:
                    # ESC while paused also quits
                    from scenes.menu_scenes import SongSelectScene
                    self.game.scene_manager.switch_to(SongSelectScene)
                    return
                return  # Don't process other input while paused
            
            # Normal gameplay input
            if event.key == pygame.K_ESCAPE:
                if self.audio_missing or (self.mode == 'multiplayer' and not self.game.network.connected):
                    from scenes.menu_scenes import SongSelectScene
                    # If disconnected, probably best to go to Title or Lobby? 
                    # Going to SongSelectScene resets flow, which is fine.
                    self.game.scene_manager.switch_to(SongSelectScene)
                    return
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
                # Block note hits for spectators
                if not getattr(self, 'is_spectator', False):
                    self.handle_hit(event.key)
        elif event.type == pygame.KEYUP:
            if not self.paused and not getattr(self, 'is_spectator', False):
                # print(f"DEBUG: GameScene KEYUP {event.key}")
                self.update_key(event.key, False)

    def toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            self.game.audio.pause()
            self.pause_selection = 0  # Reset selection
            self.pause_menu = ["RESUME", "RESTART", "QUIT TO MENU"]
        else:
            self.game.audio.unpause()

    def change_volume(self, change):
        vol = self.game.settings.get("volume")
        vol = max(0.0, min(1.0, vol + change))
        self.game.settings.set("volume", vol)
        
        # Update Music
        self.game.audio.update_volumes()
        
        # Update SFX immediately
        sfx_vol = self.game.settings.get("sfx_volume")
        if self.sfx_hit: self.sfx_hit.set_volume(0.5 * vol * sfx_vol)
        if self.sfx_perfect: self.sfx_perfect.set_volume(0.4 * vol * sfx_vol)
        if self.sfx_miss: self.sfx_miss.set_volume(0.3 * vol * sfx_vol)

    def update_key(self, key, pressed):
        keys = self.game.settings.get("keybinds")
        if key in keys:
            lane = keys.index(key)
            self.game.renderer.key_states[lane] = pressed
            # Handle hold note release
            if not pressed:
                if not self.autoplay and not self.replay_mode:
                    t = self.game.audio.get_position()
                    self.replay_events.append([t, lane, 0]) # 0 = Up
                    
                self.handle_release_lane(lane)

    def handle_hit(self, key):
        keys = self.game.settings.get("keybinds")
        if key not in keys:
            return
        lane = keys.index(key)
        self.handle_hit_lane(lane)

    def handle_hit_lane(self, lane, target_note=None, replay=False):
        # In replay mode, input is already validated by the recording
        if self.replay_mode and not replay: return
        
        if not self.autoplay and not self.replay_mode:
            # Record Event
            t = self.game.audio.get_position()
            self.replay_events.append([t, lane, 1]) # 1 = Down
            
        self.game.renderer.key_states[lane] = True
        
        current_time = self.game.audio.get_position()
        offset_ms = self.game.settings.get("audio_offset") or 0
        current_time += offset_ms / 1000.0
        
        closest = None
        min_diff = 1.0
        
        if target_note:
            closest = target_note
            min_diff = 0.0
        else:
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
                self.combo_scale = 1.3  # Pulse
                if hit_sounds_enabled and self.sfx_perfect:
                    self.sfx_perfect.play()
            elif min_diff < 0.1:
                self.score += 100
                self.goods += 1
                self.health = min(self.max_health, self.health + 2.0)
                self.game.renderer.add_hit_effect("GREAT", lane, upscroll, hit_color)
                self.combo += 1
                self.combo_scale = 1.2  # Pulse
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
        # Multiplayer Sync: Wait for other player
        if self.mode == 'multiplayer' and not self.waiting_for_peer:
            # First time calling finish_game
            self.finished = True
            if failed: self.failed = True
            
            # Send signal
            self.game.network.send_game_finished(failed=self.failed, score=int(self.score))
            
            if not self.game.network.peer_finished:
                self.waiting_for_peer = True
                import time
                self.finish_time = time.time()
                return # Stop here, wait for update loop
        
        self.finished = True
        
        # Save Replay & Submit Score (Unified Logic)
        if not self.replay_mode and not self.autoplay and not getattr(self, 'is_spectator', False):
            # Only save if not failed? Or allow failed replays?
            # User said "bunch of replays", implying too many.
            # Let's save ONLY if valid completion for now, or maybe just once.
            # The previous code called it TWICE.
            self.save_replay()
            
            # Submit score if NOT failed
            if not (failed or self.failed):
                 if self.game.master_client.logged_in:
                     import threading
                     def submit():
                         self.game.master_client.submit_score(int(self.score), max_score=self.max_possible_score)
                     threading.Thread(target=submit, daemon=True).start()
                 
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
            'autoplay': self.autoplay,
            'next_scene_class': self.next_scene_class,
            'next_scene_params': self.next_scene_params
        })

    def save_replay(self):
        import json
        import datetime
        
        if not os.path.exists("replays"):
            os.makedirs("replays")
            
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"replays/{self.song_name}_{timestamp}.turr"
        
        data = {
            "version": 1,
            "song": self.song_name,
            "difficulty": self.difficulty,
            "score": self.score,
            "max_combo": self.max_combo,
            "timestamp": timestamp,
            "events": self.replay_events
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(data, f)
            print(f"Replay saved to {filename}")
        except Exception as e:
            print(f"Failed to save replay: {e}") 

    def draw(self, surface):
        r = self.game.renderer
        theme = r.get_theme()

        if self.audio_missing:
            surface.fill((0, 0, 0))
            self.game.renderer.draw_panel(surface, 300, 300, 424, 150, "SYSTEM ERROR", color=(50, 0, 0))
            self.game.renderer.draw_centered_text(surface, "AUDIO FILE NOT FOUND", 512, 360, theme["error"])
            self.game.renderer.draw_centered_text(surface, "[ESC] TO EXIT", 512, 400, (150, 150, 150))
            return
        
        if self.waiting_for_sync:
            import time
            left = max(0, self.start_time - time.time())
            self.game.renderer.draw_text(surface, f"SYNCING... {left:.1f}", 400, 300, TERM_AMBER)
            self.game.renderer.draw_text(surface, f"SYNCING... {left:.1f}", 400, 300, TERM_AMBER)
            return

        if self.waiting_for_peer:
            # Draw game behind
            pass # Continue to draw game elements
            
            # Overlay
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.fill((0, 0, 0))
            overlay.set_alpha(150)
            surface.blit(overlay, (0, 0))
            
            r.draw_panel(surface, 300, 250, 424, 150, "MULTIPLAYER")
            
            status = "FAILED" if self.failed else "FINISHED"
            col = theme["error"] if self.failed else theme["primary"]
            r.draw_text(surface, f"{status}", 460, 290, col)
            
            blink = "." * ((pygame.time.get_ticks() // 500) % 4)
            r.draw_text(surface, f"Waiting for opponent{blink}", 350, 340, (200, 200, 200))
            
            p_score = self.game.network.peer_final_score or self.game.network.opponent_score
            r.draw_text(surface, f"Opponent Score: {p_score}", 350, 370, theme["secondary"])
            return
             
        if self.paused:
            # Dim background
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.fill((10, 10, 20))
            overlay.set_alpha(200)
            surface.blit(overlay, (0, 0))
            
            # Draw stylized pause menu
            panel_w = 300
            panel_h = len(self.pause_menu) * 50 + 80
            panel_x = (SCREEN_WIDTH - panel_w) // 2
            panel_y = (SCREEN_HEIGHT - panel_h) // 2
            
            r.draw_panel(surface, panel_x, panel_y, panel_w, panel_h, "PAUSED")
            
            y = panel_y + 40
            for i, item in enumerate(self.pause_menu):
                selected = (i == self.pause_selection)
                # Use styled buttons
                r.draw_button(surface, item, panel_x + 20, y, selected, width=panel_w - 40)
                y += 50
                
            # Info/Help - Draw BELOW the panel to allow proper full-width display
            # y is currently inside panel logic, let's calculate bottom
            bottom_y = panel_y + panel_h + 30 
            
            # Draw standard "Song:" text
            # Use full display title, limited only by screen width (which is plenty)
            # Or truncate loosely if huge
            d_title = self.display_title
            if len(d_title) > 60: d_title = d_title[:57] + ".."
            
            # Draw with shadow for visibility against game bg
            r.draw_centered_text(surface, f"Song: {d_title}", SCREEN_WIDTH // 2, bottom_y, (255, 255, 255), r.font)
            return

        if self.mode == 'multiplayer' and not self.game.network.connected:
             # Disconnect overlay
             overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
             overlay.fill((0, 0, 0))
             overlay.set_alpha(200)
             surface.blit(overlay, (0, 0))
             
             self.game.renderer.draw_panel(surface, 300, 300, 424, 150, "DISCONNECTED", color=(50, 0, 0))
             self.game.renderer.draw_centered_text(surface, "Connection to peer lost.", 512, 350, theme["error"])
             self.game.renderer.draw_centered_text(surface, "[ESC] Return to Menu", 512, 390, (150, 150, 150))
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
        
        # HUD: Score & Combo
        # Rolling Score
        formatted_score = f"{int(self.display_score):,}"
        r.draw_text(surface, f"{formatted_score}", 20, 20, TERM_WHITE)
        r.draw_text(surface, "SCORE", 20, 45, (100, 100, 100), r.small_font)
        
        # Bouncy Combo
        if self.combo > 0:
            # Calculate bounce offset
            bounce_y = 0
            if self.combo_scale > 1.0:
                 bounce_y = (self.combo_scale - 1.0) * -10
            
            combo_col = TERM_AMBER
            if self.combo >= 50: combo_col = (255, 200, 50)
            if self.combo >= 100: combo_col = (50, 255, 255)
            
            if self.combo >= 100: combo_col = (50, 255, 255)
            
            # Moved down to Y=150 to avoid overlap with Opponent Score (at Y=80)
            base_y = 150
            r.draw_text(surface, f"{self.combo}x", 20, base_y + bounce_y, combo_col, r.big_font)
            r.draw_text(surface, "COMBO", 20, base_y + 35 + bounce_y, (100, 100, 100), r.small_font)
        
        # Spectator indicator
        if getattr(self, 'is_spectator', False):
            self.game.renderer.draw_text(surface, "◉ SPECTATING ◉", SCREEN_WIDTH - 200, 20, (255, 200, 50), self.game.renderer.font)
            
        if self.autoplay:
             # Semi-transparent watermark
             txt = "AUTOPLAY MODE"
             font = self.game.renderer.big_font
             tw, th = font.size(txt)
             
             # Draw with low alpha (requires blitting surface)
             s = pygame.Surface((tw + 20, th + 10), pygame.SRCALPHA)
             s.fill((0, 0, 0, 100))
             pygame.draw.rect(s, (255, 50, 50, 100), (0, 0, tw + 20, th + 10), 2)
             
             # Manually render text to surface
             t_surf = font.render(txt, True, (255, 50, 50))
             t_surf.set_alpha(150)
             s.blit(t_surf, (10, 5))
             
             surface.blit(s, ((SCREEN_WIDTH - tw)//2, SCREEN_HEIGHT - 150))
        
        # Smooth Health Bar
        bar_w = 400
        bar_h = 10
        bar_x = (SCREEN_WIDTH - bar_w) // 2
        bar_y = 30 # Moved up slightly
        
        # Background
        pygame.draw.rect(surface, (30, 30, 30), (bar_x, bar_y, bar_w, bar_h))
        
        # Damage Trail (Red)
        damage_w = int(bar_w * (self.damage_health / 100.0))
        pygame.draw.rect(surface, (150, 50, 50), (bar_x, bar_y, damage_w, bar_h))
        
        # Main Health (Green -> Red)
        main_w = int(bar_w * (self.display_health / 100.0))
        hp_color = (0, 255, 100) 
        if self.display_health < 30: hp_color = (255, 50, 50)
        elif self.display_health < 60: hp_color = (255, 200, 0)
        
        pygame.draw.rect(surface, hp_color, (bar_x, bar_y, main_w, bar_h))
        
        # Glow/Border
        pygame.draw.rect(surface, (100, 100, 100), (bar_x, bar_y, bar_w, bar_h), 1)
        
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
            self.game.renderer.draw_text(surface, f"ACC: {acc:.1f}%", 20, 80 if self.mode != 'multiplayer' else 110, TERM_WHITE)
        
        if self.mode == 'multiplayer':
            self.game.renderer.draw_text(surface, f"OPPONENT: {self.game.network.opponent_score}", 20, 80, TERM_RED)

        # Draw Song Info (Bottom Right)
        # Draw Song Info (Bottom Right - Right Aligned)
        d_title = self.display_title
        font = self.game.renderer.font
        tw, th = font.size(d_title)
        tx = self.game.renderer.ref_w - 20 - tw # Right align with 20px padding
        
        self.game.renderer.draw_text(surface, d_title, tx, self.game.renderer.ref_h - 60, TERM_GREEN)
    def save_replay(self):
        import json
        import datetime
        
        if not os.path.exists("replays"):
            os.makedirs("replays")
            
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"replays/{self.song_name}_{timestamp}.turr"
        
        data = {
            "version": 1,
            "song": self.song_name,
            "difficulty": self.difficulty,
            "score": self.score,
            "max_combo": self.max_combo,
            "timestamp": timestamp,
            "events": self.replay_events
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(data, f)
            print(f"Replay saved to {filename}")
        except Exception as e:
            print(f"Failed to save replay: {e}") 
