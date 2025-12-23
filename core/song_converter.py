"""
Song Converter - Auto-converts audio and .osu files to .tur beatmap format on startup.
"""

import os
import json
from core.beatmap_generator import BeatmapGenerator


def auto_convert_songs(songs_dir="songs", default_difficulty="MEDIUM", callback=None, cancel_check=None):
    """
    Scans songs directory for .mp3 / .osz and converts them to .tur
    cancel_check: Optional callable that returns True if cancellation requested
    """
    if not os.path.exists(songs_dir):
        os.makedirs(songs_dir)
        
    from core.settings_manager import SettingsManager
    settings = SettingsManager()
    force_regen = settings.get("auto_recreate_beatmaps") or False
    
    converted_count = 0
    
    # Helper to check for cancel
    def is_cancelled():
        return cancel_check and cancel_check()
    
    # First: Handle .osz extraction
    import zipfile
    osz_files = [f for f in os.listdir(songs_dir) if f.lower().endswith('.osz')]
    for idx, filename in enumerate(osz_files):
        if is_cancelled():
            if callback: callback("Cancelled", 0)
            return ["Cancelled"]
        if callback:
            callback(f"Extracting: {filename}", int((idx / max(1, len(osz_files))) * 30))
            
        folder_name = os.path.splitext(filename)[0]
        extract_dir = os.path.join(songs_dir, folder_name)
        filepath = os.path.join(songs_dir, filename)
        
        # Always extract if we want to re-gen, or if it doesn't exist
        if not os.path.exists(extract_dir) or force_regen:
            print(f"Extracting OSZ: {filename}")
            if not os.path.exists(extract_dir): os.makedirs(extract_dir)
            try:
                allowed_exts = ('.osu', '.mp3', '.wav', '.ogg', '.m4a', '.flac')
                with zipfile.ZipFile(filepath, 'r') as zip_ref:
                    for member in zip_ref.namelist():
                        if member.lower().endswith(allowed_exts):
                            zip_ref.extract(member, extract_dir)
                
                # CLEANUP: Delete the .osz archive after successful extraction
                try: os.remove(filepath)
                except: pass
            except Exception as e:
                print(f"Error extracting {filename}: {e}")
    
    audio_extensions = ('.mp3', '.wav', '.ogg', '.m4a', '.flac')
    generator = BeatmapGenerator()
    
    # Second: Handle .osu files (after extraction)
    all_files = []
    for root, dirs, files in os.walk(songs_dir):
        for f in files:
            all_files.append(os.path.join(root, f))
            
    osu_files = [f for f in all_files if f.lower().endswith('.osu')]
    
    converted_osu_folders = set()
    
    for idx, path in enumerate(osu_files):
        if is_cancelled():
            if callback: callback("Cancelled", 0)
            return ["Cancelled"]
        if callback:
            callback(f"Converting OSU: {os.path.basename(path)}", 30 + int((idx / max(1, len(osu_files))) * 30))
            
        try:
            from core.osu_parser import parse_osu
            osu_data = parse_osu(path)
            
            # Find matching audio
            audio_name = osu_data.get('audio_filename')
            if not audio_name: continue
            
            # Search in the same folder as .osu
            audio_full = os.path.join(os.path.dirname(path), audio_name)
            if not os.path.exists(audio_full):
                from core.utils import find_resource
                audio_full = find_resource(audio_name, hint_dirs=[os.path.dirname(path)])
            
            if not audio_full: continue
            
            # Unified .tur path
            safe_title = "".join([c for c in f"{osu_data['artist']} - {osu_data['title']}" if c.isalnum() or c in (' ', '-', '_')]).strip()
            tur_path = os.path.join(songs_dir, f"{safe_title}.tur")
            
            # Save the original OSU difficulty
            diff_name = osu_data['difficulty_name'].upper() or default_difficulty
            generator.save_tur(osu_data, tur_path, audio_path=audio_full, difficulty=diff_name, delete_original=False)
            
            # Generate all difficulties ONLY during explicit regeneration
            if force_regen:
                all_diffs = ["EASY", "MEDIUM", "HARD", "EXTREME", "FUCK YOU"]
                for gen_diff in all_diffs:
                    if gen_diff != diff_name:
                        try:
                            bm = generator._analyze_audio(audio_full, gen_diff)
                            generator.save_tur(bm, tur_path, audio_path=audio_full, difficulty=gen_diff, delete_original=False)
                        except:
                            pass
            
            converted_count += 1
            converted_osu_folders.add(os.path.dirname(path))
        except Exception as e:
            print(f"Failed to convert OSU {path}: {e}")

    # Third: Handle loose audio files (auto-generate if no .tur and no .osu)
    loose_audio = [f for f in all_files if f.lower().endswith(audio_extensions)]
    for idx, path in enumerate(loose_audio):
        if is_cancelled():
            if callback: callback("Cancelled", 0)
            return ["Cancelled"]
        if os.path.dirname(path) in converted_osu_folders:
            continue
            
        if callback:
             callback(f"Analyzing: {os.path.basename(path)}", 60 + int((idx / max(1, len(loose_audio))) * 20))
             
        base = os.path.splitext(os.path.basename(path))[0]
        tur_exists = False
        
        if not force_regen:
            for f in os.listdir(songs_dir):
                 if f.lower().endswith('.tur') and base.lower() in f.lower():
                      tur_exists = True
                      break
        
        if not tur_exists or force_regen:
            try:
                print(f"Generating auto-map for {os.path.basename(path)} (Force={force_regen})")
                safe_name = "".join([c for c in base if c.isalnum() or c in (' ', '-', '_')]).strip()
                tur_path = os.path.join(songs_dir, f"{safe_name}.tur")
                
                # During normal boot: only generate default difficulty (MEDIUM)
                # During force_regen: generate all 5 difficulties
                if force_regen:
                    for d in ["EASY", "MEDIUM", "HARD", "EXTREME", "FUCK YOU"]:
                        try:
                            generator.get_beatmap(path, d)
                        except: pass
                else:
                    try:
                        generator.get_beatmap(path, "MEDIUM")
                    except: pass
                
                if os.path.exists(tur_path):
                    try: os.remove(path)
                    except: pass
                
                converted_count += 1
            except: pass

    # Fourth: RE-GENERATE existing .tur files if force_regen is ON
    if force_regen:
        tur_files = []
        for root, dirs, files in os.walk(songs_dir):
            for f in files:
                if f.lower().endswith('.tur'):
                    tur_files.append(os.path.join(root, f))
                    
        for idx, tur_path in enumerate(tur_files):
            if is_cancelled():
                if callback: callback("Cancelled", 0)
                return ["Cancelled"]
            filename = os.path.basename(tur_path)
            if callback:
                callback(f"Re-Generating: {filename}", 80 + int((idx / max(1, len(tur_files))) * 15))
            
            try:
                # Load will extract the audio back to a file
                data = generator.load_tur(tur_path)
                audio_path = data.get('audio_path')
                
                if audio_path and os.path.exists(audio_path):
                    print(f"Re-analyzing {filename} from extracted audio...")
                    for d in ["EASY", "MEDIUM", "HARD", "EXTREME", "FUCK YOU"]:
                        try:
                            # analyze and merge into tur
                            bm = generator._analyze_audio(audio_path, d)
                            generator.save_tur(bm, tur_path, audio_path=audio_path, difficulty=d, delete_original=False)
                        except: pass
                    
                    # Cleanup extracted audio
                    try: os.remove(audio_path)
                    except: pass
                
                converted_count += 1
            except Exception as e:
                print(f"Fail re-gen {filename}: {e}")

    # Reset force_regen flag so it doesn't happen every time
    if force_regen:
        settings.set("auto_recreate_beatmaps", False)
        settings.save()

    # FINAL CLEANUP
    import shutil
    for folder in converted_osu_folders:
        try:
            if os.path.abspath(folder).startswith(os.path.abspath(songs_dir)) and folder != os.path.abspath(songs_dir):
                shutil.rmtree(folder)
        except Exception as e:
            print(f"Cleanup error for {folder}: {e}")

    if callback: callback("Ready", 100)
    return [f"Processed {converted_count} maps"]



