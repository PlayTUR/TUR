"""
Playit Manager - Free TCP tunneling via playit.gg
Manages the playit binary for creating free game server tunnels.
Auto-downloads the binary if missing!

How it works:
1. First run: Downloads playit binary automatically
2. Playit generates a claim code to link to your (free) playit.gg account
3. After claiming: Tunnels are created automatically
4. Share the tunnel address (like abc123.playit.gg:12345) with friends
"""

import subprocess
import threading
import platform
import time
import os
import re
import urllib.request

# Download URLs for playit binaries
PLAYIT_VERSION = "0.15.26"
PLAYIT_URLS = {
    "Windows": f"https://github.com/playit-cloud/playit-agent/releases/download/v{PLAYIT_VERSION}/playit-windows-x86_64-signed.exe",
    "Linux": f"https://github.com/playit-cloud/playit-agent/releases/download/v{PLAYIT_VERSION}/playit-linux-amd64",
}


class PlayitManager:
    def __init__(self):
        self.process = None
        self.tunnel_address = None
        self.claim_code = None
        self.error_message = ""
        self.status_message = ""
        self.is_running = False
        self.is_claimed = False
        self.is_downloading = False
        
        # Output buffer
        self._output_lines = []
        self._lock = threading.Lock()
        
        # Config file location
        self.config_dir = self._get_config_dir()
        self.config_file = os.path.join(self.config_dir, "playit.toml")
        
        # Tools directory
        self.tools_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tools")
        
        # Find or download the playit binary
        self.binary_path = self._find_binary()
    
    def _get_config_dir(self):
        """Get config directory for playit"""
        if platform.system() == "Windows":
            return os.path.join(os.environ.get("APPDATA", "."), "TUR")
        else:
            return os.path.expanduser("~/.config/TUR")
    
    def _get_binary_name(self):
        """Get the expected binary name for this platform"""
        if platform.system() == "Windows":
            return "playit.exe"
        else:
            return "playit"
    
    def _find_binary(self):
        """Find the playit binary for the current platform"""
        system = platform.system()
        binary_name = self._get_binary_name()
        
        # Check in tools/ directory first
        tools_path = os.path.join(self.tools_dir, binary_name)
        if os.path.isfile(tools_path):
            if system != "Windows":
                try:
                    os.chmod(tools_path, 0o755)
                except:
                    pass
            return os.path.abspath(tools_path)
        
        # Check current directory
        if os.path.isfile(binary_name):
            if system != "Windows":
                try:
                    os.chmod(binary_name, 0o755)
                except:
                    pass
            return os.path.abspath(binary_name)
        
        # Check system paths on Linux
        if system != "Windows":
            for path in ["/usr/bin/playit", "/usr/local/bin/playit"]:
                if os.path.isfile(path):
                    return path
        
        return None
    
    def _download_binary(self):
        """Download the playit binary for the current platform"""
        system = platform.system()
        
        if system not in PLAYIT_URLS:
            self.error_message = f"Unsupported platform: {system}"
            return False
        
        url = PLAYIT_URLS[system]
        binary_name = self._get_binary_name()
        
        # Create tools directory
        os.makedirs(self.tools_dir, exist_ok=True)
        dest_path = os.path.join(self.tools_dir, binary_name)
        
        self.status_message = "Downloading playit..."
        self.is_downloading = True
        
        try:
            print(f"Downloading playit from {url}...")
            
            # Download with progress
            urllib.request.urlretrieve(url, dest_path)
            
            # Make executable on Linux
            if system != "Windows":
                os.chmod(dest_path, 0o755)
            
            self.binary_path = os.path.abspath(dest_path)
            self.status_message = "Download complete!"
            print(f"Downloaded playit to {dest_path}")
            return True
            
        except Exception as e:
            self.error_message = f"Download failed: {str(e)[:40]}"
            print(f"Failed to download playit: {e}")
            return False
        finally:
            self.is_downloading = False
    
    def is_available(self):
        """Check if playit binary is available (or can be downloaded)"""
        # Can always try to download
        return True
    
    def ensure_binary(self):
        """Ensure binary exists, download if needed"""
        if self.binary_path:
            return True
        return self._download_binary()
    
    def is_setup_complete(self):
        """Check if playit has been claimed/setup"""
        return os.path.exists(self.config_file)
    
    def start_tunnel(self, local_port=1337):
        """
        Start playit tunnel to the specified local port.
        Returns True if started successfully (or starting in background).
        """
        if self.is_running:
            return True
        
        if self.is_downloading:
            return True  # Already downloading
        
        self.error_message = ""
        self.status_message = "Starting..."
        self.tunnel_address = None
        self.claim_code = None
        
        # Start in background thread so UI can update
        threading.Thread(target=self._start_tunnel_thread, args=(local_port,), daemon=True).start()
        return True
    
    def _start_tunnel_thread(self, local_port):
        """Background thread for downloading and starting playit"""
        # Download binary if needed
        if not self.binary_path:
            self.is_downloading = True
            self.status_message = "Downloading..."
            
            system = platform.system()
            if system not in PLAYIT_URLS:
                self.error_message = f"Unsupported platform: {system}"
                self.is_downloading = False
                return
            
            url = PLAYIT_URLS[system]
            binary_name = self._get_binary_name()
            
            # Create tools directory
            os.makedirs(self.tools_dir, exist_ok=True)
            dest_path = os.path.join(self.tools_dir, binary_name)
            
            try:
                print(f"Downloading from {url}...")
                urllib.request.urlretrieve(url, dest_path)
                
                # Make executable on Linux
                if system != "Windows":
                    os.chmod(dest_path, 0o755)
                
                self.binary_path = os.path.abspath(dest_path)
                self.status_message = "Download complete!"
                print(f"Downloaded to {dest_path}")
                
            except Exception as e:
                self.error_message = f"Download failed: {str(e)[:40]}"
                print(f"Download failed: {e}")
                self.is_downloading = False
                return
            finally:
                self.is_downloading = False
        
        # Now start the actual playit process
        self.status_message = "Connecting..."
        
        # Ensure config directory exists
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Build command with -s for stdout output
        cmd = [
            self.binary_path,
            "-s",  # Output to stdout
            "--secret_path", self.config_file,  # config_file is already absolute
        ]
        
        print(f"Running: {' '.join(cmd)}")
        
        try:
            # Start the process
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                text=True,
                bufsize=1,  # Line buffered
            )
            
            self.is_running = True
            
            # Read output in this thread
            self._read_output()
            
        except FileNotFoundError:
            self.error_message = "Binary not found"
        except PermissionError:
            self.error_message = "Permission denied - check file permissions"
        except Exception as e:
            self.error_message = f"Failed to start: {str(e)[:40]}"
    
    def _read_output(self):
        """Read output from playit process"""
        try:
            for line in self.process.stdout:
                line = line.strip()
                if not line:
                    continue
                
                with self._lock:
                    self._output_lines.append(line)
                    # Keep last 100 lines
                    if len(self._output_lines) > 100:
                        self._output_lines.pop(0)
                
                print(f"[playit] {line}")  # Debug output
                
                # Parse for claim code
                # Look for URL like https://playit.gg/claim/XXXXXX
                claim_url_match = re.search(r'playit\.gg/claim/([A-Za-z0-9-]+)', line, re.IGNORECASE)
                if claim_url_match and not self.is_claimed:
                    self.claim_code = claim_url_match.group(1)
                    self.status_message = f"Claim at: playit.gg/claim/{self.claim_code}"
                
                # Also check for "claim code: XXX" format
                claim_match = re.search(r'claim[:\s]+([A-Za-z0-9-]+)', line, re.IGNORECASE)
                if claim_match and not self.is_claimed and not self.claim_code:
                    self.claim_code = claim_match.group(1)
                    self.status_message = f"Claim code: {self.claim_code}"
                
                # Parse for tunnel address
                # Format: "abc123.playit.gg:12345" or with subdomains
                tunnel_match = re.search(r'([a-z0-9-]+(?:\.[a-z0-9-]+)*\.playit\.gg:\d+)', line, re.IGNORECASE)
                if tunnel_match:
                    self.tunnel_address = tunnel_match.group(1)
                    self.is_claimed = True
                    self.claim_code = None  # Clear claim code once we have tunnel
                    self.status_message = f"Tunnel ready: {self.tunnel_address}"
                
                # Check for "claimed" or "connected" message
                if "claimed" in line.lower() or "connected" in line.lower():
                    self.is_claimed = True
                
                # Check for errors
                if "error" in line.lower() and "tunnel" not in line.lower():
                    self.error_message = line[:60]
                    
        except Exception as e:
            print(f"Playit output reader error: {e}")
        finally:
            self.is_running = False
    
    def get_tunnel_address(self):
        """Get the current tunnel address if available"""
        return self.tunnel_address
    
    def get_claim_code(self):
        """Get the claim code if account needs to be linked"""
        return self.claim_code if not self.is_claimed else None
    
    def stop(self):
        """Stop the playit process - force kill if needed"""
        self.is_running = False
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=2)
            except:
                pass
            try:
                self.process.kill()
            except:
                pass
        self.process = None
        self.tunnel_address = None
        self.status_message = ""
        
        # Force kill any lingering playit processes
        self._force_kill_playit()
    
    def _force_kill_playit(self):
        """Force kill any playit processes by name"""
        try:
            system = platform.system()
            if system == "Windows":
                subprocess.run(["taskkill", "/F", "/IM", "playit.exe"], 
                              capture_output=True, timeout=5)
            else:
                # Linux/Mac - kill by name
                subprocess.run(["pkill", "-9", "-f", "playit"], 
                              capture_output=True, timeout=5)
        except:
            pass  # Best effort
    
    def get_recent_output(self, lines=10):
        """Get recent output lines for debugging"""
        with self._lock:
            return self._output_lines[-lines:]


# Global instance
_playit_manager = None

def get_playit_manager():
    """Get or create the global PlayitManager instance"""
    global _playit_manager
    if _playit_manager is None:
        _playit_manager = PlayitManager()
    return _playit_manager


def is_available():
    """Check if playit is available"""
    return get_playit_manager().is_available()
