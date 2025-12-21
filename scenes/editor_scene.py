import pygame
import math
import json
import os
from core.scene_manager import Scene
from core.config import *

class EditorScene(Scene):
    def on_enter(self, params):
        self.song_name = params['song']
        self.difficulty = params['difficulty']
        self.path = os.path.join("songs", self.song_name)
        
        # Load existing data
        self.beatmap = self.game.generator.get_beatmap(self.path, self.difficulty)
        # We work on a copy logic? The generator caches it. We should probably reload or save explicitly.
        # beatmap is a list of dicts. We can modify it in place and save logic later.
        
        self.game.audio.load_song(self.path)
        # Don't play yet, pause
        self.paused = True
        self.audio_pos = 0.0
        self.scroll_speed = 100 # Time scale for editor
        self.zoom = 100 # Pixels per second in editor view
        
        self.selected_lane = 0
        self.grid_snap = 0.25 # seconds

    def update(self):
        if not self.paused:
            # We can't rely on audio.get_pos if we want precise scrub
            # But for playback we do.
            if not self.game.audio.is_playing:
                self.paused = True
            self.audio_pos = self.game.audio.get_position()
            
    def draw(self, surface):
        surface.fill(BLACK)
        
        # Draw Timeline
        center_x = SCREEN_WIDTH // 2
        
        # Time Indicator
        self.game.renderer.draw_text(surface, f"TIME: {self.audio_pos:.2f}s", 10, 10, TERM_WHITE)
        self.game.renderer.draw_text(surface, f"SNAP: {self.grid_snap}s | ZOOM: {self.zoom}", 10, 30, TERM_WHITE)
        self.game.renderer.draw_text(surface, "[SPACE] PLAY/PAUSE | [S] SAVE | [CLICK] PLACE/REMOVE", 10, 700, TERM_AMBER)
        
        # Draw notes relative to center line (which is current time)
        # Let's say center Y is current time.
        timeline_y = SCREEN_HEIGHT // 2
        pygame.draw.line(surface, TERM_RED, (0, timeline_y), (SCREEN_WIDTH, timeline_y), 2)
        
        # Lanes
        lane_w = 80
        start_x = center_x - (2 * lane_w)
        
        for i in range(4):
            x = start_x + i * lane_w
            pygame.draw.rect(surface, (30, 30, 30), (x, 0, lane_w, SCREEN_HEIGHT), 1)
            self.game.renderer.draw_text(surface, f"L{i}", x + 30, timeline_y + 10, (100, 100, 100))

        # Draw Notes
        # y = timeline_y - (note_time - audio_pos) * zoom
        for note in self.beatmap:
            diff = note['time'] - self.audio_pos
            if diff < -5 or diff > 5: continue # optimization
            
            y = timeline_y - (diff * self.zoom)
            x = start_x + note['lane'] * lane_w
            
            col = TERM_GREEN
            pygame.draw.rect(surface, col, (x + 5, y - 10, lane_w - 10, 20))

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.audio.stop()
                from scenes.menu_scenes import SongSelectScene
                self.game.scene_manager.switch_to(SongSelectScene)
            elif event.key == pygame.K_SPACE:
                self.toggle_playback()
            elif event.key == pygame.K_s:
                self.save_map()
            elif event.key == pygame.K_UP:
                self.zoom += 10
            elif event.key == pygame.K_DOWN:
                self.zoom = max(10, self.zoom - 10)
            elif event.key == pygame.K_LEFT:
                self.audio_pos = max(0, self.audio_pos - 1)
                if self.game.audio.is_playing:
                     # Seek is hard in pygame mixer without restarting
                     pass 
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Left Click
                self.handle_click(event.pos)
            elif event.button == 4: # Scroll Up
                self.audio_pos = max(0, self.audio_pos - 0.5)
            elif event.button == 5:
                self.audio_pos += 0.5

    def toggle_playback(self):
        if self.paused:
            self.game.audio.stop() # Reset
            # Pygame mixer can't seek easily on streamed music like mp3 usually, assume restart logic or implement complex seeking
            # For prototype editor, just restart is safer or play from 0
            self.game.audio.play() # Plays from start
            # If we want to play from audio_pos, we need 'start' arg in play, available in pygame 2.0+
            try:
                pygame.mixer.music.set_pos(self.audio_pos) # Only works for .ogg in some versions?
                # Actually play(start=...)
                pygame.mixer.music.play(start=self.audio_pos)
            except:
                pygame.mixer.music.play()
            
            self.paused = False
        else:
            self.game.audio.stop()
            self.paused = True

    def handle_click(self, pos):
        mx, my = pos
        center_x = SCREEN_WIDTH // 2
        lane_w = 80
        start_x = center_x - (2 * lane_w)
        
        # Check lane
        if start_x <= mx <= start_x + 4 * lane_w:
            lane = (mx - start_x) // lane_w
            
            # Calculate time
            # y = timeline_y - (t - curr) * zoom
            # (timeline_y - y) / zoom = t - curr
            # t = curr + (timeline_y - y) / zoom
            timeline_y = SCREEN_HEIGHT // 2
            time_offset = (timeline_y - my) / self.zoom
            note_time = self.audio_pos + time_offset
            
            # Snap
            note_time = round(note_time / self.grid_snap) * self.grid_snap
            
            if note_time < 0: return
            
            # Remove existing close note
            removed = False
            for note in self.beatmap[:]:
                if note['lane'] == lane and abs(note['time'] - note_time) < 0.05:
                    self.beatmap.remove(note)
                    removed = True
                    break
            
            # Add new if not removed
            if not removed:
                self.beatmap.append({'time': note_time, 'lane': int(lane)})
                self.beatmap.sort(key=lambda x: x['time'])

    def save_map(self):
        # We need to find the cache file corresponding to this song/diff
        # Generator has the logic. We will hack it to allow saving.
        # Or expose a save method in generator.
        
        # Just use the generator's internal hash logic again
        file_hash = self.game.generator._get_file_hash(self.path, self.difficulty)
        cache_path = os.path.join(self.game.generator.cache_dir, f"{file_hash}.json")
        
        with open(cache_path, 'w') as f:
            json.dump(self.beatmap, f)
            print("Map Saved!")
