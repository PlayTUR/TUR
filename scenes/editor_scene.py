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
        
        # Load map
        map_data = self.game.generator.get_beatmap(self.path, self.difficulty)
        
        if isinstance(map_data, list):
            self.beatmap = map_data
            audio_source = self.path
        else:
            self.beatmap = map_data.get('notes', [])
            self.events = map_data.get('events', [])
            audio_source = map_data.get('audio_path', self.path)
            
        from core.utils import find_resource
        resolved_audio = find_resource(audio_source, hint_dirs=["songs", os.path.dirname(self.path)])
        
        if resolved_audio:
            try:
                self.game.audio.load_song(resolved_audio)
            except Exception as e:
                print(f"EDITOR: Error loading audio: {e}")
                self.audio_missing = True
        else:
            print(f"EDITOR: Audio file not found: {audio_source}")
            self.audio_missing = True

        # Don't play yet, pause
        self.paused = True
        self.audio_missing = False if resolved_audio else True # Ensure flag is set
        self.audio_pos = 0.0
        self.scroll_speed = 100 # Time scale for editor
        self.zoom = 100 # Pixels per second in editor view
        
        self.selected_lane = 0
        self.grid_snap = 0.25 # seconds
        self.edit_mode = "NOTES" # NOTES or EVENTS
        self.events = [] # list of {time, type, ...}
        self.selected_event_type = EVENT_CAMERA_ZOOM

    def update(self):
        if self.audio_missing: return
        if not self.paused:
            # We can't rely on audio.get_pos if we want precise scrub
            # But for playback we do.
            if not self.game.audio.is_playing:
                self.paused = True
            self.audio_pos = self.game.audio.get_position()
            
    def draw(self, surface):
        surface.fill(BLACK)
        
        if self.audio_missing:
            self.game.renderer.draw_panel(surface, 300, 300, 400, 150, "SYSTEM ERROR")
            self.game.renderer.draw_text(surface, "AUDIO FILE NOT FOUND", 320, 340, (255, 50, 50))
            self.game.renderer.draw_text(surface, "[ESC] TO EXIT", 320, 380, (150, 150, 150))
            return
            
        # Draw Timeline
        center_x = SCREEN_WIDTH // 2
        
        # Mode Indicator
        mode_col = TERM_AMBER if self.edit_mode == "EVENTS" else TERM_GREEN
        self.game.renderer.draw_text(surface, f"MODE: {self.edit_mode}", 10, 50, mode_col)
        if self.edit_mode == "EVENTS":
            self.game.renderer.draw_text(surface, f"TYPE: {self.selected_event_type} [1-3]", 10, 70, TERM_AMBER)
        
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

        # Draw Events
        for ev in self.events:
            diff = ev['time'] - self.audio_pos
            if diff < -5 or diff > 5: continue
            
            y = timeline_y - (diff * self.zoom)
            
            # Draw event marker on left side
            text = "EV"
            col = (200, 200, 200)
            if ev['type'] == EVENT_CAMERA_ZOOM: 
                text = "ZOOM"
                col = (100, 255, 255)
            elif ev['type'] == EVENT_CAMERA_SHAKE: 
                text = "SHAKE"
                col = (255, 100, 100)
            elif ev['type'] == EVENT_NOTE_GLOW: 
                text = "GLOW"
                col = (100, 255, 0)
                
            pygame.draw.circle(surface, col, (start_x - 40, int(y)), 10)
            self.game.renderer.draw_text(surface, text, start_x - 90, int(y) - 10, col)

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
                if self.game.audio.is_playing:
                    self.game.audio.stop()
                from scenes.menu_scenes import SongSelectScene
                self.game.scene_manager.switch_to(SongSelectScene)
            if self.audio_missing: return
            
            if event.key == pygame.K_SPACE:
                self.toggle_playback()
            elif event.key == pygame.K_s:
                self.save_map()
            elif event.key == pygame.K_TAB:
                self.edit_mode = "EVENTS" if self.edit_mode == "NOTES" else "NOTES"
            elif event.key == pygame.K_1: self.selected_event_type = EVENT_CAMERA_ZOOM
            elif event.key == pygame.K_2: self.selected_event_type = EVENT_CAMERA_SHAKE
            elif event.key == pygame.K_3: self.selected_event_type = EVENT_NOTE_GLOW
            
            elif event.key == pygame.K_UP:
                self.zoom += 10
            elif event.key == pygame.K_DOWN:
                self.zoom = max(10, self.zoom - 10)
            elif event.key == pygame.K_LEFT:
                self.audio_pos = max(0, self.audio_pos - 1)
                if self.game.audio.is_playing:
                     pass 
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Left Click
                if self.edit_mode == "NOTES":
                    self.handle_click(event.pos)
                else:
                    self.handle_click_event(event.pos)
            elif event.button == 4: # Scroll Up
                self.audio_pos = max(0, self.audio_pos - 0.5)
            elif event.button == 5:
                self.audio_pos += 0.5

    def toggle_playback(self):
        if self.paused:
            self.game.audio.stop() # Reset
            self.game.audio.play() # Plays from start
            try:
                # Actually play(start=...)
                pygame.mixer.music.play(start=self.audio_pos)
            except:
                pygame.mixer.music.play()
            
            self.paused = False
        else:
            self.game.audio.stop()
            self.paused = True

    def handle_click_event(self, pos):
        mx, my = pos
        timeline_y = SCREEN_HEIGHT // 2
        time_offset = (timeline_y - my) / self.zoom
        event_time = self.audio_pos + time_offset
        event_time = round(event_time / self.grid_snap) * self.grid_snap
        
        if event_time < 0: return

        # Remove existing event near here
        removed = False
        for e in self.events[:]:
            if abs(e['time'] - event_time) < 0.1:
                self.events.remove(e)
                removed = True
                break
        
        if not removed:
             # Add event
             ev = {'time': event_time, 'type': self.selected_event_type}
             if self.selected_event_type == EVENT_CAMERA_ZOOM:
                 ev['value'] = 1.5 # Default zoom in
                 ev['duration'] = 1.0
             elif self.selected_event_type == EVENT_CAMERA_SHAKE:
                 ev['intensity'] = 10.0
                 ev['duration'] = 0.5
             elif self.selected_event_type == EVENT_NOTE_GLOW:
                 ev['color'] = (0, 255, 255)
                 ev['duration'] = 2.0
                 
             self.events.append(ev)
             self.events.sort(key=lambda x: x['time'])

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
        # Determine .tur path
        if self.path.endswith('.tur'):
            tur_path = self.path
        else:
            base = os.path.splitext(self.path)[0]
            tur_path = f"{base}_{self.difficulty.lower()}.tur"
        
        # Get existing data if possible to preserve audio
        audio_path_to_use = self.path
        
        try:
            # Re-save using generator
            # We need to construct the beatmap dict
            beatmap_data = {
                'bpm': getattr(self, 'bpm', 120),
                'duration': getattr(self, 'duration', 180),
                'notes': self.beatmap,
                'events': self.events
            }
            
            # If we are editing a .tur, we need to handle the embedded audio 
            # save_tur will re-embed if we pass the extracted path
            
            # If self.path is a .tur, self.game.audio.current_song_path might be the extracted temp file?
            # Actually EditorScene loads audio via load_song(self.path). 
            # If self.path is .tur, load_song extracts it.
            # But we don't know where it extracted it easily unless we check generator logic or if load_song updates something.
            # Ideally get_beatmap returned 'audio_path'.
            
            # Let's rely on generator.save_tur to handle it if we pass the right things.
            # If we pass audio_path=None, it might fail to embed.
            
            # Use the audio path from the currently loaded song if available
            # We can get it from the generator if we re-query or store it.
            
            # Better approach:
            # If self.path is .tur, we want to update it.
            # generator.save_tur handles bundle creation.
            
            # We need the AUDIO file path to embed.
            # If we are editing a .tur, the audio is inside it. 
            # We should extract it to a temp path if not already, then pass it to save_tur.
            
            # Hack: Use get_beatmap again to get the audio_path
            temp_map = self.game.generator.get_beatmap(self.path, self.difficulty)
            real_audio_path = temp_map.get('audio_path', self.path)
            
            self.game.generator.save_tur(
                beatmap_data, 
                tur_path, 
                audio_path=real_audio_path, 
                difficulty=self.difficulty,
                embed_audio=True,
                delete_original=False # Don't delete our temp file or source
            )
            
            print(f"Map Saved to {tur_path}")
            self.game.renderer.draw_text(self.game.screen, "SAVED!", 10, 60, (0, 255, 0))
            
        except Exception as e:
            print(f"Save error: {e}")
