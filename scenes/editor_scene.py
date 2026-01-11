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
        self.game.discord.update(f"Charting {self.song_name}", "Editor")
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
            
        # --- UI Sidebar (Left) ---
        ui_x = 10
        ui_y = 50
        
        # Valid Mouse Pos for hover (Virtual)
        mx, my = self.game.get_virtual_pos(pygame.mouse.get_pos())
        
        # Helper for buttons
        def draw_btn(text, y, active=False, color=None):
            rect = pygame.Rect(ui_x, y, 140, 30)
            hover = rect.collidepoint(mx, my)
            
            c = color if color else (TERM_GREEN if active else (50, 50, 50))
            if hover and not active: c = (80, 80, 80)
            
            pygame.draw.rect(surface, c, rect)
            pygame.draw.rect(surface, TERM_WHITE, rect, 1)
            self.game.renderer.draw_text(surface, text, ui_x + 10, y + 5, BLACK if active else TERM_WHITE)
            return rect

        # Mode Toggles
        self.btn_notes = draw_btn("NOTES", ui_y, self.edit_mode == "NOTES")
        ui_y += 35
        self.btn_events = draw_btn("EVENTS", ui_y, self.edit_mode == "EVENTS")
        ui_y += 45
        
        # Tools
        self.btn_tool_zoom = None
        self.btn_tool_shake = None
        self.btn_tool_glow = None
        self.btn_tool_speed = None
        
        if self.edit_mode == "EVENTS":
            self.game.renderer.draw_text(surface, "TOOLS:", ui_x, ui_y, TERM_AMBER)
            ui_y += 25
            self.btn_tool_zoom = draw_btn("ZOOM", ui_y, self.selected_event_type == EVENT_CAMERA_ZOOM, (100, 255, 255) if self.selected_event_type == EVENT_CAMERA_ZOOM else None)
            ui_y += 35
            self.btn_tool_shake = draw_btn("SHAKE", ui_y, self.selected_event_type == EVENT_CAMERA_SHAKE, (255, 100, 100) if self.selected_event_type == EVENT_CAMERA_SHAKE else None)
            ui_y += 35
            self.btn_tool_glow = draw_btn("GLOW", ui_y, self.selected_event_type == EVENT_NOTE_GLOW, (100, 255, 0) if self.selected_event_type == EVENT_NOTE_GLOW else None)
            ui_y += 35
            self.btn_tool_speed = draw_btn("SPEED", ui_y, self.selected_event_type == EVENT_SPEED_CHANGE, (255, 255, 0) if self.selected_event_type == EVENT_SPEED_CHANGE else None)
            ui_y += 45

        # Actions
        ui_y = 500
        self.btn_save = draw_btn("SAVE [S]", ui_y, False, (50, 100, 200))
        ui_y += 35
        self.btn_play = draw_btn("PAUSE" if not self.paused else "PLAY", ui_y, not self.paused)
        
        # --- Timeline & Grid ---
        
        # Time Indicator
        self.game.renderer.draw_text(surface, f"TIME: {self.audio_pos:.2f}s", 10, 10, TERM_WHITE)
        self.game.renderer.draw_text(surface, f"SNAP: {self.grid_snap}s | ZOOM: {self.zoom}", 10, 30, TERM_WHITE)
        self.game.renderer.draw_text(surface, "[SPACE] PLAY/PAUSE | [S] SAVE | [CLICK] PLACE/REMOVE", 10, 700, TERM_AMBER)
        
        # Draw notes relative to center line (which is current time)
        # Let's say center Y is current time.
        timeline_y = SCREEN_HEIGHT // 2
        pygame.draw.line(surface, TERM_RED, (0, timeline_y), (SCREEN_WIDTH, timeline_y), 2)
        
        # Lanes
        center_x = SCREEN_WIDTH // 2
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
            
        # Draw Ghost Note (Hover)
        if self.edit_mode == "NOTES" and not self.check_ui_click((mx*0 + pygame.mouse.get_pos()[0], 0)): # Hacky check if mouse is over UI using real coords?
            # actually we have virtual mx, my
            # check ui logic uses virtual mx, my? No draw uses hardcoded ui_x=10.
            # let's just calc lane/time
            
            center_x = SCREEN_WIDTH // 2
            lane_w = 80
            start_x = center_x - (2 * lane_w)
            
            if start_x <= mx <= start_x + 4 * lane_w:
                 lane = int((mx - start_x) // lane_w)
                 
                 timeline_y = SCREEN_HEIGHT // 2
                 time_offset = (timeline_y - my) / self.zoom
                 hover_time = self.audio_pos + time_offset
                 hover_time = round(hover_time / self.grid_snap) * self.grid_snap
                 
                 if hover_time >= 0:
                     diff = hover_time - self.audio_pos
                     y = timeline_y - (diff * self.zoom)
                     x = start_x + lane * lane_w
                     
                     # Ghost
                     s = pygame.Surface((lane_w - 10, 20))
                     s.set_alpha(100)
                     s.fill((0, 255, 0))
                     surface.blit(s, (x + 5, y - 10))
                     
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
            
            # Event Tool Shortcuts (Only in EVENTS mode)
            elif event.key == pygame.K_1 and self.edit_mode == "EVENTS": self.selected_event_type = EVENT_CAMERA_ZOOM
            elif event.key == pygame.K_2 and self.edit_mode == "EVENTS": self.selected_event_type = EVENT_CAMERA_SHAKE
            elif event.key == pygame.K_3 and self.edit_mode == "EVENTS": self.selected_event_type = EVENT_NOTE_GLOW
            elif event.key == pygame.K_4 and self.edit_mode == "EVENTS": self.selected_event_type = EVENT_SPEED_CHANGE
            
            elif event.key == pygame.K_UP:
                self.zoom += 10
            elif event.key == pygame.K_DOWN:
                self.zoom = max(10, self.zoom - 10)
            elif event.key == pygame.K_LEFT:
                self.audio_pos = max(0, self.audio_pos - 1)
                
            # Note placement via keys (1-4 / D,F,J,K support would be better but 1-4 is standard editor)
            elif event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4]:
                if self.edit_mode == "NOTES":
                    lane = event.key - pygame.K_1
                    # Use cursor Y (timeline) for time
                    self.place_note_at_cursor(lane)
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Convert to virtual coords for logic
            virtual_pos = self.game.get_virtual_pos(event.pos)
            print(f"DEBUG: Click {event.pos} -> Virtual {virtual_pos}")
            
            if event.button == 1: # Left Click
                if self.edit_mode == "NOTES":
                    print(f"DEBUG: Handling Note Click at {virtual_pos}")
                    self.handle_click(virtual_pos)
                else:
                    print("DEBUG: Handling Event Click")
                    self.handle_click_event(virtual_pos)
            elif event.button == 4: # Scroll Up
                self.audio_pos = max(0, self.audio_pos - 0.5)
            elif event.button == 5:
                self.audio_pos += 0.5
            
    def place_note_at_cursor(self, lane):
        note_time = self.audio_pos
        # Snap
        note_time = round(note_time / self.grid_snap) * self.grid_snap
        if note_time < 0: return
        
        # Toggle note
        removed = False
        for note in self.beatmap[:]:
            if note['lane'] == lane and abs(note['time'] - note_time) < 0.05:
                self.beatmap.remove(note)
                removed = True
                break
        
        if not removed:
            self.beatmap.append({'time': note_time, 'lane': int(lane)})
            self.beatmap.sort(key=lambda x: x['time'])

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

    def check_ui_click(self, pos):
        mx, my = pos
        # debug
        # print(f"DEBUG: UI Check {mx},{my}")
        
        if not (10 <= mx <= 150): return False
        
        # Mode Toggles
        if 50 <= my <= 80:
            print("DEBUG: UI Click NOTES")
            self.edit_mode = "NOTES"
            return True
        if 85 <= my <= 115:
            self.edit_mode = "EVENTS"
            return True
            
        # Tools
        if self.edit_mode == "EVENTS":
            if 155 <= my <= 185:
                self.selected_event_type = EVENT_CAMERA_ZOOM
                return True
            if 190 <= my <= 220:
                self.selected_event_type = EVENT_CAMERA_SHAKE
                return True
            if 225 <= my <= 255:
                self.selected_event_type = EVENT_NOTE_GLOW
                return True
            if 260 <= my <= 290:
                self.selected_event_type = EVENT_SPEED_CHANGE
                return True
        
        # Actions
        if 500 <= my <= 530:
            self.save_map()
            return True
        if 535 <= my <= 565:
            self.toggle_playback()
            return True
            
        return False

    def handle_click_event(self, pos):
        if self.check_ui_click(pos): return
        
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
             elif self.selected_event_type == EVENT_SPEED_CHANGE:
                 ev['multiplier'] = 2.0
                 
             self.events.append(ev)
             self.events.sort(key=lambda x: x['time'])

    def handle_click(self, pos):
        if self.check_ui_click(pos): return
        
        mx, my = pos
        center_x = SCREEN_WIDTH // 2
        lane_w = 80
        start_x = center_x - (2 * lane_w)
        
        
        # Check lane
        print(f"DEBUG: Lanes start at {start_x}, click at {mx}")
        if start_x <= mx <= start_x + 4 * lane_w:
            lane = int((mx - start_x) // lane_w)
            print(f"DEBUG: Calculated Lane: {lane}")
            
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
                print(f"DEBUG: Added note at {note_time} Lane {lane}")
            else:
                print(f"DEBUG: Removed note at {note_time} Lane {lane}")

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
