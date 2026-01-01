"""
Master Server Client for TUR
Communicates with the central matchmaking server for:
- Account registration/login
- Server browser (list/register/heartbeat)
"""

import urllib.request
import urllib.parse
import json
import threading
import time

# Default server URL - your VPS
MASTER_SERVER_URL = "http://154.53.35.148:8080"

class MasterClient:
    def __init__(self, server_url=None):
        self.server_url = server_url or MASTER_SERVER_URL
        self.auth_token = None
        self.username = None
        self.username = None
        self.is_admin = False
        self.logged_in = False
        
        # Server hosting state
        self.registered_server_id = None
        self.heartbeat_thread = None
        self.heartbeat_running = False
        
        # Connection Monitoring
        self.server_online = False
        self.monitor_thread = None
        self.monitor_running = False
        
        # Cached server list
        self.servers = []
        self.last_refresh = 0
        
        # Status
        self.status = ""
        self.error = ""
    
    def _request(self, endpoint, method="GET", data=None):
        """Make HTTP request to master server"""
        url = f"{self.server_url}{endpoint}"
        
        try:
            headers = {
                "Content-Type": "application/json",
                "X-TUR-Client": "TUR-G4M3-CL13NT-v1"  # Client validation
            }
            if self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"
            
            if data:
                req = urllib.request.Request(
                    url,
                    data=json.dumps(data).encode('utf-8'),
                    headers=headers,
                    method=method
                )
            else:
                req = urllib.request.Request(url, headers=headers, method=method)
            
            with urllib.request.urlopen(req, timeout=10) as response:
                return json.loads(response.read().decode())
                
        except urllib.error.HTTPError as e:
            error_body = e.read().decode() if e.fp else str(e)
            try:
                error_data = json.loads(error_body)
                self.error = error_data.get("detail", str(e))
            except:
                self.error = str(e)
            return None
        except urllib.error.URLError as e:
            self.error = f"Cannot reach server: {e.reason}"
            return None
        except Exception as e:
            self.error = str(e)
            return None
            return None
    
    def get_server_stats(self):
        """Fetch global server performance metrics"""
        res = self._request("/health")
        if res:
            return {
                "players": res.get("players", "0"),
                "total": res.get("total_operators", "0"),
                "version": res.get("version", "v1.0.0")
            }
        return None

    def get_status(self):
        """Check if server is online"""
        try:
            res = self._request("/health")
            return res and res.get("status") == "ok"
        except:
            return False
    
    # === Authentication ===
    
    def login(self, username, password):
        """Login to existing account"""
        self.status = "Logging in..."
        result = self._request("/login", "POST", {
            "username": username,
            "password": password
        })
        
        if result and result.get("success"):
            self.auth_token = result.get("token")
            self.username = result.get("username")
            # We need to fetch full stats to get admin status since login response is minimal
            # But wait, login doesn't return is_admin. Let's fetch self immediately.
            self.logged_in = True
            
            # Fetch full profile to populate is_admin
            try:
                profile = self.get_my_stats()
                if profile:
                    self.is_admin = profile.get("is_admin", False)
                    # Propagate to game settings for UI
                    if hasattr(self, 'game') and self.game:
                        self.game.settings.set("is_admin", self.is_admin)
            except:
                self.is_admin = False
                
            self.status = f"Logged in as {self.username}"
            return True
        
        if result:
            self.error = result.get("message", "Login failed")
        if result:
            self.error = result.get("message", "Login failed")
        return False
    
    def rename_user(self, new_name):
        """Rename current user"""
        if not self.auth_token: return False
        
        res = self._request("/api/v2/users/rename", "POST", {"username": new_name})
        if res and res.get("success"):
            self.username = res.get("username")
            return True
        elif res:
            self.error = res.get("detail", "Rename failed")
        
        return False

    def logout(self):
        """Clear local session"""
        self.auth_token = None
        self.username = None
        self.logged_in = False
        self.status = ""
    
    # === Server Browser ===
    
    def get_servers(self, force_refresh=False):
        """Get list of active servers"""
        now = time.time()
        
        # Cache for 5 seconds
        if not force_refresh and (now - self.last_refresh) < 5:
            return self.servers
        
        result = self._request("/servers")
        
        if result:
            self.servers = result.get("servers", [])
            self.last_refresh = now
        
        return self.servers
    
    def get_servers_async(self, callback=None):
        """Fetch servers in background"""
        def fetch():
            servers = self.get_servers(force_refresh=True)
            if callback:
                callback(servers)
        
        threading.Thread(target=fetch, daemon=True).start()
    
    # === Server Hosting ===
    
    def register_server(self, name, port, host_name=None, password_protected=False, max_players=2, public_ip=None):
        """Register this game as a joinable server"""
        self.status = "Registering server..."
        
        # Try to get public IP if not provided
        if not public_ip:
            public_ip = self._get_public_ip()
        
        data = {
            "name": name,
            "port": port,
            "host_name": host_name or self.username or "Anonymous",
            "password_protected": password_protected,
            "max_players": max_players
        }
        
        # Add IP as query param (server should also detect from request)
        result = self._request(f"/servers/register?client_ip={public_ip}", "POST", data)
        
        if result and result.get("success"):
            self.registered_server_id = result.get("server_id")
            self.status = "Server registered!"
            self._start_heartbeat()
            return True
        
        return False
    
    def _get_public_ip(self):
        """Get public IP address"""
        try:
            with urllib.request.urlopen("https://api.ipify.org", timeout=5) as r:
                return r.read().decode().strip()
        except:
            try:
                with urllib.request.urlopen("https://checkip.amazonaws.com", timeout=5) as r:
                    return r.read().decode().strip()
            except:
                return "0.0.0.0"
    
    def _start_heartbeat(self):
        """Start heartbeat thread to keep server alive"""
        if self.heartbeat_thread and self.heartbeat_running:
            return
        
        self.heartbeat_running = True
        
        def heartbeat_loop():
            while self.heartbeat_running and self.registered_server_id:
                try:
                    # Get current player count from network manager if available
                    player_count = 1  # Default, should get from network state
                    
                    self._request(
                        f"/servers/{self.registered_server_id}/heartbeat?player_count={player_count}",
                        "POST"
                    )
                except:
                    pass
                time.sleep(30)  # Every 30 seconds
        
        self.heartbeat_thread = threading.Thread(target=heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()
    
    def unregister_server(self):
        """Remove server from list"""
        if self.registered_server_id:
            self._request(f"/servers/{self.registered_server_id}", "DELETE")
            self.registered_server_id = None
        
        self.heartbeat_running = False
        self.status = ""
    
    def is_server_running(self):
        """Check if the master server is reachable"""
        try:
            result = self._request("/health")
            return result is not None
        except:
            return False

    # === Leaderboards & Stats ===
    
    def submit_score(self, score, max_score=0, song_hash=None, song_name="Unknown", difficulty="MEDIUM", stats=None):
        if not self.auth_token: return False
        
        data = {
            "score": score,
            "max_score": max_score,
            "song_hash": song_hash,
            "song_name": song_name,
            "difficulty": difficulty
        }
        
        if stats:
            data.update(stats) # perfects, goods, etc
            
        result = self._request("/api/v2/stats/submit", "POST", data)
        return result and result.get("success")
        
    def get_leaderboard(self):
        result = self._request("/api/v2/leaderboard")
        if result:
             return result.get("leaderboard", [])
        return []
        
    def get_my_stats(self):
         if not self.auth_token: return None
         return self._request("/api/v2/users/me")

    # === Connection Monitoring ===
    
    def start_monitoring(self):
        """Start background check for server availability"""
        if self.monitor_running: return
        self.monitor_running = True
        
        def monitor():
            while self.monitor_running:
                online = self.get_status()
                if online != self.server_online:
                    self.server_online = online
                    # print(f"Server status changed: {'ONLINE' if online else 'OFFLINE'}")
                time.sleep(5)
                
        self.monitor_thread = threading.Thread(target=monitor, daemon=True)
        self.monitor_thread.start()
        
    def stop_monitoring(self):
        self.monitor_running = False


# Singleton instance
_master_client = None

def get_master_client(server_url=None):
    """Get or create singleton master client"""
    global _master_client
    if _master_client is None:
        _master_client = MasterClient(server_url)
    return _master_client
