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
        Returns a list of hits: [{'time': float, 'lane': int}]
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
        from config import DIFF_SETTINGS
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
        
        notes = []
        for i, t in enumerate(onset_times):
            # Difficulty Density Filter
            # Skip notes based on density multiplier effectively
            # This is a simple probabilistic filter to thin out notes for easier diffs
            # For "FUCK YOU", we actually want to ADD notes
            
            seed = np.sin(t * 123.45) # det. random
            
            if difficulty == "FUCK YOU":
                # CHAOS MODE: Add streams 
                # Add the actual detected note
                lane = int((seed + 1) * 2) % 4
                notes.append({'time': float(t), 'lane': lane})
                
                # Add a 1/8th note spam
                if i % 2 == 0:
                    notes.append({'time': float(t) + 0.1, 'lane': (lane+1)%4})
                    
            elif difficulty == "EXTREME":
                lane = int((seed + 1) * 2) % 4
                notes.append({'time': float(t), 'lane': lane})
                
            else:
                # Standard filtering
                if (seed + 1) / 2 > density_mult:
                     # Skip this note to reduce density for easy/med
                     continue
                
                lane = int((seed + 1) * 2) % 4
                notes.append({'time': float(t), 'lane': lane})
            
        return notes
