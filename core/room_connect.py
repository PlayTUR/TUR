
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
        """Join via Room Code with domain fallback"""
        self.error_message = ""
        
        # Clean the code
        code = room_code.strip()
        
        # Check if it's a full URL already
        if "ngrok" in code.lower() or "." in code:
            # Direct URL - try once
            url = self._code_to_url(code)
            return self._try_join_url(url)
        
        # Try multiple domain variants
        for domain in self.NGROK_DOMAINS:
            url = f"wss://{code}.{domain}"
            print(f"Trying: {url}")
            if self._try_join_url(url):
                return True
        
        # All failed
        if not self.error_message:
            self.error_message = "Could not connect to room. Is the host still online?"
        return False
    
    def _try_join_url(self, url):
        """Attempt to join a single URL"""
        future = asyncio.run_coroutine_threadsafe(self._async_join(url), self.loop)
        try:
            success = future.result(timeout=8)
            if success:
                self.is_host = False
                self.connected = True
                return True
        except asyncio.TimeoutError:
            self.error_message = "Connection timed out"
        except Exception as e:
            error_str = str(e)
            # Provide user-friendly error messages
            if "404" in error_str or "not found" in error_str.lower():
                self.error_message = "Room not found - host may have closed it"
            elif "refused" in error_str.lower():
                self.error_message = "Connection refused - host not available"
            elif "timeout" in error_str.lower():
                self.error_message = "Connection timed out"
            else:
                self.error_message = f"Join Error: {error_str[:50]}"
        return False

    async def _async_join(self, url):
        try:
            # Add connection timeout
            self.active_ws = await asyncio.wait_for(
                websockets.connect(url),
                timeout=6.0
            )
            # Start listener task
            self.loop.create_task(self._client_listen())
            return True
        except asyncio.TimeoutError:
            self.error_message = "Connection timed out"
            return False
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

    # Known ngrok domains (try in order)
    NGROK_DOMAINS = [
        "ngrok-free.app",
        "ngrok.io", 
        "ngrok.app",
    ]
    
    # --- Utility ---
    def _url_to_code(self, url):
        """Extract subdomain from ngrok URL as room code"""
        try:
            clean = url.replace("https://", "").replace("http://", "")
            # Remove trailing slashes
            clean = clean.rstrip('/')
            parts = clean.split('.')
            if len(parts) >= 2:
                # Store the actual domain used for this session
                self._ngrok_domain = '.'.join(parts[1:])
                return parts[0]  # The subdomain is the code
            return clean
        except:
            return url

    def _code_to_url(self, code):
        """Reconstruct WebSocket URL from room code"""
        # If user pasted full URL, clean and use it
        if "ngrok" in code.lower():
            url = code
            if not url.startswith("http") and not url.startswith("ws"):
                url = f"https://{code}"
            # Convert to websocket
            return url.replace("https://", "wss://").replace("http://", "ws://")
        
        # If we have a stored domain from hosting, prefer that
        if hasattr(self, '_ngrok_domain') and self._ngrok_domain:
            return f"wss://{code}.{self._ngrok_domain}"
        
        # Default to trying the first known domain
        return f"wss://{code}.{self.NGROK_DOMAINS[0]}"
    
    def _try_connect_with_fallback(self, code):
        """Try connecting with multiple domain fallbacks"""
        # If it's already a full URL, just try it
        if "ngrok" in code.lower() or "." in code:
            return self._code_to_url(code), None
        
        # Try each domain variant
        for domain in self.NGROK_DOMAINS:
            url = f"wss://{code}.{domain}"
            yield url
