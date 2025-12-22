import time
try:
    from pypresence import Presence
    PYPRESENCE_AVAILABLE = True
except ImportError:
    PYPRESENCE_AVAILABLE = False

# Placeholder Client ID - User should replace this with their own app ID from Discord Developer Portal
CLIENT_ID = "123456789012345678" 

class DiscordRPCManager:
    def __init__(self, game):
        self.game = game
        self.rpc = None
        self.connected = False
        self.start_time = int(time.time())
        self.last_update = 0
        
        # Get ID from settings or use placeholder
        client_id = self.game.settings.get("discord_client_id") or "123456789012345678"
        
        if PYPRESENCE_AVAILABLE:
            try:
                self.rpc = Presence(client_id)
                self.rpc.connect()
                self.connected = True
                print("Discord RPC Connected!")
            except Exception as e:
                print(f"Discord RPC Failed to Connect: {e}")
                self.connected = False
        else:
            print("pypresence not installed. Discord RPC disabled.")

    def update(self, details="In Menu", state=None, large_image="logo", large_text="TUR: The Rhythm"):
        if not self.connected:
            return
            
        # Rate limit updates (15 sec rule is strict in pypresence/discord docs, 
        # but pypresence handles some of it. We'll limit to once per 15s to be safe if spamming)
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
            self.connected = False # Disable on error to prevent spamming logs
            
    def close(self):
        if self.connected and self.rpc:
            try:
                self.rpc.close()
            except:
                pass
