"""
Network Manager for TUR Multiplayer
Room codes, UDP hole punching, song transfer.
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
    def __init__(self, port=9999):
        self.port = port
        self.udp_socket = None
        self.tcp_socket = None
        self.connection = None
        self.broadcast_socket = None
        
        self.is_host = False
        self.connected = False
        self.connecting = False
        self.broadcasting = False
        self.running = True
        self.lock = threading.Lock()
        
        self.external_ip = None
        self.external_port = None
        self.local_ip = get_local_ip()
        self.room_code = ""
        
        self.peer_address = None
        self.opponent_name = "Waiting..."
        self.opponent_score = 0
        self.opponent_ready = False
        
        self.room_name = "TUR Room"
        self.room_password = ""
        
        self.start_timestamp = 0
        self.seed = 0
        self.selected_song = None
        self.selected_difficulty = None
        
        self.transfer_progress = 0
        self.transfer_total = 0
        self.pending_file_data = b''
        
        self.status_message = ""
        self.error_message = ""

    def generate_room_code(self):
        if not self.external_ip or not self.external_port:
            return None
        try:
            ip_parts = [int(x) for x in self.external_ip.split('.')]
            data = bytes(ip_parts) + struct.pack('>H', self.external_port)
            encoded = base64.b32encode(data).decode('ascii').rstrip('=')
            self.room_code = f"{encoded[:4]}-{encoded[4:8]}" if len(encoded) >= 8 else encoded
            return self.room_code
        except:
            return None
    
    def decode_room_code(self, code):
        try:
            clean = code.replace('-', '').replace(' ', '').upper()
            clean += '=' * ((8 - len(clean) % 8) % 8)
            data = base64.b32decode(clean)
            ip = '.'.join(str(b) for b in data[:4])
            port = struct.unpack('>H', data[4:6])[0]
            return ip, port
        except:
            return None, None

    def host_game(self, room_name="TUR Room", password=""):
        self.is_host = True
        self.room_name = room_name
        self.room_password = password
        self.connected = False
        self.connecting = True
        self.error_message = ""
        threading.Thread(target=self._host_thread, daemon=True).start()
    
    def _host_thread(self):
        try:
            self.status_message = "Discovering external address..."
            ip, port, sock = discover_external_address()
            if ip:
                self.external_ip = ip
                self.external_port = port
                self.udp_socket = sock
                self.generate_room_code()
                self.status_message = f"Room Code: {self.room_code}"
            else:
                self.status_message = "STUN failed - LAN only"
                self.room_code = "LAN-ONLY"
            
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.tcp_socket.settimeout(1.0)
            self.tcp_socket.bind(('0.0.0.0', self.port))
            self.tcp_socket.listen(2)
            self.connecting = False
            
            # Start LAN broadcast for P2P discovery
            self.start_broadcasting()
            
            while self.running and self.is_host:
                try:
                    conn, addr = self.tcp_socket.accept()
                    if not self.connection:
                        self.connection = conn
                        self.peer_address = addr
                        self.connected = True
                        self.status_message = "Player connected!"
                        threading.Thread(target=self._tcp_listen, args=(conn,), daemon=True).start()
                except socket.timeout:
                    continue
                except:
                    break
        except Exception as e:
            self.error_message = f"Host error: {e}"
        finally:
            self.connecting = False

    def join_with_code(self, code, password=""):
        ip, port = self.decode_room_code(code)
        if ip:
            self.port = port
            self.join_game(ip, password)
        else:
            self.error_message = "Invalid room code"
    
    def join_game(self, ip, password=""):
        self.is_host = False
        self.room_password = password
        self.connected = False
        self.connecting = True
        self.error_message = ""
        threading.Thread(target=self._join_thread, args=(ip,), daemon=True).start()
    
    def _join_thread(self, ip):
        try:
            self.status_message = f"Connecting to {ip}..."
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_socket.settimeout(10.0)
            self.tcp_socket.connect((ip, self.port))
            self.connection = self.tcp_socket
            self.peer_address = (ip, self.port)
            self.connected = True
            self.connecting = False
            self.status_message = "Connected!"
            self.send({'type': 'hello', 'name': 'PLAYER 2', 'password': self.room_password})
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
                            self._handle_message(json.loads(line), conn)
                        except:
                            pass
            except socket.timeout:
                continue
            except:
                break
        self.connected = False
        self.status_message = "Disconnected"
    
    def _handle_message(self, msg, conn):
        with self.lock:
            t = msg.get('type', '')
            if t == 'hello':
                if self.is_host and self.room_password and msg.get('password') != self.room_password:
                    self.send({'type': 'error', 'msg': 'Wrong password'}, conn)
                    conn.close()
                    self.connection = None
                    self.connected = False
                    return
                self.opponent_name = msg.get('name', 'Player 2')
                if self.is_host:
                    self.send({'type': 'hello', 'name': 'HOST'})
            elif t == 'score':
                self.opponent_score = msg.get('score', 0)
            elif t == 'ready':
                self.opponent_ready = msg.get('ready', False)
            elif t == 'start':
                self.start_timestamp = msg.get('start_time', 0)
                self.seed = msg.get('seed', 0)
            elif t == 'error':
                self.error_message = msg.get('msg', 'Error')
    
    def send(self, data, conn=None):
        target = conn or self.connection
        if target:
            try:
                target.send((json.dumps(data) + '\n').encode('utf-8'))
                return True
            except:
                return False
        return False

    def start_game_request(self, seed=None):
        if self.is_host:
            self.start_timestamp = time.time() + 3.0
            self.seed = seed or int(time.time())
            self.send({'type': 'start', 'start_time': self.start_timestamp, 'seed': self.seed})
            return self.start_timestamp
        return 0
    
    def send_score(self, score):
        self.send({'type': 'score', 'score': score})

    def close(self):
        self.running = False
        self.connected = False
        self.connecting = False
        self.is_host = False
        self.broadcasting = False
        for s in [self.connection, self.tcp_socket, self.udp_socket, self.broadcast_socket]:
            if s:
                try: s.close()
                except: pass
        self.connection = self.tcp_socket = self.udp_socket = self.broadcast_socket = None
        self.room_code = self.status_message = self.error_message = ""
        self.opponent_name = "Waiting..."
        self.opponent_score = 0
    
    def reset(self):
        self.close()
        self.running = True
    
    # ===== P2P LAN DISCOVERY =====
    DISCOVERY_PORT = 9998
    
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
    
    def join_by_code(self, code, password=""):
        """Alias for join_with_code"""
        self.join_with_code(code, password)

