"""
Song Downloader for TUR
<<<<<<< HEAD
Download songs from YouTube and other sources using yt-dlp.
"""

import os
import subprocess
import threading
import hashlib
import platform
import stat
import urllib.request


class SongDownloader:
    def __init__(self, songs_dir="songs"):
        self.songs_dir = songs_dir
        os.makedirs(songs_dir, exist_ok=True)
        self.downloading = False
        self.download_progress = 0
        self.download_total = 100
        self.download_error = ""
        self.download_filename = ""
        self.status_text = ""
        self.ytdlp_path = "yt-dlp" # Default system path
        self.queue = []
        self.current_idx = 0
        self.total_in_batch = 0
    
    def get_local_songs(self):
        songs = []
        if os.path.exists(self.songs_dir):
            for f in os.listdir(self.songs_dir):
                if f.lower().endswith(('.mp3', '.wav', '.ogg', '.m4a', '.webm')):
                    songs.append({'filename': f, 'name': os.path.splitext(f)[0].replace('_', ' ').title()})
        return songs
    
    def download_from_url(self, url, filename=None):
        if self.downloading:
            return False
        self.queue = [url]
        self.current_idx = 0
        self.total_in_batch = 1
        self.downloading = True
        self.download_progress = 0
        self.download_error = ""
        self.status_text = "Starting download..."
        threading.Thread(target=self._download_queue_thread, args=(filename,), daemon=True).start()
        return True

    def download_batch(self, urls):
        if self.downloading or not urls:
            return False
        self.queue = urls
        self.current_idx = 0
        self.total_in_batch = len(urls)
        self.downloading = True
        self.download_progress = 0
        self.download_error = ""
        self.status_text = f"Preparing batch (0/{len(urls)})..."
        threading.Thread(target=self._download_queue_thread, daemon=True).start()
        return True

    def _download_queue_thread(self, single_filename=None):
        for idx, url in enumerate(self.queue):
            self.current_idx = idx + 1
            self.status_text = f"({self.current_idx}/{self.total_in_batch}) Initializing..."
            try:
                self._download_thread_worker(url, single_filename if self.total_in_batch == 1 else None)
            except Exception as e:
                print(f"Batch Error on {url}: {e}")
                self.download_error = f"Error on song {idx+1}"
            
            if self.download_error and self.total_in_batch == 1:
                break # Stop if single download failed
        
        self.downloading = False
        if not self.download_error:
            self.status_text = f"Batch complete! ({self.total_in_batch} songs)"
    
    def _ensure_ytdlp(self):
        """Check for yt-dlp and download if missing"""
        # 1. Check system path
        try:
            # Silence the check
            subprocess.run(["yt-dlp", "--version"], capture_output=True, check=True)
            self.ytdlp_path = "yt-dlp"
            return True
        except:
            pass
        
        # 2. Check local binary in tools/ directory
        tools_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools")
        os.makedirs(tools_dir, exist_ok=True)
        
        system = platform.system()
        local_bin_name = "yt-dlp.exe" if system == "Windows" else "yt-dlp"
        local_bin_path = os.path.join(tools_dir, local_bin_name)
        
        if os.path.exists(local_bin_path):
            self.ytdlp_path = local_bin_path
            return True
        
        # 3. Download if missing
        self.status_text = "Downloading yt-dlp system..."
        print(f"yt-dlp not found. Attempting to download standalone binary to {local_bin_path}...")
        
        try:
            # Point to the official standalone binaries on GitHub
            # Windows: yt-dlp.exe, Linux: yt-dlp
            url = f"https://github.com/yt-dlp/yt-dlp/releases/latest/download/{local_bin_name}"
            
            # Use a more modern request if possible, but urllib is fine for absolute basics
            with urllib.request.urlopen(url) as response, open(local_bin_path, 'wb') as out_file:
                data = response.read()
                out_file.write(data)
            
            if system != "Windows":
                # Ensure executable bit is set on Linux/MacOS
                st = os.stat(local_bin_path)
                os.chmod(local_bin_path, st.st_mode | stat.S_IEXEC)
            
            self.ytdlp_path = local_bin_path
            print("yt-dlp downloaded and configured successfully!")
            return True
        except Exception as e:
            self.download_error = f"Binary fetch failed: {e}"
            print(f"ERROR: Could not auto-download yt-dlp: {e}")
            return False

    def _download_thread_worker(self, url, filename):
        try:
            # Ensure yt-dlp is available
            if not self._ensure_ytdlp():
                return
            
            # Generate filename if not provided
            if not filename:
                # Try to get clean title if possible, else use hash
                filename = f"song_{hashlib.md5(url.encode()).hexdigest()[:8]}"
            
            # Remove extension if provided (yt-dlp adds it)
            filename = os.path.splitext(filename)[0]
            
            output_template = os.path.join(self.songs_dir, f"{filename}.%(ext)s")
            
            batch_prefix = f"({self.current_idx}/{self.total_in_batch}) " if self.total_in_batch > 1 else ""
            self.status_text = f"{batch_prefix}Downloading audio..."
            self.download_progress = 10
            
            # Use yt-dlp to download audio
            cmd = [
                self.ytdlp_path,
                "-x",  # Extract audio
                "--audio-format", "mp3",
                "--audio-quality", "0",  # Best quality
                "-o", output_template,
                "--no-playlist",  # Don't download playlists
                "--progress",
                url
            ]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            
            # Monitor progress
            for line in process.stdout:
                if "[download]" in line and "%" in line:
                    try:
                        pct = line.split("%")[0].split()[-1]
                        self.download_progress = int(float(pct))
                        self.status_text = f"{batch_prefix}Downloading: {self.download_progress}%"
                    except:
                        pass
                elif "Destination" in line:
                    self.status_text = f"{batch_prefix}Converting to MP3..."
                    self.download_progress = 90
            
            process.wait()
            
            if process.returncode == 0:
                # Find the downloaded file
                for f in os.listdir(self.songs_dir):
                    if f.startswith(filename) and f.endswith(('.mp3', '.m4a', '.webm', '.wav')):
                        self.download_filename = f
                        break
                
                self.download_progress = 100
                self.status_text = f"{batch_prefix}Done: {self.download_filename}"
            else:
                self.download_error = "Download failed. Check URL."
            
        except Exception as e:
            self.download_error = str(e)[:50]


