import time

try:
    from pypresence import Presence
    PYPRESENCE_AVAILABLE = True
except ImportError:
    PYPRESENCE_AVAILABLE = False

# TUR Discord Application Client ID
# This is the registered Discord application that shows "Playing TUR" for all players
DEFAULT_CLIENT_ID = "1453128602110529678"


class DiscordRPCManager:
    def __init__(self, game):
        self.game = game
        self.rpc = None
        self.connected = False
        self.start_time = int(time.time())
        self.last_update = 0
        
        # Use built-in Client ID
        client_id = DEFAULT_CLIENT_ID
        
        if PYPRESENCE_AVAILABLE:
            import threading
            threading.Thread(target=self._connect, args=(client_id,), daemon=True).start()
        else:
            print("pypresence not installed. Discord RPC disabled.")

    def _connect(self, client_id):
        try:
            self.rpc = Presence(client_id)
            self.rpc.connect()
            self.connected = True
            print("Discord RPC Connected!")
        except Exception as e:
            print(f"Discord RPC Failed to Connect: {e}")
            self.connected = False

    def update(self, details="In Menu", state=None, large_image="logo", large_text="TUR: The Rhythm"):
        if not self.connected:
            return
            
        # Rate limit updates (Discord requires 15 second minimum between updates)
        if time.time() - self.last_update < 15:
            return

        try:
            self.rpc.update(
                details=details,
                state=state,
                large_image=large_image,
                large_text=large_text,
                start=self.start_time
            )
            self.last_update = time.time()
        except Exception as e:
            print(f"RPC Update Failed: {e}")
            self.connected = False
            
    def close(self):
        if self.connected and self.rpc:
            try:
                self.rpc.close()
            except:
                pass
