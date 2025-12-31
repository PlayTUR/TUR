"""
Tailscale Manager for TUR Online Multiplayer
Handles Tailscale detection, connection, and IP retrieval.
"""

import subprocess
import platform
import threading
import time
import os
import webbrowser


class TailscaleManager:
    def __init__(self):
        self.tailscale_ip = None
        self.is_connected = False
        self.is_checking = False
        self.status_message = ""
        self.error_message = ""
        self.peers = []  # Other devices on the tailnet
        
    def _run_command(self, args, timeout=10):
        """Run a tailscale command and return output"""
        try:
            # On Windows, tailscale CLI might be in different locations
            if platform.system() == "Windows":
                # Try common paths
                tailscale_paths = [
                    "tailscale",
                    r"C:\Program Files\Tailscale\tailscale.exe",
                    r"C:\Program Files (x86)\Tailscale\tailscale.exe",
                ]
                for path in tailscale_paths:
                    try:
                        result = subprocess.run(
                            [path] + args,
                            capture_output=True,
                            text=True,
                            timeout=timeout,
                            creationflags=subprocess.CREATE_NO_WINDOW
                        )
                        return result
                    except FileNotFoundError:
                        continue
                return None
            else:
                # Linux/Mac
                result = subprocess.run(
                    ["tailscale"] + args,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                return result
        except FileNotFoundError:
            return None
        except subprocess.TimeoutExpired:
            return None
        except Exception as e:
            print(f"Tailscale command error: {e}")
            return None
    
    def is_installed(self):
        """Check if Tailscale is installed"""
        result = self._run_command(["version"], timeout=5)
        return result is not None and result.returncode == 0
    
    def get_status(self):
        """Get Tailscale connection status"""
        result = self._run_command(["status", "--json"], timeout=5)
        if result and result.returncode == 0:
            try:
                import json
                return json.loads(result.stdout)
            except:
                pass
        return None
    
    def get_ip(self):
        """Get Tailscale IPv4 address"""
        result = self._run_command(["ip", "-4"], timeout=5)
        if result and result.returncode == 0:
            ip = result.stdout.strip().split('\n')[0]
            if ip and ip.startswith("100."):
                self.tailscale_ip = ip
                return ip
        return None
    
    def check_connection(self, callback=None):
        """Check if connected to Tailscale network"""
        self.is_checking = True
        self.status_message = "Checking Tailscale..."
        self.error_message = ""
        
        def check_thread():
            try:
                # Check if installed
                if not self.is_installed():
                    self.error_message = "Tailscale not installed"
                    self.is_connected = False
                    self.is_checking = False
                    if callback:
                        callback(False, "not_installed")
                    return
                
                # Get IP
                ip = self.get_ip()
                if ip:
                    self.tailscale_ip = ip
                    self.is_connected = True
                    self.status_message = f"Connected: {ip}"
                    
                    # Try to get peers
                    self._update_peers()
                    
                    if callback:
                        callback(True, ip)
                else:
                    self.is_connected = False
                    self.error_message = "Not connected to Tailscale"
                    if callback:
                        callback(False, "not_connected")
                        
            except Exception as e:
                self.error_message = str(e)
                self.is_connected = False
                if callback:
                    callback(False, str(e))
            finally:
                self.is_checking = False
        
        threading.Thread(target=check_thread, daemon=True).start()
    
    def _update_peers(self):
        """Get list of peers on the tailnet"""
        try:
            status = self.get_status()
            if status is None:
                self.peers = []
                return
            
            peer_dict = status.get("Peer")
            if peer_dict is None:
                self.peers = []
                return
                
            self.peers = []
            for peer_id, peer_info in peer_dict.items():
                if peer_info and peer_info.get("Online"):
                    ips = peer_info.get("TailscaleIPs") or [""]
                    self.peers.append({
                        "name": peer_info.get("HostName", "Unknown"),
                        "ip": ips[0] if ips else "",
                        "os": peer_info.get("OS", ""),
                        "online": peer_info.get("Online", False)
                    })
        except Exception as e:
            print(f"Error updating peers: {e}")
            self.peers = []
    
    def get_peers(self):
        """Get list of online peers"""
        try:
            self._update_peers()
        except:
            pass
        return self.peers
    
    def open_login(self):
        """Open Tailscale login page"""
        if platform.system() == "Windows":
            # Try to run tailscale up which will prompt for login
            result = self._run_command(["up"], timeout=5)
            if result and "https://" in result.stdout:
                # Extract URL and open it
                for line in result.stdout.split('\n'):
                    if "https://" in line:
                        url = line.strip()
                        webbrowser.open(url)
                        return True
        else:
            # On Linux, tailscale up might need sudo
            # Just open the admin page
            webbrowser.open("https://login.tailscale.com/admin/machines")
        return False
    
    def open_download_page(self):
        """Open Tailscale download page"""
        webbrowser.open("https://tailscale.com/download")
    
    def get_invite_instructions(self):
        """Get instructions for inviting a friend"""
        return [
            "1. Both players install Tailscale from tailscale.com",
            "2. Create a free account (or use Google/GitHub login)",
            "3. One player shares their Tailnet invite link:",
            "   - Go to admin.tailscale.com → Settings → Sharing",
            "   - Or use 'Share' in Tailscale app",
            "4. Once both are on same Tailnet, use LAN mode!",
            f"5. Your Tailscale IP: {self.tailscale_ip or 'Not connected'}",
        ]


# Global instance
_manager = None

def get_tailscale_manager():
    """Get or create global TailscaleManager instance"""
    global _manager
    if _manager is None:
        _manager = TailscaleManager()
    return _manager


def check_tailscale_available():
    """Quick check if Tailscale is available and connected"""
    manager = get_tailscale_manager()
    if manager.is_installed():
        ip = manager.get_ip()
        if ip:
            return True, ip
        return False, "Not connected"
    return False, "Not installed"
