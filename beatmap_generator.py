import librosa
import numpy as np
import os
import hashlib
import json

class BeatmapGenerator:
    def __init__(self, cache_dir='beatmap_cache'):
        self.cache_dir = cache_dir
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

    def get_beatmap(self, audio_path, difficulty="MEDIUM"):
        """
        Generates or retrieves a beatmap for the given audio file.
        Returns: {'bpm': float, 'duration': float, 'notes': list}
        """
        # Create a hash of the file path + file size/mtime + difficulty for caching
        file_hash = self._get_file_hash(audio_path, difficulty)
        cache_path = os.path.join(self.cache_dir, f"{file_hash}.json")

        if os.path.exists(cache_path):
            print(f"Loading cached beatmap for {os.path.basename(audio_path)} [{difficulty}]")
            try:
                with open(cache_path, 'r') as f:
                    return json.load(f)
            except:
                pass # Fail gracefully

        print(f"Generating beatmap for {os.path.basename(audio_path)} [{difficulty}]... (This may take a moment)")
        beatmap = self._analyze_audio(audio_path, difficulty)
        
        with open(cache_path, 'w') as f:
            json.dump(beatmap, f)
            
        return beatmap

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
            y, sr = librosa.load(path, sr=22050)
        except Exception as e:
            print(f"Error loading audio: {e}")
            return []

        # Adjust onset detection based on difficulty
        # For 'Easy', we smooth more to find only major beats
        hop_length = 512
        if difficulty == "EASY":
            wait = 10 # Wait frames between onsets
        elif difficulty == "FUCK YOU":
            wait = 1
        else:
            wait = 5

        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        onset_frames = librosa.onset.onset_detect(
            onset_envelope=onset_env, 
            sr=sr, 
            units='frames',
            hop_length=hop_length,
            backtrack=False,
            wait=wait
        )
        onset_times = librosa.frames_to_time(onset_frames, sr=sr)
        
        # Rhythm Analysis
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        bpm = float(tempo)
        print(f"Detected BPM: {bpm:.1f}")
        
        notes = []
        for i, t in enumerate(onset_times):
            # Difficulty Density Filter
            seed = np.sin(t * 123.45) # det. random
            
            if difficulty == "FUCK YOU":
                # CHAOS MODE
                lane = int((seed + 1) * 2) % 4
                notes.append({'time': float(t), 'lane': lane})
                if i % 2 == 0:
                    notes.append({'time': float(t) + 0.1, 'lane': (lane+1)%4})
                    
            elif difficulty == "EXTREME":
                lane = int((seed + 1) * 2) % 4
                notes.append({'time': float(t), 'lane': lane})
                
            else:
                if (seed + 1) / 2 > density_mult: continue
                lane = int((seed + 1) * 2) % 4
                notes.append({'time': float(t), 'lane': lane})
            
        # Return structure update: Dictionary with metadata
        result = {
            'bpm': bpm,
            'notes': notes,
            'duration': librosa.get_duration(y=y, sr=sr)
        }
        return result
