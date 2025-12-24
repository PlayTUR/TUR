
import asyncio
import threading
import json
import queue
import time
import os
import hashlib
import binascii
import ngrok
import websockets

class RoomConnect:
    def __init__(self):
        self.ngrok_token = None
        self.public_url = None
        self.region = "US" # Default
        self.error_message = ""
        self.connected = False
        self.is_host = False
        
        # Port for local WS server
        self.port = 1338 
        
        # Async/Thread management
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.msg_queue = queue.Queue()
        self.active_ws = None
        self.tunnel = None
        self.server = None
        
        # Token file
        self.token_file = "ngrok.token"
        self._load_token()
        
        # Start background loop
        self.thread.start()

    def _run_loop(self):
        """Background asyncio loop"""
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def _load_token(self):
        if os.path.exists(self.token_file):
            try:
                with open(self.token_file, 'r') as f:
                    self.ngrok_token = f.read().strip()
            except:
                pass

    def save_token(self, token):
        self.ngrok_token = token
        try:
            with open(self.token_file, 'w') as f:
                f.write(token)
        except:
            pass

    def set_token(self, token):
        self.save_token(token)

    def host_game(self, room_name="TUR Room"):
        """Start hosting via Ngrok (HTTP/WS)"""
        self.error_message = ""
        if not self.ngrok_token:
            self.error_message = "No Authtoken"
            return None
            
        future = asyncio.run_coroutine_threadsafe(self._async_host(), self.loop)
        try:
            room_code = future.result(timeout=15)
            if room_code:
                self.is_host = True
                self.connected = True
                return room_code
        except Exception as e:
            self.error_message = f"Host Timeout/Error: {e}"
        return None

    async def _async_host(self):
        try:
            # Cleanup previous
            if self.tunnel:
                try: await self.tunnel.close()
                except: pass
            if self.server:
                self.server.close()
                await self.server.wait_closed()
                
            # 1. Start Ngrok Tunnel (HTTP)
            # ngrok-python sync API is fine or we can use generic setup
            self.tunnel = await ngrok.forward(self.port, authtoken=self.ngrok_token, proto="http")
            self.public_url = self.tunnel.url()
            
            # Detect region from URL if possible (e.g. us.ngrok...)
            # Modern ngrok urls are random subdomains usually.
            # We'll generate code hash from full URL.
            
            # 2. Start WS Server
            self.server = await websockets.serve(self._handle_client, "0.0.0.0", self.port)
            
            # 3. Generate Code
            return self._url_to_code(self.public_url)
            
        except Exception as e:
            self.error_message = str(e)
            return None

    async def _handle_client(self, websocket):
        """Handle incoming connection (Host side)"""
        if self.active_ws:
            # Only 1 on 1 for now? Or allow overwrite?
            try:
                await self.active_ws.close()
            except:
                pass
        
        self.active_ws = websocket
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    self.msg_queue.put(data)
                except:
                    pass
        except:
            pass
        finally:
            if self.active_ws == websocket:
                self.active_ws = None

    def join_game(self, room_code):
        """Join via Room Code"""
        self.error_message = ""
        url = self._code_to_url(room_code)
        if not url:
            self.error_message = "Invalid Code"
            return False
            
        # Convert https -> wss
        if url.startswith("https://"):
            url = url.replace("https://", "wss://")
        elif url.startswith("http://"):
            url = url.replace("http://", "ws://")
            
        future = asyncio.run_coroutine_threadsafe(self._async_join(url), self.loop)
        try:
            success = future.result(timeout=10)
            if success:
                self.is_host = False
                self.connected = True
                return True
        except Exception as e:
            self.error_message = f"Join Error: {e}"
            
        return False

    async def _async_join(self, url):
        try:
            self.active_ws = await websockets.connect(url)
            # Start listener task
            self.loop.create_task(self._client_listen())
            return True
        except Exception as e:
            self.error_message = str(e)
            return False

    async def _client_listen(self):
        """Client side listener loop"""
        try:
            async for message in self.active_ws:
                try:
                    data = json.loads(message)
                    self.msg_queue.put(data)
                except:
                    pass
        except:
            pass

    def send_game_data(self, data):
        """Send JSON data to peer"""
        if self.active_ws and self.active_ws.open:
            msg = json.dumps(data)
            asyncio.run_coroutine_threadsafe(self._safe_send(msg), self.loop)
            return True
        return False

    async def _safe_send(self, msg):
        try:
            if self.active_ws:
                await self.active_ws.send(msg)
        except:
            pass

    def get_messages(self):
        """Retrieve all queued messages"""
        msgs = []
        while not self.msg_queue.empty():
            try:
                msgs.append(self.msg_queue.get_nowait())
            except:
                break
        return msgs

    def close(self):
        self.connected = False
        asyncio.run_coroutine_threadsafe(self._async_close(), self.loop)

    async def _async_close(self):
        if self.active_ws:
            await self.active_ws.close()
        if self.server:
            self.server.close()
        if self.tunnel:
            try:
                # ngrok listener object
                await self.tunnel.close()
            except:
                pass

    # --- Utility ---
    def _url_to_code(self, url):
        """Generate room code from URL: [Region]-[Hash]"""
        # We can just hash the whole URL
        # Or simplistic region detect
        region = "US"
        if ".eu." in url: region = "EU"
        elif ".ap." in url: region = "AP"
        elif ".jp." in url: region = "JP"
        elif ".sa." in url: region = "SA"
        
        h = hashlib.md5(url.encode()).hexdigest()[:6].upper()
        return f"{region}-{h}"

    def _code_to_url(self, code):
        """
        Problem: We can't reverse the hash.
        Previously we relied on the tunnel giving us a predictable URL or storing the URL.
        WEBSOCKET approach means URL is dynamic from Ngrok.
        We CANNOT accept just a hash code unless we have a directory service.
        OR we must ask user to share the FULL URL?
        The previous code relied on the user typing "EU-XXXXXX".
        Wait. Previous implementation used standard TCP port tunnels which might have been static?
        No, previous implementation assumed we could reverse it or send the IP?
        Actually, previous implementation:
            `NetworkManager.generate_room_code` -> `crc32(ip)`
        Ngrok URLs are random strings: `https://gopher-hero-random.ngrok-free.app`
        Usage without a DB means users must share the **URL**.
        The "Code" concept is hard with random domains unless serialized.
        URL is long.
        
        Solution for Free Tier Usability:
        We must show the FULL URL or a compressed version.
        Or use a tinyurl service?
        Or keep the code UI but use a separate external KV store? (Too complex).
        
        Simplest: User shares the **Room Code** which IS the URL, but maybe we just ask them to share the URL?
        Or we stick to "Code" but the "Code" is just the subdomain part?
        e.g. `gopher-hero-random`.
        Url: `https://<code >.ngrok-free.app`
        YES. Ngrok free domains are `https://<subdomain>.ngrok-free.app`.
        So the "Code" is the subdomain.
        """
        # Parse Code
        try:
            # Code might be "US-XYZ" (Old) or just "subdomain"
            # If we assume ngrok-free.app
            
            # If code contains '.', treat as full URL or domain
            if '.' in code:
                 # Clean it
                 if not code.startswith("http"):
                     return f"https://{code}"
                 return code
            
            # If code looks like subdomain
            # Check if it has region prefix from our _url_to_code?
            # Our _url_to_code generated a Hash. We can't reverse hash.
            # We MUST change _url_to_code to return the Subdomain.
            pass
        except:
            pass
        return None 
    
    def _url_to_code(self, url):
        # Extract subdomain
        # https://xxxxxx.ngrok-free.app
        try:
            clean = url.replace("https://", "").replace("http://", "")
            parts = clean.split('.')
            if len(parts) >= 3:
                return parts[0] # The subdomain
            return clean # Fallback
        except:
            return url

    def _code_to_url(self, code):
        # Reconstruct URL
        # Assumption: Uses ngrok-free.app
        # This is brittle if ngrok changes domains, but standard for free tier.
        if "ngrok" in code: # User pasted full url?
             return code if code.startswith("http") else f"wss://{code}"
        
        return f"wss://{code}.ngrok-free.app"
