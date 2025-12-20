import socket
import threading
import json
import time

class NetworkManager:
    def __init__(self, port=9999):
        self.port = port
        self.socket = None
        self.connection = None 
        self.is_host = False
        self.connected = False
        self.opponent_name = "Waiting..."
        self.opponent_score = 0
        self.running = True
        self.lock = threading.Lock()
        
        # Room State
        self.room_password = ""
        self.is_spectator = False
        self.peers = [] # Limit to 1 peer for now for simple 1v1/Spec, or list for advanced
        
        # Game State
        self.start_timestamp = 0
        self.seed = 0

    def host_game(self, password=""):
        self.is_host = True
        self.room_password = password
        threading.Thread(target=self._host_thread, daemon=True).start()

    def join_game(self, ip, password=""):
        self.is_host = False
        self.room_password = password
        threading.Thread(target=self._join_thread, args=(ip,), daemon=True).start()

    def _host_thread(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(('0.0.0.0', self.port))
            self.socket.listen(4) # Allow spectators
            print(f"Hosting on port {self.port}...")
            
            while self.running:
                conn, addr = self.socket.accept()
                print(f"Connection from {addr}")
                # Handle handshake in a thread or immediately?
                # Simple single-peer logic for main game, but for spectator we need lists.
                # Let's stick to 1v1 + spectators later. For now, first connection is Player 2.
                if not self.connection:
                    self.connection = conn
                    self.connected = True
                    threading.Thread(target=self._listen, args=(conn,), daemon=True).start()
                else:
                    # Spectator or reject
                    pass
        except Exception as e:
            print(f"Host Error: {e}")

    def _join_thread(self, ip):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((ip, self.port))
            self.connection = self.socket
            self.connected = True
            
            # Send Handshake
            self.send({'type': 'hello', 'password': self.room_password})
            
            self._listen(self.socket)
        except Exception as e:
            print(f"Join Error: {e}")
            self.connected = False

    def _listen(self, conn):
        buffer = ""
        while self.running:
            try:
                data = conn.recv(4096)
                if not data: break
                
                buffer += data.decode('utf-8')
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if not line: continue
                    try:
                        msg = json.loads(line)
                        self._handle_message(msg, conn)
                    except:
                        pass
            except:
                break
        self.connected = False

    def _handle_message(self, msg, conn):
        with self.lock:
            if msg['type'] == 'hello':
                # Check password if host
                if self.is_host and self.room_password and msg.get('password') != self.room_password:
                    # Reject (Close)
                    self.send({'type': 'error', 'msg': 'Wrong Password'}, conn)
                    conn.close()
                    self.connection = None
                    self.connected = False
                    return
                    
                self.opponent_name = msg.get('name', 'Unknown')
                if self.is_host:
                    # Reply hello
                    self.send({'type': 'hello', 'name': 'HOST'}, conn)

            elif msg['type'] == 'score':
                self.opponent_score = msg['score']
                
            elif msg['type'] == 'start':
                self.start_timestamp = msg['start_time']
                self.seed = msg['seed']
                
            elif msg['type'] == 'error':
                print(f"Network Error: {msg['msg']}")

    def send(self, data, conn=None):
        target = conn or self.connection
        if target:
            try:
                msg = json.dumps(data) + '\n'
                target.send(msg.encode('utf-8'))
            except:
                pass

    def start_game_request(self, seed=None):
        if self.is_host:
            # Set start time to 3 seconds from now
            start_time = time.time() + 3.0
            self.start_timestamp = start_time
            self.seed = seed or int(time.time())
            self.send({'type': 'start', 'start_time': start_time, 'seed': self.seed})
            return start_time
        return 0

    def propose_song(self, filename, difficulty):
        self.send({'type': 'offer_song', 'filename': filename, 'difficulty': difficulty})
        
    def close(self):
        self.running = False
        if self.socket: self.socket.close()
