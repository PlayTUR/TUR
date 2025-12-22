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
                return self.load_tur(audio_path)
            else:
                print(f".tur file not found: {audio_path}")
                return {'bpm': 120, 'notes': [], 'duration': 180}
        
        # Case 1.5: Input is a .osu file
        if audio_path.lower().endswith('.osu'):
            from core.osu_parser import parse_osu
            print(f"Direct OSB/OSU Load: {os.path.basename(audio_path)}")
            osu_data = parse_osu(audio_path)
            if osu_data:
                return {
                    'bpm': osu_data.get('bpm', 120),
                    'duration': 180, # Placeholder, would need analysis
                    'notes': osu_data['notes'],
                    'audio_path': os.path.join(os.path.dirname(audio_path), osu_data['audio_filename'])
                }

        # Case 2: Audio file -> check for existing .tur or cache
        tur_path = self._get_tur_path(audio_path, difficulty)
        
        # Check for sidecar .tur file (e.g., song_medium.tur)
        if os.path.exists(tur_path):
            print(f"Loading sidecar beatmap: {os.path.basename(tur_path)}")
            try:
                data = self.load_tur(tur_path)
                if not data.get('audio_path'):
                    data['audio_path'] = audio_path
                return data
            except Exception as e:
                print(f"Error loading .tur file: {e}")
        
        # Check cache
        file_hash = self._get_file_hash(audio_path, difficulty)
        cache_path = os.path.join(self.cache_dir, f"{file_hash}.json")

        if os.path.exists(cache_path):
            print(f"Loading cached beatmap for {os.path.basename(audio_path)} [{difficulty}]")
            try:
                with open(cache_path, 'r') as f:
                    beatmap = json.load(f)
                    beatmap['audio_path'] = audio_path
                    return beatmap
            except:
                pass

        # Generate new beatmap
        print(f"Generating beatmap for {os.path.basename(audio_path)} [{difficulty}]...")
        beatmap = self._analyze_audio(audio_path, difficulty)
        
        if not beatmap or isinstance(beatmap, list):
            # Fallback if analysis failed
            print("Audio analysis failed, using empty map")
            beatmap = {'bpm': 120, 'notes': [], 'duration': 180, 'audio_path': audio_path}
        else:
            beatmap['audio_path'] = audio_path
        
        # Save to cache
        with open(cache_path, 'w') as f:
            json.dump(beatmap, f)
        
        # Auto-export as .tur for future editing
        self.save_tur(beatmap, tur_path, audio_path, difficulty)
            
        return beatmap
    
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
        else:
            # Legacy Format
            if data.get('difficulty', 'MEDIUM') == difficulty:
                notes = data.get('notes', [])
            else:
                 # File doesn't have this difficulty
                 notes = []

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
            'title': data.get('title', ''),
            'artist': data.get('artist', ''),
            'difficulty': difficulty, # The requested one
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
            ]
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
        from core.config import DIFF_SETTINGS
        print(f"Analyzing {path} with difficulty {difficulty}")
        
        settings = DIFF_SETTINGS.get(difficulty, DIFF_SETTINGS["MEDIUM"])
        density_mult = settings["density"]
        
        try:
            # Load with higher sample rate for better transient detection
            y, sr = librosa.load(path, sr=44100)
        except Exception as e:
            print(f"Error loading audio: {e}")
            return []

        # 1. Component Separation (HPSS)
        # This allows us to target 'fast instruments' (harmonic) vs 'drums' (percussive)
        print("Performing Harmonic-Percussive separation...")
        y_harmonic, y_percussive = librosa.effects.hpss(y)
        
        hop_length = 512
        # Adaptive wait windows based on difficulty
        if difficulty == "EASY": wait = 12
        elif difficulty == "MEDIUM": wait = 8
        elif difficulty == "HARD": wait = 4
        elif difficulty == "EXTREME": wait = 2
        else: wait = 1 # FUCK YOU: No mercy

        # 2. Detect Onsets for both components
        onset_env_p = librosa.onset.onset_strength(y=y_percussive, sr=sr)
        onset_frames_p = librosa.onset.onset_detect(onset_envelope=onset_env_p, sr=sr, wait=wait)
        
        # Harmonic peaks target the 'fastest instruments' (melodic leads)
        onset_env_h = librosa.onset.onset_strength(y=y_harmonic, sr=sr)
        onset_frames_h = librosa.onset.onset_detect(onset_envelope=onset_env_h, sr=sr, wait=wait)
        
        # Combine and sort all potential timestamps
        combined_frames = sorted(list(set(onset_frames_p) | set(onset_frames_h)))
        onset_times = librosa.frames_to_time(combined_frames, sr=sr)
        
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        bpm = float(tempo)
        print(f"Detected BPM: {bpm:.1f}")
        
        notes = []
        duration = librosa.get_duration(y=y, sr=sr)
        last_note_time = 0
        
        for f in combined_frames:
            t = float(librosa.frames_to_time(f, sr=sr))
            seed = np.sin(t * 123.45)
            
            # Strength from both sources
            strength_p = onset_env_p[f] if f < len(onset_env_p) else 0
            strength_h = onset_env_h[f] if f < len(onset_env_h) else 0
            strength = max(strength_p, strength_h)
            
            # Gap Check (Long notes for atmospheric sections)
            gap = t - last_note_time
            if gap > 2.5 and len(notes) > 0:
                hold_start = last_note_time + 0.2
                hold_length = min(gap - 0.5, 3.0)
                if hold_length > 0.5:
                    hold_lane = (notes[-1]['lane'] + 2) % 4
                    notes.append({'time': float(hold_start), 'lane': hold_lane, 'length': float(hold_length), 'hit': False})
            
            # Density Check
            is_extreme = difficulty in ["EXTREME", "FUCK YOU"]
            if not is_extreme:
                if (seed + 1) / 2 > density_mult:
                    continue
            
            # Lane selection based on spectral content? (Higher freq -> right lanes)
            # For simplicity, we use seed but bias by strength
            lane = int((seed + 1) * 2) % 4
            chord_size = 1
            
            # Chord logic based on combined strength
            if difficulty == "FUCK YOU":
                if strength > 1.2: chord_size = 4
                elif strength > 0.6: chord_size = 3
                elif strength > 0.3: chord_size = 2
            elif difficulty == "EXTREME":
                if strength > 1.5: chord_size = 3
                elif strength > 0.8: chord_size = 2
            elif difficulty == "HARD":
                if strength > 2.0: chord_size = 2
            
            # Generate primary notes
            lanes = [lane]
            while len(lanes) < chord_size:
                next_lane = (lanes[-1] + 1) % 4
                if next_lane not in lanes: lanes.append(next_lane)
            
            for l in lanes:
                # Decide on hold length
                length = 0.0
                if strength_h > strength_p * 1.5 and seed > 0.5:
                    # Harmonic lead -> likely a held synth or guitar note
                    length = 0.1 + (seed + 1) * 0.4
                
                notes.append({'time': t, 'lane': l, 'length': length, 'hit': False})
            
            # Technical Overlays for FAST fragments
            if difficulty == "FUCK YOU":
                # High energy harmonic content (The "Fastest Instrument" logic)
                if strength_h > 1.5:
                    # Append a 1/32nd repeat (vibrato/fast shred)
                    notes.append({'time': t + 0.04, 'lane': (lane + 1) % 4, 'length': 0, 'hit': False})
                    notes.append({'time': t + 0.08, 'lane': (lane + 2) % 4, 'length': 0, 'hit': False})
                elif strength_p > 2.0:
                    # Heavy percussive kick -> 1/16th double
                    notes.append({'time': t + 0.08, 'lane': lane, 'length': 0, 'hit': False})

            elif difficulty == "EXTREME" and strength_h > 2.0:
                # Fast melodic flick
                notes.append({'time': t + 0.1, 'lane': (lane + 2) % 4, 'length': 0, 'hit': False})
            
            last_note_time = t
        
        notes.sort(key=lambda n: n['time'])
        return {'bpm': bpm, 'notes': notes, 'duration': duration}

