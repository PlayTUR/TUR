"""
Network Manager for TUR Multiplayer
Room codes, UDP hole punching, song transfer.
Features:
- Room code system (encoded IP:port)
- UDP hole punching for NAT traversal
- Song file transfer
- Synchronized game start
"""

import socket
import threading
import json
import time
import hashlib
import base64
import os
import struct
from core.stun_client import discover_external_address, get_local_ip


class NetworkManager:
    DISCOVERY_PORT = 9998
    
    def __init__(self, port=9999):
        self.port = port
        self.udp_socket = None
        self.tcp_socket = None
        self.connection = None
        self.broadcast_socket = None
        
        # State
        self.is_host = False
        self.connected = False
        self.connecting = False
        self.broadcasting = False
        self.running = True
        self.lock = threading.Lock()
        
        # Address info
        self.external_ip = None
        self.external_port = None
        self.local_ip = get_local_ip()
        self.room_code = ""
        
        # Peer info
        self.peer_address = None
        self.opponent_name = "Waiting..."
        self.opponent_score = 0
        self.opponent_ready = False
        
        # Room settings
        self.room_name = "TUR Room"
        self.room_password = ""
        
        # Game sync
        self.start_timestamp = 0
        self.seed = 0
        self.selected_song = None
        self.selected_difficulty = None
        
        # File transfer
        self.transfer_progress = 0
        self.transfer_total = 0
        self.pending_file_data = b''
        
        # Status messages
        self.status_message = ""
        self.error_message = ""

    # === Room Code System ===
    
    def generate_room_code(self):
        """Generate a shareable room code from external IP:port"""
        if not self.external_ip or not self.external_port:
            return None
        
        try:
            ip_parts = [int(x) for x in self.external_ip.split('.')]
            data = bytes(ip_parts) + struct.pack('>H', self.external_port)
            encoded = base64.b32encode(data).decode('ascii').rstrip('=')
            
            if len(encoded) >= 8:
                self.room_code = f"{encoded[:4]}-{encoded[4:8]}"
            else:
                self.room_code = encoded
            
            return self.room_code
        except Exception as e:
            print(f"Room code generation error: {e}")
            return None
    
    def decode_room_code(self, code):
        """Decode room code back to IP:port"""
        try:
            clean = code.replace('-', '').replace(' ', '').upper()
            padding = (8 - len(clean) % 8) % 8
            clean += '=' * padding
            data = base64.b32decode(clean)
            ip = '.'.join(str(b) for b in data[:4])
            port = struct.unpack('>H', data[4:6])[0]
            return ip, port
        except Exception as e:
            print(f"Room code decode error: {e}")
            return None, None

    # === Hosting ===
    
    def host_game(self, room_name="TUR Room", password=""):
        """Start hosting with UDP hole punching ready"""
        self.is_host = True
        self.room_name = room_name
        self.room_password = password
        self.connected = False
        self.connecting = True
        self.error_message = ""
        
        threading.Thread(target=self._host_thread, daemon=True).start()
    
    def _host_thread(self):
        try:
            # Step 1: Discover external address via STUN
            self.status_message = "Discovering external address..."
            ip, port, sock = discover_external_address()
            
            if ip:
                self.external_ip = ip
                self.external_port = port
                self.udp_socket = sock
                self.generate_room_code()
                self.status_message = f"Room Code: {self.room_code}"
            else:
                self.status_message = "STUN failed - LAN only mode"
                self.room_code = "LAN-ONLY"
            
            # Step 2: Set up TCP listener
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.tcp_socket.settimeout(1.0)
            self.tcp_socket.bind(('0.0.0.0', self.port))
            self.tcp_socket.listen(2)
            self.connecting = False
            
            # Start LAN broadcast for P2P discovery
            self.start_broadcasting()
            
            # Step 3: Listen for connections
            while self.running and self.is_host:
                try:
                    conn, addr = self.tcp_socket.accept()
                    print(f"Connection from {addr}")
                    
                    if not self.connection:
                        self.connection = conn
                        self.peer_address = addr
                        self.connected = True
                        self.status_message = "Player connected!"
                        threading.Thread(target=self._tcp_listen, args=(conn,), daemon=True).start()
                        
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        print(f"Accept error: {e}")
                    break
                    
        except Exception as e:
            self.error_message = f"Host error: {e}"
        finally:
            self.connecting = False

    # === Joining ===
    
    def join_with_code(self, code, password=""):
        """Join game using room code"""
        ip, port = self.decode_room_code(code)
        if ip:
            self.port = port
            self.join_game(ip, password)
        else:
            self.error_message = "Invalid room code"
    
    def join_by_code(self, code, password=""):
        """Alias for join_with_code"""
        self.join_with_code(code, password)
    
    def join_game(self, ip, password=""):
        """Join game by IP"""
        self.is_host = False
        self.room_password = password
        self.connected = False
        self.connecting = True
        self.error_message = ""
        
        threading.Thread(target=self._join_thread, args=(ip,), daemon=True).start()
    
    def _join_thread(self, ip):
        try:
            self.status_message = f"Connecting to {ip}:{self.port}..."
            
            # Try UDP hole punch first (send a few packets)
            if self.udp_socket:
                for _ in range(3):
                    try:
                        self.udp_socket.sendto(b'PUNCH', (ip, self.port))
                    except:
                        pass
                    time.sleep(0.1)
            
            # TCP connection
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_socket.settimeout(10.0)
            self.tcp_socket.connect((ip, self.port))
            
            self.connection = self.tcp_socket
            self.peer_address = (ip, self.port)
            self.connected = True
            self.connecting = False
            self.status_message = "Connected!"
            
            # Handshake
            self.send({
                'type': 'hello',
                'name': 'PLAYER 2',
                'password': self.room_password
            })
            
            self._tcp_listen(self.tcp_socket)
            
        except socket.timeout:
            self.error_message = "Connection timed out"
            self.connecting = False
        except ConnectionRefusedError:
            self.error_message = "Connection refused"
            self.connecting = False
        except Exception as e:
            self.error_message = f"Failed: {e}"
            self.connecting = False
            self.connected = False

    # === Communication ===
    
    def _tcp_listen(self, conn):
        buffer = ""
        while self.running and self.connected:
            try:
                conn.settimeout(1.0)
                data = conn.recv(65536)
                if not data:
                    break
                
                buffer += data.decode('utf-8', errors='ignore')
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if line:
                        try:
                            msg = json.loads(line)
                            self._handle_message(msg, conn)
                        except json.JSONDecodeError:
                            pass
            except socket.timeout:
                continue
            except Exception as e:
                print(f"Listen error: {e}")
                break
        
        self.connected = False
        self.status_message = "Disconnected"
    
    def _handle_message(self, msg, conn):
        with self.lock:
            msg_type = msg.get('type', '')
            
            if msg_type == 'hello':
                if self.is_host:
                    # Verify password
                    if self.room_password and msg.get('password') != self.room_password:
                        self.send({'type': 'error', 'msg': 'Wrong password'}, conn)
                        conn.close()
                        self.connection = None
                        self.connected = False
                        return
                    
                    self.opponent_name = msg.get('name', 'Player 2')
                    self.send({'type': 'hello', 'name': 'HOST'})
                else:
                    self.opponent_name = msg.get('name', 'Host')
            
            elif msg_type == 'score':
                self.opponent_score = msg.get('score', 0)
            
            elif msg_type == 'ready':
                self.opponent_ready = msg.get('ready', False)
            
            elif msg_type == 'song_select':
                self.selected_song = msg.get('song')
                self.selected_difficulty = msg.get('difficulty')
                song_hash = msg.get('hash')
                
                # Check if we have this song
                song_path = os.path.join('songs', self.selected_song)
                if os.path.exists(song_path):
                    local_hash = self._file_hash(song_path)
                    if local_hash == song_hash:
                        self.send({'type': 'song_ready', 'have_it': True})
                    else:
                        self.send({'type': 'song_ready', 'have_it': False})
                else:
                    self.send({'type': 'song_ready', 'have_it': False})
            
            elif msg_type == 'song_ready':
                if not msg.get('have_it'):
                    self._send_song_file()
            
            elif msg_type == 'file_start':
                self.transfer_total = msg.get('size', 0)
                self.transfer_progress = 0
                self.pending_file_data = b''
                self.status_message = "Receiving song... 0%"
            
            elif msg_type == 'file_chunk':
                chunk = base64.b64decode(msg.get('data', ''))
                self.pending_file_data += chunk
                self.transfer_progress = len(self.pending_file_data)
                pct = int(100 * self.transfer_progress / max(1, self.transfer_total))
                self.status_message = f"Receiving song... {pct}%"
            
            elif msg_type == 'file_end':
                filename = msg.get('filename', 'received.wav')
                filepath = os.path.join('songs', filename)
                os.makedirs('songs', exist_ok=True)
                with open(filepath, 'wb') as f:
                    f.write(self.pending_file_data)
                self.pending_file_data = b''
                self.status_message = "Song received!"
                self.send({'type': 'song_ready', 'have_it': True})
            
            elif msg_type == 'start':
                self.start_timestamp = msg.get('start_time', 0)
                self.seed = msg.get('seed', 0)
            
            elif msg_type == 'error':
                self.error_message = msg.get('msg', 'Error')
    
    def send(self, data, conn=None):
        target = conn or self.connection
        if target:
            try:
                msg = json.dumps(data) + '\n'
                target.send(msg.encode('utf-8'))
                return True
            except:
                return False
        return False

    # === Song Transfer ===
    
    def _file_hash(self, filepath):
        """Get MD5 hash of file"""
        h = hashlib.md5()
        with open(filepath, 'rb') as f:
            while chunk := f.read(8192):
                h.update(chunk)
        return h.hexdigest()
    
    def _send_song_file(self):
        """Send selected song to peer"""
        if not self.selected_song:
            return
        
        filepath = os.path.join('songs', self.selected_song)
        if not os.path.exists(filepath):
            return
        
        threading.Thread(target=self._send_file_thread, args=(filepath,), daemon=True).start()
    
    def _send_file_thread(self, filepath):
        try:
            filename = os.path.basename(filepath)
            filesize = os.path.getsize(filepath)
            
            self.send({'type': 'file_start', 'filename': filename, 'size': filesize})
            
            chunk_size = 32768
            with open(filepath, 'rb') as f:
                while chunk := f.read(chunk_size):
                    encoded = base64.b64encode(chunk).decode('ascii')
                    self.send({'type': 'file_chunk', 'data': encoded})
                    time.sleep(0.01)
            
            self.send({'type': 'file_end', 'filename': filename})
            self.status_message = "Song sent!"
            
        except Exception as e:
            print(f"File transfer error: {e}")

    # === Game Control ===
    
    def select_song(self, filename, difficulty):
        """Host selects a song"""
        self.selected_song = filename
        self.selected_difficulty = difficulty
        
        filepath = os.path.join('songs', filename)
        file_hash = self._file_hash(filepath) if os.path.exists(filepath) else ""
        
        self.send({
            'type': 'song_select',
            'song': filename,
            'difficulty': difficulty,
            'hash': file_hash
        })
    
    def start_game_request(self, seed=None):
        """Start the game (host only)"""
        if self.is_host:
            start_time = time.time() + 3.0
            self.start_timestamp = start_time
            self.seed = seed or int(time.time())
            self.send({
                'type': 'start',
                'start_time': start_time,
                'seed': self.seed
            })
            return start_time
        return 0
    
    def send_score(self, score):
        """Send current score"""
        self.send({'type': 'score', 'score': score})
    
    def set_ready(self, ready=True):
        """Set ready status"""
        self.send({'type': 'ready', 'ready': ready})

    # === Cleanup ===
    
    def close(self):
        self.running = False
        self.connected = False
        self.connecting = False
        self.is_host = False
        self.broadcasting = False
        
        for sock in [self.connection, self.tcp_socket, self.udp_socket, self.broadcast_socket]:
            if sock:
                try:
                    sock.close()
                except:
                    pass
        
        self.connection = None
        self.tcp_socket = None
        self.udp_socket = None
        self.broadcast_socket = None
        self.room_code = ""
        self.status_message = ""
        self.error_message = ""
        self.opponent_name = "Waiting..."
        self.opponent_score = 0
    
    def reset(self):
        self.close()
        self.running = True

    # === P2P LAN Discovery ===
    
    def start_broadcasting(self):
        """Host broadcasts presence on LAN for P2P discovery"""
        self.broadcasting = True
        self.broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        def broadcast_loop():
            while self.broadcasting and self.is_host:
                try:
                    has_pass = "1" if self.room_password else "0"
                    msg = f"TUR|{self.room_name}|{self.room_code}|{self.local_ip}|{self.port}|{has_pass}"
                    self.broadcast_socket.sendto(msg.encode(), ('<broadcast>', self.DISCOVERY_PORT))
                except:
                    pass
                time.sleep(2)
        
        threading.Thread(target=broadcast_loop, daemon=True).start()
    
    def scan_lan_servers(self, timeout=3.0):
        """Scan LAN for TUR servers broadcasting"""
        servers = []
        
        try:
            scan_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            scan_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            scan_sock.bind(('', self.DISCOVERY_PORT))
            scan_sock.settimeout(0.5)
            
            end_time = time.time() + timeout
            seen = set()
            
            while time.time() < end_time:
                try:
                    data, addr = scan_sock.recvfrom(1024)
                    msg = data.decode('utf-8')
                    
                    if msg.startswith("TUR|"):
                        parts = msg.split("|")
                        if len(parts) >= 6:
                            key = f"{parts[2]}|{addr[0]}"
                            if key not in seen:
                                seen.add(key)
                                servers.append({
                                    "name": parts[1],
                                    "code": parts[2],
                                    "ip": parts[3],
                                    "port": int(parts[4]),
                                    "password": parts[5] == "1",
                                    "host": addr[0],
                                    "players": 1
                                })
                except socket.timeout:
                    continue
                except:
                    break
            
            scan_sock.close()
        except Exception as e:
            print(f"LAN scan error: {e}")
        
        return servers
