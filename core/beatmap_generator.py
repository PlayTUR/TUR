import librosa
import numpy as np
import os
import hashlib
import json
import random

class BeatmapGenerator:
    def __init__(self, cache_dir='beatmap_cache'):
        self.cache_dir = cache_dir
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

    def get_beatmap(self, audio_path, difficulty="MEDIUM"):
        """
        Loads beatmap from .tur file or generates one.
        Priority: .tur file > cache > generate new
        Returns: {'bpm': float, 'duration': float, 'notes': list, 'audio_path': str}
        """
        # Case 1: Input is already a .tur file
        if audio_path.lower().endswith('.tur'):
            if os.path.exists(audio_path):
                print(f"Loading .tur bundle: {os.path.basename(audio_path)}")
                return self.load_tur(audio_path, difficulty)
            else:
                return {'bpm': 120, 'notes': [], 'duration': 180}
        
        # Case 1.5: Input is a .osu file
        if audio_path.lower().endswith('.osu'):
            from core.osu_parser import parse_osu
            print(f"Direct OSB/OSU Load: {os.path.basename(audio_path)}")
            osu_data = parse_osu(audio_path)
            if osu_data:
                return {
                    'bpm': osu_data.get('bpm', 120),
                    'duration': 180, 
                    'notes': osu_data['notes'],
                    'audio_path': os.path.join(os.path.dirname(audio_path), osu_data['audio_filename'])
                }

        # Case 2: Audio file -> check for existing .tur
        tur_path = self._get_tur_path(audio_path, difficulty)
        
        if os.path.exists(tur_path):
            # Check if this SPECIFIC difficulty exists in the .tur
            try:
                data = self.load_tur(tur_path, difficulty)
                # If we got fallback notes (check logical size or if load_tur marks it), 
                # actually load_tur returns whatever diff it found if requested is missing?
                # My load_tur implementation: "If requested diff missing, try fallback".
                # We should check if the returned difficulty is what we wanted.
                if data['difficulty'] == difficulty:
                    return data
                
                # If mismatch, we need to generate this difficulty and add it
                print(f"Difficulty {difficulty} missing in .tur, generating...")
                # Fall through to generation logic but only for this diff
            except Exception as e:
                print(f"Error loading .tur: {e}")

        # Check cache (Legacy json cache, skipping for simplicity in favor of .tur)
        
        # Generate new beatmap(s)
        from core.config import DIFFICULTIES
        
        # If the file didn't exist, we generate ALL difficulties
        # If it did exist but missed one, we just add the one (or all missing).
        
        # Let's just generate ALL missing difficulties to be safe and helpful.
        print(f"Generating beatmaps for {os.path.basename(audio_path)}...")
        
        generated_result = None
        
        # We need to loop through all difficulties
        # Setup: Embed audio only on the first save to avoid overhead/errors
        first_save = True
        if os.path.exists(tur_path):
             first_save = False # Already exists, don't re-embed unless needed
             
        for diff in DIFFICULTIES:
            # Check if we already have it (optimization)
            if os.path.exists(tur_path):
                 try:
                     existing = self.load_tur(tur_path, diff)
                     if existing['difficulty'] == diff and existing['notes']:
                         if diff == difficulty: generated_result = existing
                         continue # Skip existing
                 except: pass

            print(f"  - Generating {diff}...")
            beatmap = self._analyze_audio(audio_path, diff)
            
            if not beatmap: continue
            
            beatmap['audio_path'] = audio_path
            
            # Save/Merge into .tur
            # embed_audio is True only if file doesn't exist yet or we want to ensure it
            # self.save_tur handles merging.
            # We only delete original audio after LAST difficulty if we want to clean up, 
            # currently save_tur deletes if embed_audio=True. 
            # We should only delete after the loop or if we are sure.
            # Actually save_tur's delete_original logic might overlap.
            # Let's handle embedding explicitly.
            
            do_embed = False
            if first_save:
                do_embed = True
                first_save = False
            
            self.save_tur(beatmap, tur_path, audio_path, diff, embed_audio=do_embed, delete_original=False)
            
            if diff == difficulty:
                # Reload to get full struct
                generated_result = self.load_tur(tur_path, diff)

        # Cleanup original audio if we embedded it
        # (Only if we confirmed we created a .tur and embedded audio)
        # For now, let's leave the MP3 there to be safe or reliance on user cleanup.
        # But previous logic had `delete_original=True`.
        # Safe to delete if we are sure .tur exists and has audio.
        
        if generated_result:
             return generated_result
             
        # Fallback
        return {'bpm': 120, 'notes': [], 'duration': 180, 'audio_path': audio_path}
    
    def _get_tur_path(self, audio_path, difficulty):
        """Get .tur file path for an audio file"""
        base = os.path.splitext(audio_path)[0]
        # Unified path - single file for all diffs
        return f"{base}.tur"
    
    def load_tur(self, tur_path, difficulty="MEDIUM"):
        """Load a .tur bundle file (contains beatmap + embedded audio)"""
        with open(tur_path, 'r') as f:
            data = json.load(f)
        
        # Extract embedded audio if present
        audio_path = None
        if data.get('audio_data'):
            import base64
            audio_ext = data.get('audio_ext', '.mp3')
            audio_path = tur_path.replace('.tur', audio_ext)
            
            # Only extract if not already exists
            if not os.path.exists(audio_path):
                audio_bytes = base64.b64decode(data['audio_data'])
                with open(audio_path, 'wb') as af:
                    af.write(audio_bytes)
        
        # Unified Difficulty Handling
        notes = []
        if 'difficulties' in data:
            # New Format
            diff_data = data['difficulties'].get(difficulty, {})
            # If requested diff missing, try fallback
            if not diff_data and data['difficulties']:
                 diff_data = next(iter(data['difficulties'].values()))
            notes = diff_data.get('notes', [])
            events = diff_data.get('events', [])
        else:
            # Legacy Format
            if data.get('difficulty', 'MEDIUM') == difficulty:
                notes = data.get('notes', [])
                events = data.get('events', [])
            else:
                 # File doesn't have this difficulty
                 notes = []
                 events = []

        # Ensure all notes have required fields
        for note in notes:
            note.setdefault('lane', 0)
            note.setdefault('time', 0)
            note.setdefault('length', 0)
            note.setdefault('hit', False)
        
        return {
            'bpm': data.get('bpm', 120),
            'duration': data.get('duration', 180),
            'notes': notes,
            'events': events,
            'title': data.get('title', ''),
            'artist': data.get('artist', ''),
            'difficulty': difficulty, # The requested one
            'source': data.get('source', 'generated'),  # 'osu!' for imports, 'generated' for MP3
            'audio_path': audio_path or (os.path.join(os.path.dirname(tur_path), data.get('audio')) if data.get('audio') else ''),
            'all_difficulties': list(data.get('difficulties', {}).keys()) if 'difficulties' in data else [data.get('difficulty', 'MEDIUM')]
        }
    
    def save_tur(self, beatmap, tur_path, audio_path=None, difficulty=None, embed_audio=True, delete_original=True):
        """
        Save beatmap as .tur bundle file.
        Supports merging difficulties into existing file.
        """
        import base64
        
        # Check if file exists to merge
        existing_data = {}
        if os.path.exists(tur_path):
            try:
                with open(tur_path, 'r') as f:
                    existing_data = json.load(f)
            except:
                pass
                
        # Base Data structure
        title = os.path.splitext(os.path.basename(audio_path))[0] if audio_path else existing_data.get('title', 'Unknown')
        
        data = {
            'format': 'TUR_BUNDLE_v3',
            'title': existing_data.get('title', title),
            'artist': existing_data.get('artist', 'Unknown'),
            'bpm': beatmap.get('bpm', existing_data.get('bpm', 120)),
            'duration': beatmap.get('duration', existing_data.get('duration', 180)),
            'difficulties': existing_data.get('difficulties', {})
        }
        
        # If legacy existing data, migrate it
        if 'notes' in existing_data and 'difficulties' not in existing_data:
            old_diff = existing_data.get('difficulty', 'MEDIUM')
            data['difficulties'][old_diff] = {
                'notes': existing_data['notes']
            }
            
        # Update/Add current difficulty
        current_diff = difficulty or 'MEDIUM'
        data['difficulties'][current_diff] = {
            'notes': [
                {
                    'time': n['time'],
                    'lane': n['lane'],
                    'length': n.get('length', 0)
                }
                for n in beatmap.get('notes', [])
            ],
            'events': beatmap.get('events', [])
        }
        
        # Audio Handling (Preserve valid existing audio)
        if 'audio_data' in existing_data:
            data['audio_data'] = existing_data['audio_data']
            data['audio_ext'] = existing_data.get('audio_ext', '.mp3')
            data['audio_size'] = existing_data.get('audio_size', 0)
        
        # Embed new audio if requested/needed
        if embed_audio and audio_path and os.path.exists(audio_path):
            # Only overwrite if explicitly providing new audio
             try:
                with open(audio_path, 'rb') as af:
                    audio_bytes = af.read()
                data['audio_data'] = base64.b64encode(audio_bytes).decode('ascii')
                data['audio_ext'] = os.path.splitext(audio_path)[1]
                data['audio_size'] = len(audio_bytes)
                print(f"Embedded audio: {len(audio_bytes)} bytes")
                
                if delete_original:
                    try:
                        os.remove(audio_path)
                    except:
                        pass
             except Exception as e:
                print(f"Could not embed audio: {e}")
                data['audio'] = os.path.basename(audio_path)
        else:
             # Keep reference
             data['audio'] = existing_data.get('audio', os.path.basename(audio_path) if audio_path else '')

        with open(tur_path, 'w') as f:
            json.dump(data, f)
        
        print(f"Saved merged .tur bundle: {os.path.basename(tur_path)}")

    def _get_file_hash(self, path, difficulty):
        hasher = hashlib.md5()
        hasher.update(path.encode('utf-8'))
        hasher.update(difficulty.encode('utf-8')) # Factor in difficulty
        # Include stats to invalidate if file changes
        stats = os.stat(path)
        hasher.update(str(stats.st_size).encode('utf-8'))
        hasher.update(str(stats.st_mtime).encode('utf-8'))
        return hasher.hexdigest()

    def _analyze_audio(self, path, difficulty="MEDIUM"):
        """
        Deterministic, intensity-based beatmap generation.
        No random.random() - all decisions based on audio analysis.
        """
        from core.config import DIFF_SETTINGS
        
        settings = DIFF_SETTINGS.get(difficulty, DIFF_SETTINGS["MEDIUM"])
        
        # Check for cached onset data (avoids re-analyzing same audio)
        onset_cache_key = hashlib.md5(path.encode()).hexdigest()
        onset_cache_path = os.path.join(self.cache_dir, f"{onset_cache_key}_onsets_v2.json")
        
        cached_onsets = None
        if os.path.exists(onset_cache_path):
            try:
                with open(onset_cache_path, 'r') as f:
                    cached_onsets = json.load(f)
            except:
                pass
        
        if cached_onsets:
            onset_times = cached_onsets['onset_times']
            bpm = cached_onsets['bpm']
            duration = cached_onsets['duration']
            onset_strengths = cached_onsets.get('strengths', [1.0] * len(onset_times))
            beat_times = cached_onsets.get('beat_times', [])
        else:
            # Full audio analysis
            try:
                y, sr = librosa.load(path, sr=22050)
            except Exception as e:
                print(f"Error loading audio: {e}")
                return {'bpm': 120, 'notes': [], 'duration': 180}
            
            # Always use full HPSS for maximum onset detection
            y_harmonic, y_percussive = librosa.effects.hpss(y)
            
            # Get onset envelopes from both harmonic and percussive
            onset_env_p = librosa.onset.onset_strength(y=y_percussive, sr=sr)
            onset_env_h = librosa.onset.onset_strength(y=y_harmonic, sr=sr)
            
            # Detect onsets with minimal wait (catch everything)
            onset_frames_p = librosa.onset.onset_detect(onset_envelope=onset_env_p, sr=sr, wait=1)
            onset_frames_h = librosa.onset.onset_detect(onset_envelope=onset_env_h, sr=sr, wait=1)
            
            # Combine all onsets
            combined_frames = sorted(list(set(onset_frames_p) | set(onset_frames_h)))
            
            # Get strength for each onset (max of harmonic/percussive)
            onset_strengths = []
            for f in combined_frames:
                str_p = onset_env_p[f] if f < len(onset_env_p) else 0
                str_h = onset_env_h[f] if f < len(onset_env_h) else 0
                onset_strengths.append(float(max(str_p, str_h)))
            
            onset_times = [float(t) for t in librosa.frames_to_time(combined_frames, sr=sr)]
            
            # Get tempo and beat positions
            tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
            bpm = float(tempo)
            beat_times = [float(t) for t in librosa.frames_to_time(beat_frames, sr=sr)]
            duration = float(librosa.get_duration(y=y, sr=sr))
            
            # Cache analysis data
            try:
                with open(onset_cache_path, 'w') as f:
                    json.dump({
                        'onset_times': onset_times,
                        'bpm': bpm,
                        'duration': duration,
                        'strengths': onset_strengths,
                        'beat_times': beat_times
                    }, f)
            except:
                pass
        
        print(f"Detected BPM: {bpm:.1f} ({len(onset_times)} onsets)")
        
        # Normalize strengths to 0-1 range
        max_strength = max(onset_strengths) if onset_strengths else 1.0
        norm_strengths = [s / max_strength for s in onset_strengths]
        
        # Difficulty configuration - DETERMINISTIC, multiplier-based
        # note_mult: how many subdivisions to add
        # chord_threshold: intensity above this = chord
        # max_chord: maximum simultaneous notes
        # subdivision: beat fraction (4 = quarter, 8 = 8th, 16 = 16th, 32 = 32nd)
        diff_config = {
            "EASY": {
                "note_mult": 0.5, "chord_threshold": 0.9, "max_chord": 2,
                "subdivision": 4, "hold_threshold": 0.95, "hold_min": 0.3
            },
            "MEDIUM": {
                "note_mult": 0.8, "chord_threshold": 0.75, "max_chord": 2,
                "subdivision": 4, "hold_threshold": 0.85, "hold_min": 0.25
            },
            "HARD": {
                "note_mult": 1.0, "chord_threshold": 0.6, "max_chord": 3,
                "subdivision": 16, "hold_threshold": 0.7, "hold_min": 0.2
            },
            "EXTREME": {
                "note_mult": 1.5, "chord_threshold": 0.4, "max_chord": 3,
                "subdivision": 16, "hold_threshold": 0.5, "hold_min": 0.15
            },
            "FUCK YOU": {
                "note_mult": 2.5, "chord_threshold": 0.15, "max_chord": 4,
                "subdivision": 32, "hold_threshold": 0.3, "hold_min": 0.1
            }
        }
        
        cfg = diff_config.get(difficulty, diff_config["MEDIUM"])
        
        notes = []
        
        # Helper: deterministic lane from time (no random!)
        def get_lane(t, offset=0):
            # Use time-based hash for deterministic lane selection
            hash_val = int(abs(np.sin(t * 1000.0 + offset) * 10000))
            return hash_val % 4
        
        # Helper: get chord lanes based on intensity
        def get_chord_lanes(t, intensity, max_notes):
            base_lane = get_lane(t)
            lanes = [base_lane]
            
            if intensity >= cfg["chord_threshold"]:
                # Add more lanes based on intensity
                extra = 1
                if intensity >= 0.9:
                    extra = min(3, max_notes - 1)
                elif intensity >= 0.7:
                    extra = min(2, max_notes - 1)
                
                for i in range(extra):
                    new_lane = get_lane(t, offset=(i + 1) * 100)
                    if new_lane not in lanes:
                        lanes.append(new_lane)
            
            return lanes[:max_notes]
        
        # Process each onset - ALL onsets become notes
        for idx, t in enumerate(onset_times):
            if t < 0.5:  # Skip first 0.5s (usually silence)
                continue
            
            intensity = norm_strengths[idx] if idx < len(norm_strengths) else 0.5
            
            # Determine chord size based on intensity
            chord_lanes = get_chord_lanes(t, intensity, cfg["max_chord"])
            
            for lane in chord_lanes:
                # Determine if this should be a hold note
                hold_length = 0.0
                if intensity >= cfg["hold_threshold"]:
                    # Find next onset to determine hold length
                    if idx + 1 < len(onset_times):
                        gap = onset_times[idx + 1] - t
                        if gap > cfg["hold_min"] * 2:
                            hold_length = max(cfg["hold_min"], gap * 0.6)
                
                notes.append({
                    'time': t,
                    'lane': lane,
                    'length': hold_length,
                    'hit': False
                })
        
        # Add beat subdivisions based on difficulty
        if cfg["subdivision"] >= 8 and beat_times:
            spb = 60.0 / bpm  # Seconds per beat
            
            for i, beat_t in enumerate(beat_times[:-1]):
                next_beat = beat_times[i + 1]
                beat_gap = next_beat - beat_t
                
                # Calculate subdivision interval
                sub_count = cfg["subdivision"] // 4  # 8th = 2 subs, 16th = 4, 32nd = 8
                sub_interval = beat_gap / sub_count
                
                for s in range(1, sub_count):
                    sub_t = beat_t + s * sub_interval
                    
                    # Check if there's already a note near this time
                    has_nearby = any(abs(n['time'] - sub_t) < 0.03 for n in notes)
                    if has_nearby:
                        continue
                    
                    # Add subdivision note
                    lane = get_lane(sub_t)
                    notes.append({
                        'time': sub_t,
                        'lane': lane,
                        'length': 0,
                        'hit': False
                    })
        
        # For extreme difficulties, add stream patterns between onsets
        if difficulty in ["EXTREME", "FUCK YOU"]:
            stream_notes = []
            for i in range(len(onset_times) - 1):
                t1, t2 = onset_times[i], onset_times[i + 1]
                gap = t2 - t1
                
                # If gap is moderate (good for streams)
                if 0.15 < gap < 0.5:
                    # Add rapid alternating notes
                    if difficulty == "FUCK YOU":
                        interval = 0.05
                    else:
                        interval = 0.08
                    cur_t = t1 + interval
                    lane_offset = 0
                    
                    while cur_t < t2 - 0.03:
                        has_nearby = any(abs(n['time'] - cur_t) < 0.025 for n in notes)
                        if not has_nearby:
                            # Alternating lanes for streams
                            stream_lane = (get_lane(t1) + lane_offset) % 4
                            stream_notes.append({
                                'time': cur_t,
                                'lane': stream_lane,
                                'length': 0,
                                'hit': False
                            })
                            lane_offset = (lane_offset + 1) % 4
                        cur_t += interval
            
            notes.extend(stream_notes)
        
        # Apply note multiplier (add or remove notes)
        if cfg["note_mult"] < 1.0:
            # Remove some notes deterministically
            keep_count = int(len(notes) * cfg["note_mult"])
            # Sort by time, then by intensity (keep high intensity)
            notes.sort(key=lambda n: n['time'])
            # Keep every Nth note
            step = max(1, int(1 / cfg["note_mult"]))
            notes = [n for i, n in enumerate(notes) if i % step == 0]
        
        # Sort by time
        notes.sort(key=lambda n: n['time'])
        
        # Remove notes that are too close together (< 30ms)
        filtered_notes = []
        last_times = {0: 0, 1: 0, 2: 0, 3: 0}
        for note in notes:
            lane = note['lane']
            if note['time'] - last_times[lane] >= 0.03:
                filtered_notes.append(note)
                last_times[lane] = note['time']
        
        notes = filtered_notes
        
        print(f"Generated {len(notes)} notes for {difficulty} (deterministic, intensity-based)")
        return {'bpm': bpm, 'notes': notes, 'duration': duration}