class BeatmapGenerator:
    def generate_beatmap(self, song_path, difficulty="MEDIUM", bpm=120):
        import random
        try:
            duration = os.path.getsize(song_path) / 10000
        except:
            duration = 180
        
        nps = {"EASY": 2, "MEDIUM": 4, "HARD": 6, "EXTREME": 10}.get(difficulty, 4)
        notes = []
        t = 2.0
        while t < duration - 2:
            if random.random() < 0.8:
                notes.append({'time': round(t, 3), 'lane': random.randint(0, 3), 'type': 'tap'})
            t += 1.0 / nps * random.uniform(0.8, 1.2)
        return {'song': os.path.basename(song_path), 'difficulty': difficulty, 'notes': notes}
=======
Download songs from free sources and auto-generate beatmaps.
"""

import os
import urllib.request
import urllib.parse
import json
import threading
import hashlib


class SongDownloader:
    """Download and manage songs from online sources"""
    
    def __init__(self, songs_dir="songs"):
        self.songs_dir = songs_dir
        os.makedirs(songs_dir, exist_ok=True)
        
        # Download state
        self.downloading = False
        self.download_progress = 0
        self.download_total = 0
        self.download_error = ""
        self.download_filename = ""
        
        # Available songs (could be fetched from a server)
        self.available_songs = []
        self.last_refresh = 0
    
    def get_local_songs(self):
        """Get list of locally downloaded songs"""
        songs = []
        if os.path.exists(self.songs_dir):
            for f in os.listdir(self.songs_dir):
                if f.lower().endswith(('.mp3', '.wav', '.ogg')):
                    path = os.path.join(self.songs_dir, f)
                    songs.append({
                        'filename': f,
                        'path': path,
                        'size': os.path.getsize(path),
                        'name': os.path.splitext(f)[0].replace('_', ' ').title()
                    })
        return songs
    
    def download_from_url(self, url, filename=None):
        """Download a song from URL"""
        if self.downloading:
            return False
        
        self.downloading = True
        self.download_progress = 0
        self.download_error = ""
        
        threading.Thread(target=self._download_thread, args=(url, filename), daemon=True).start()
        return True
    
    def _download_thread(self, url, filename):
        try:
            # Parse filename from URL if not provided
            if not filename:
                parsed = urllib.parse.urlparse(url)
                filename = os.path.basename(parsed.path)
                if not filename:
                    filename = f"song_{hashlib.md5(url.encode()).hexdigest()[:8]}.mp3"
            
            self.download_filename = filename
            filepath = os.path.join(self.songs_dir, filename)
            
            # Create request with headers to avoid blocks
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            # Download with progress
            with urllib.request.urlopen(req, timeout=30) as response:
                self.download_total = int(response.headers.get('Content-Length', 0))
                
                with open(filepath, 'wb') as f:
                    while True:
                        chunk = response.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)
                        self.download_progress += len(chunk)
            
            self.download_filename = filename
            
        except Exception as e:
            self.download_error = str(e)
            print(f"Download error: {e}")
        finally:
            self.downloading = False
    
    def get_download_status(self):
        """Get current download status"""
        if self.download_total > 0:
            pct = int(100 * self.download_progress / self.download_total)
        else:
            pct = 0
        
        return {
            'downloading': self.downloading,
            'progress': self.download_progress,
            'total': self.download_total,
            'percent': pct,
            'filename': self.download_filename,
            'error': self.download_error
        }


class BeatmapGenerator:
    """Generate simple beatmaps from audio analysis"""
    
    def __init__(self):
        self.difficulties = {
            'EASY': {'notes_per_second': 2, 'lanes': [1, 2]},
            'MEDIUM': {'notes_per_second': 4, 'lanes': [0, 1, 2, 3]},
            'HARD': {'notes_per_second': 6, 'lanes': [0, 1, 2, 3]},
            'EXTREME': {'notes_per_second': 10, 'lanes': [0, 1, 2, 3]}
        }
    
    def generate_beatmap(self, song_path, difficulty="MEDIUM", bpm=None):
        """Generate beatmap for a song"""
        import random
        
        # Get song duration (estimate from file size if we can't analyze)
        try:
            size = os.path.getsize(song_path)
            # Rough estimate: ~10KB per second for MP3
            duration = size / 10000
        except:
            duration = 180  # Default 3 minutes
        
        settings = self.difficulties.get(difficulty, self.difficulties['MEDIUM'])
        notes_per_second = settings['notes_per_second']
        lanes = settings['lanes']
        
        # Generate notes
        notes = []
        current_time = 2.0  # Start after 2 seconds
        
        # Use BPM if provided for more musical timing
        if bpm:
            beat_interval = 60.0 / bpm
        else:
            beat_interval = 1.0 / notes_per_second
        
        while current_time < duration - 2:
            # Add some variation
            if random.random() < 0.8:  # 80% chance of note
                lane = random.choice(lanes)
                notes.append({
                    'time': round(current_time, 3),
                    'lane': lane,
                    'type': 'tap'
                })
            
            # Occasionally add double notes on higher difficulties
            if difficulty in ['HARD', 'EXTREME'] and random.random() < 0.2:
                other_lanes = [l for l in lanes if l != lane]
                if other_lanes:
                    notes.append({
                        'time': round(current_time, 3),
                        'lane': random.choice(other_lanes),
                        'type': 'tap'
                    })
            
            current_time += beat_interval * random.uniform(0.8, 1.2)
        
        return {
            'song': os.path.basename(song_path),
            'difficulty': difficulty,
            'notes': notes,
            'duration': duration
        }
    
    def save_beatmap(self, beatmap, filepath):
        """Save beatmap to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(beatmap, f, indent=2)
    
    def load_beatmap(self, filepath):
        """Load beatmap from JSON file"""
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)
        return None


# Simple test
if __name__ == "__main__":
    dl = SongDownloader()
    print("Local songs:", dl.get_local_songs())
    
    gen = BeatmapGenerator()
    # Example beatmap generation
    if dl.get_local_songs():
        song = dl.get_local_songs()[0]
        beatmap = gen.generate_beatmap(song['path'], 'MEDIUM')
        print(f"Generated {len(beatmap['notes'])} notes for {song['name']}")
>>>>>>> 0dc16cc (use code wyind in the fortnite item shop)
