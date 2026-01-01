"""
GitHub Actions Auto-Updater
Checks for new builds from GitHub Actions and allows downloading updates.
Supports multiple update sources: GitHub, Itch.io (dummy), or disabled.
"""

import os
import sys
import json
import platform
import threading
import time
import urllib.request
import urllib.error
import hashlib
from datetime import datetime

# Configuration - Update these for your repository
GITHUB_OWNER = "PlayTUR"      # Organization
GITHUB_REPO = "RELEASES"      # Releases repository

# Direct update server (for hash-verified updates)
UPDATE_SERVER_URL = "http://154.53.35.148/updates/"

# Update source options
UPDATE_SOURCE_GITHUB = "github"
UPDATE_SOURCE_ITCHIO = "itchio"  # Dummy/simulation
UPDATE_SOURCE_DISABLED = "disabled"


class Updater:
    def __init__(self, source=None):
        """
        Initialize updater with specified source.
        source: 'github', 'itchio', or 'disabled'
        """
        self.source = source or UPDATE_SOURCE_GITHUB
        self.current_version = self._load_local_version()
        self.remote_version = None
        self.remote_build_info = None
        self.update_available = False
        self.is_checking = False
        self.is_downloading = False
        self.download_progress = 0
        self.status_message = ""
        self.error_message = ""
        
        # Paths
        self.version_file = self._get_version_file_path()
        self.update_dir = self._get_update_dir()
    
    def set_source(self, source):
        """Change the update source"""
        self.source = source
        self.update_available = False
        self.remote_version = None
        self.remote_build_info = None
        self.error_message = ""
        self.status_message = ""
        
    def _get_version_file_path(self):
        """Get path to version file"""
        # Check in app directory first
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(app_dir, ".build_version")
    
    def _get_update_dir(self):
        """Get temporary update directory"""
        if platform.system() == "Windows":
            return os.path.join(os.environ.get("TEMP", "."), "TUR_update")
        else:
            return "/tmp/TUR_update"
    
    def _load_local_version(self):
        """Load local build version/timestamp"""
        version_file = self._get_version_file_path()
        try:
            if os.path.exists(version_file):
                with open(version_file, 'r') as f:
                    data = f.read().strip()
                    try:
                        info = json.loads(data)
                        return info.get("build_time", "unknown")
                    except:
                        return data
        except Exception as e:
            print(f"Error loading version: {e}")
        return "unknown"
    
    def _get_platform_artifact_name(self):
        """Get the artifact name for current platform"""
        system = platform.system()
        if system == "Windows":
            return "TUR-Windows"
        elif system == "Linux":
            return "TUR-Linux"
        else:
            return None
    
    def _get_binary_filename(self):
        """Get the expected binary filename for current platform"""
        system = platform.system()
        if system == "Windows":
            return "TUR.exe"
        elif system == "Linux":
            return "TUR"
        else:
            return None
    
    def _get_file_hash(self, filepath):
        """Calculate SHA256 hash of a file"""
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _verify_and_download(self, filename, progress_callback=None):
        """
        Download file with SHA256 verification.
        Returns path to verified file, or None if verification fails.
        """
        # 1. Download the expected hash from the server
        if progress_callback:
            progress_callback("status", "Fetching integrity signature...")
        
        try:
            hash_url = f"{UPDATE_SERVER_URL}{filename}.sha256"
            hash_req = urllib.request.Request(hash_url)
            hash_req.add_header("User-Agent", "TUR-Game-Updater")
            
            with urllib.request.urlopen(hash_req, timeout=15) as response:
                hash_content = response.read().decode().strip()
                expected_hash = hash_content.split()[0]  # Get just the hash string
        except urllib.error.HTTPError as e:
            if e.code == 404:
                self.error_message = "Security Error: Hash signature not found"
            else:
                self.error_message = f"Hash fetch failed: HTTP {e.code}"
            return None
        except Exception as e:
            self.error_message = f"Hash fetch failed: {str(e)[:30]}"
            return None
        
        # 2. Download the actual binary
        if progress_callback:
            progress_callback("status", "Downloading update...")
        
        try:
            binary_url = f"{UPDATE_SERVER_URL}{filename}"
            binary_req = urllib.request.Request(binary_url)
            binary_req.add_header("User-Agent", "TUR-Game-Updater")
            
            # Create update directory
            os.makedirs(self.update_dir, exist_ok=True)
            temp_file = os.path.join(self.update_dir, filename + ".tmp")
            
            with urllib.request.urlopen(binary_req, timeout=120) as response:
                total_size = int(response.headers.get('Content-Length', 0))
                downloaded = 0
                
                with open(temp_file, 'wb') as f:
                    while True:
                        chunk = response.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0 and progress_callback:
                            pct = int(downloaded * 100 / total_size)
                            progress_callback("progress", pct)
                            
        except Exception as e:
            self.error_message = f"Download failed: {str(e)[:30]}"
            if os.path.exists(temp_file):
                os.remove(temp_file)
            return None
        
        # 3. Verify the hash
        if progress_callback:
            progress_callback("status", "Verifying integrity...")
        
        actual_hash = self._get_file_hash(temp_file)
        
        if actual_hash == expected_hash:
            if progress_callback:
                progress_callback("status", "Signature verified!")
            return temp_file
        else:
            self.error_message = "SECURITY ALERT: Hash mismatch! Update rejected."
            os.remove(temp_file)
            return None
    
    def check_for_updates(self, callback=None):
        """
        Check for updates based on configured source.
        Returns True if update available, False otherwise.
        """
        if self.source == UPDATE_SOURCE_DISABLED:
            self.status_message = "Updates disabled"
            return False
        elif self.source == UPDATE_SOURCE_ITCHIO:
            return self._check_itchio(callback)
        else:
            return self._check_github(callback)
    
    def _check_itchio(self, callback=None):
        """
        Dummy itch.io update check (simulated).
        Always returns no update available.
        """
        self.is_checking = True
        self.status_message = "Checking itch.io..."
        
        # Simulate network delay
        time.sleep(0.5)
        
        # Itch.io is dummy - always up to date
        self.update_available = False
        self.status_message = "Up to date (itch.io)"
        self.remote_version = self.current_version
        self.remote_build_info = {
            "source": "itchio",
            "message": "Itch.io updates coming soon!"
        }
        
        self.is_checking = False
        
        if callback:
            callback(False)
        return False
    
    def _check_github(self, callback=None):
        """
        Check GitHub Releases for newer versions.
        Returns True if update available, False otherwise.
        """
        if self.is_checking:
            return False
            
        self.is_checking = True
        self.error_message = ""
        self.status_message = "Checking for updates..."
        
        try:
            # Get latest release from PlayTUR/RELEASES
            api_url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
            
            req = urllib.request.Request(api_url)
            req.add_header("Accept", "application/vnd.github.v3+json")
            req.add_header("User-Agent", "TUR-Game-Updater")
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
            
            remote_tag = data.get("tag_name", "")
            remote_time = data.get("published_at", "")
            
            # Find Windows asset
            download_url = None
            for asset in data.get("assets", []):
                if "Windows" in asset["name"] or asset["name"].endswith(".zip"):
                    download_url = asset["browser_download_url"]
                    break
            
            self.remote_version = remote_tag
            self.remote_build_info = {
                "source": "github",
                "tag": remote_tag,
                "published_at": remote_time,
                "html_url": data.get("html_url", ""),
                "download_url": download_url,
                "body": data.get("body", "")[:200]
            }
            
            # Compare versions - check if remote tag differs from local
            local_version = self._get_local_tag()
            
            if local_version == "unknown" or local_version != remote_tag:
                self.update_available = True
                self.status_message = f"New version: {remote_tag}"
            else:
                self.update_available = False
                self.status_message = "You have the latest version"
            
            if callback:
                callback(self.update_available)
                
            return self.update_available
            
        except urllib.error.HTTPError as e:
            if e.code == 404:
                self.error_message = "No releases found"
            elif e.code == 403:
                self.error_message = "API rate limited - try later"
            else:
                self.error_message = f"HTTP Error: {e.code}"
        except urllib.error.URLError as e:
            self.error_message = "Network error - check connection"
        except Exception as e:
            self.error_message = f"Check failed: {str(e)[:30]}"
        finally:
            self.is_checking = False
            
        return False
    
    def _get_local_tag(self):
        """Get local version tag from .build_version"""
        version_file = self._get_version_file_path()
        try:
            if os.path.exists(version_file):
                with open(version_file, 'r') as f:
                    data = json.loads(f.read().strip())
                    return data.get("version", "unknown")
        except:
            pass
        return "unknown"
    
    def check_for_updates_async(self, callback=None):
        """Check for updates in background thread"""
        def check_thread():
            result = self.check_for_updates()
            if callback:
                callback(result)
        
        thread = threading.Thread(target=check_thread, daemon=True)
        thread.start()
    
    def get_artifacts(self, run_id):
        """Get list of artifacts for a workflow run"""
        try:
            api_url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/actions/runs/{run_id}/artifacts"
            
            req = urllib.request.Request(api_url)
            req.add_header("Accept", "application/vnd.github.v3+json")
            req.add_header("User-Agent", "TUR-Game-Updater")
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                
            return data.get("artifacts", [])
        except Exception as e:
            print(f"Error getting artifacts: {e}")
            return []
    
    def perform_update(self):
        """
        Download and install update from GitHub releases with hash verification.
        Yields progress 0-100.
        """
        if self.source == UPDATE_SOURCE_ITCHIO:
            self.status_message = "Itch.io updates coming soon!"
            for i in range(0, 101, 10):
                time.sleep(0.1)
                yield i
            return
        
        self.is_downloading = True
        self.download_progress = 0
        
        try:
            if not self.remote_build_info or not self.remote_build_info.get("download_url"):
                self.error_message = "No download URL available"
                yield 0
                return
            
            download_url = self.remote_build_info["download_url"]
            filename = download_url.split("/")[-1]  # e.g., TUR-Windows-private-beta-1.zip
            hash_url = download_url + ".sha256"
            
            os.makedirs(self.update_dir, exist_ok=True)
            temp_file = os.path.join(self.update_dir, filename + ".tmp")
            
            yield 5
            self.status_message = "Fetching integrity signature..."
            
            # 1. Download SHA256 hash
            try:
                req = urllib.request.Request(hash_url)
                req.add_header("User-Agent", "TUR-Game-Updater")
                with urllib.request.urlopen(req, timeout=15) as response:
                    hash_content = response.read().decode().strip()
                    expected_hash = hash_content.split()[0].lower()
            except Exception as e:
                self.error_message = f"Hash not found: {str(e)[:30]}"
                yield 0
                return
            
            yield 10
            self.status_message = "Downloading update..."
            
            # 2. Download the ZIP
            try:
                req = urllib.request.Request(download_url)
                req.add_header("User-Agent", "TUR-Game-Updater")
                
                with urllib.request.urlopen(req, timeout=300) as response:
                    total_size = int(response.headers.get('Content-Length', 0))
                    downloaded = 0
                    
                    with open(temp_file, 'wb') as f:
                        while True:
                            chunk = response.read(8192)
                            if not chunk:
                                break
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            if total_size > 0:
                                pct = 10 + int(downloaded * 70 / total_size)
                                self.download_progress = pct
                                yield pct
            except Exception as e:
                self.error_message = f"Download failed: {str(e)[:30]}"
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                yield 0
                return
            
            yield 85
            self.status_message = "Verifying integrity..."
            
            # 3. Verify hash
            actual_hash = self._get_file_hash(temp_file)
            
            if actual_hash.lower() != expected_hash:
                self.error_message = "SECURITY ALERT: Hash mismatch! Update rejected."
                os.remove(temp_file)
                yield 0
                return
            
            yield 90
            self.status_message = "Signature verified!"
            
            # 4. Rename to final
            final_path = os.path.join(self.update_dir, filename)
            if os.path.exists(final_path):
                os.remove(final_path)
            os.rename(temp_file, final_path)
            
            self.status_message = f"Update downloaded! Extract: {final_path}"
            yield 100
            
        except Exception as e:
            self.error_message = f"Update failed: {str(e)[:40]}"
            yield 0
        finally:
            self.is_downloading = False
    
    def restart_game(self):
        """Restart the game application"""
        print("Restarting application...")
        try:
            python = sys.executable
            os.execl(python, python, *sys.argv)
        except Exception as e:
            print(f"Restart failed: {e}")
            sys.exit(0)


# Global instance
_updater = None

def get_updater(source=None):
    """Get or create global Updater instance"""
    global _updater
    if _updater is None:
        _updater = Updater(source)
    elif source and _updater.source != source:
        _updater.set_source(source)
    return _updater

def get_update_sources():
    """Get list of available update sources"""
    return [
        (UPDATE_SOURCE_GITHUB, "GitHub Actions"),
        (UPDATE_SOURCE_ITCHIO, "Itch.io (Coming Soon)"),
        (UPDATE_SOURCE_DISABLED, "Disabled"),
    ]
