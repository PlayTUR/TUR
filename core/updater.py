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
from datetime import datetime

# Configuration - Update these for your repository
GITHUB_OWNER = "PlayTUR"  # Your GitHub username
GITHUB_REPO = "TUR"     # Your repository name

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
        Check GitHub Actions for newer builds.
        Returns True if update available, False otherwise.
        """
        if self.is_checking:
            return False
            
        self.is_checking = True
        self.error_message = ""
        self.status_message = "Checking GitHub..."
        
        try:
            # Get latest successful workflow run
            api_url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/actions/runs?status=success&per_page=1"
            
            req = urllib.request.Request(api_url)
            req.add_header("Accept", "application/vnd.github.v3+json")
            req.add_header("User-Agent", "TUR-Game-Updater")
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                
            if not data.get("workflow_runs"):
                self.status_message = "No builds found"
                self.is_checking = False
                return False
            
            latest_run = data["workflow_runs"][0]
            remote_time = latest_run.get("created_at", "")
            run_id = latest_run.get("id")
            
            self.remote_version = remote_time
            self.remote_build_info = {
                "source": "github",
                "run_id": run_id,
                "created_at": remote_time,
                "html_url": latest_run.get("html_url", ""),
                "head_sha": latest_run.get("head_sha", "")[:7]
            }
            
            # Compare versions
            if self.current_version == "unknown":
                self.update_available = True
                self.status_message = "New version available!"
            else:
                try:
                    local_dt = datetime.fromisoformat(self.current_version.replace("Z", "+00:00"))
                    remote_dt = datetime.fromisoformat(remote_time.replace("Z", "+00:00"))
                    self.update_available = remote_dt > local_dt
                    
                    if self.update_available:
                        self.status_message = "New version available!"
                    else:
                        self.status_message = "You have the latest version"
                except:
                    self.update_available = self.current_version != remote_time
                    self.status_message = "New version available!" if self.update_available else "Up to date"
            
            if callback:
                callback(self.update_available)
                
            return self.update_available
            
        except urllib.error.HTTPError as e:
            if e.code == 404:
                self.error_message = "Repository not found"
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
        Download and install update.
        Yields progress 0-100.
        """
        if self.source == UPDATE_SOURCE_ITCHIO:
            # Itch.io is dummy - just simulate
            self.status_message = "Itch.io updates coming soon!"
            for i in range(0, 101, 10):
                time.sleep(0.1)
                yield i
            return
        
        if not self.remote_build_info:
            self.error_message = "No update info available"
            yield 0
            return
            
        self.is_downloading = True
        self.download_progress = 0
        
        try:
            run_id = self.remote_build_info.get("run_id")
            artifact_name = self._get_platform_artifact_name()
            
            if not artifact_name:
                self.error_message = "Unsupported platform"
                yield 0
                return
            
            self.status_message = "Fetching artifact info..."
            yield 5
            
            # Get artifacts list
            artifacts = self.get_artifacts(run_id)
            
            # Find matching artifact
            target_artifact = None
            for artifact in artifacts:
                if artifact.get("name") == artifact_name:
                    target_artifact = artifact
                    break
            
            if not target_artifact:
                self.error_message = f"Artifact '{artifact_name}' not found"
                yield 0
                return
            
            self.status_message = "Download from GitHub Actions page"
            yield 10
            
            # Simulate progress (actual download requires auth)
            for i in range(10, 100, 5):
                time.sleep(0.05)
                self.download_progress = i
                yield i
            
            self.status_message = "Open GitHub to download manually"
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