def preload_all_songs(songs_dir="songs", callback=None):
    """
    Pre-load all .tur files into memory cache.
    """
    if not os.path.exists(songs_dir):
        return []
    
    songs = []
    
    # Use os.walk for recursive loading (needed for OSZ folders)
    tur_files = []
    for root, dirs, files in os.walk(songs_dir):
        # Skip internal folders
        if "__pycache__" in root: continue
        
        for f in files:
            if f.lower().endswith('.tur'):
                tur_files.append(os.path.join(root, f))
                
    total = len(tur_files)
    
    for idx, filepath in enumerate(tur_files):
        filename = os.path.basename(filepath)
        if callback:
            callback(f"Loading {idx+1}/{total}: {filename[:30]}")
        
        try:
            # Use generator to load for consistent parsing
            gen = BeatmapGenerator()
            # Just load generic metadata initially
            data = gen.load_tur(filepath, "MEDIUM")
            
            songs.append({
                'tur_file': filename,
                'path': filepath,
                'audio': data.get('audio_path', ''),
                'title': data.get('title', filename[:-4]),
                'artist': data.get('artist', 'Unknown'),
                'difficulty': 'MULTI', # Indicates unified
                'all_difficulties': data.get('all_difficulties', ['MEDIUM']),
                'bpm': data.get('bpm', 120),
                'duration': data.get('duration', 0)
            })
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
    
    return songs


def get_tur_songs(songs_dir="songs"):
    # Simplified wrapper
    return preload_all_songs(songs_dir)

