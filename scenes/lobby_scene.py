"""
Lobby Scene - Multiplayer Hub
Room code system, host/client differentiation, song transfer UI.
"""

import pygame
import time
from core.scene_manager import Scene
from core.config import *


class LobbyScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.state = "MENU"
        
        # Navigation
        self.menu_index = 0
        self.menu_items = ["HOST GAME", "JOIN WITH CODE", "BROWSE SERVERS", "DIRECT CONNECT (IP)", "BACK"]
        
        # Input
        self.code_buffer = ""
        self.ip_buffer = ""
        self.password_buffer = ""
        self.room_name_buffer = "TUR ROOM"
        self.input_focus = 0
        
        # Server browser
        self.servers = []
        self.server_index = 0
        self.filter_locked = None
        self.refreshing = False
        
        # Animation
        self.blink_timer = 0

    def on_enter(self, params=None):
        self.state = "MENU"
        self.menu_index = 0
        self.code_buffer = ""
        self.ip_buffer = ""
        self.game.network.reset()
        
    def update(self):
        self.blink_timer = (self.blink_timer + 1) % 60
        
        # Auto-transition when connected as client
        if self.state == "JOINING" and self.game.network.connected:
            self.state = "CLIENT_LOBBY"

    def draw(self, surface):
        r = self.game.renderer
        theme = r.get_theme()
        surface.fill(theme["bg"])
        
        r.draw_text(surface, "◉ MULTIPLAYER ◉", 50, 30, theme["primary"], r.big_font)
        
        # Status bar
        if self.game.network.error_message:
            r.draw_text(surface, f"✗ {self.game.network.error_message}", 50, 700, theme["error"])
        elif self.game.network.status_message:
            r.draw_text(surface, f"● {self.game.network.status_message}", 50, 700, theme["secondary"])
        
        # Draw current state
        if self.state == "MENU":
            self._draw_menu(surface, r, theme)
        elif self.state == "HOST_SETUP":
            self._draw_host_setup(surface, r, theme)
        elif self.state == "HOSTING":
            self._draw_hosting(surface, r, theme)
        elif self.state == "JOIN_CODE":
            self._draw_join_code(surface, r, theme)
        elif self.state == "SERVER_BROWSER":
            self._draw_server_browser(surface, r, theme)
        elif self.state == "DIRECT":
            self._draw_direct(surface, r, theme)
        elif self.state == "JOINING":
            self._draw_joining(surface, r, theme)
        elif self.state == "CLIENT_LOBBY":
            self._draw_client_lobby(surface, r, theme)

    def _draw_menu(self, surface, r, theme):
        """Main menu"""
        r.draw_panel(surface, 100, 150, 400, 350, "SELECT_MODE")
        
        y = 170
        for i, item in enumerate(self.menu_items):
            r.draw_button(surface, item, 120, y, i == self.menu_index, 360)
            y += 50
        
        # How it works panel
        r.draw_panel(surface, 550, 150, 400, 200, "HOW_IT_WORKS")
        r.draw_text(surface, "HOST:", 570, 180, theme["secondary"])
        r.draw_text(surface, "Create room, share code.", 570, 205, (150, 150, 150))
        r.draw_text(surface, "JOIN:", 570, 245, theme["secondary"])
        r.draw_text(surface, "Enter host's room code.", 570, 270, (150, 150, 150))
        r.draw_text(surface, "No port forwarding needed!", 570, 310, theme["primary"])
        
        # NAT Type display
        r.draw_panel(surface, 550, 380, 400, 80, "CONNECTIVITY")
        if hasattr(self, 'nat_status'):
            msg, color = self.nat_status
            r.draw_text(surface, msg, 570, 410, color)
        else:
            r.draw_text(surface, "Checking NAT type...", 570, 410, (100, 100, 100))
            self._check_nat_type()
        
        r.draw_text(surface, "[↑/↓] Navigate  [ENTER] Select  [ESC] Back", 100, 550, (80, 80, 80))
    
    def _check_nat_type(self):
        """Check NAT type in background"""
        if hasattr(self, '_nat_checking'):
            return
        self._nat_checking = True
        
        import threading
        def check():
            try:
                from core.stun_client import get_nat_status_display
                self.nat_status = get_nat_status_display()
            except Exception as e:
                self.nat_status = (f"NAT check failed: {e}", (255, 100, 100))
            self._nat_checking = False
        
        threading.Thread(target=check, daemon=True).start()

    def _draw_host_setup(self, surface, r, theme):
        """Host setup screen"""
        r.draw_panel(surface, 150, 150, 700, 250, "HOST_SETUP")
        
        y = 180
        r.draw_input_field(surface, "ROOM NAME:", self.room_name_buffer, 180, y, 500, self.input_focus == 0)
        y += 80
        r.draw_input_field(surface, "PASSWORD (optional):", self.password_buffer, 180, y, 500, self.input_focus == 1)
        y += 90
        r.draw_button(surface, "CREATE ROOM", 350, y, True, 250)
        r.draw_text(surface, "[TAB] Switch  [ENTER] Create  [ESC] Back", 150, 500, (80, 80, 80))

    def _draw_hosting(self, surface, r, theme):
        """Hosting - show room code prominently"""
        r.draw_panel(surface, 200, 100, 600, 150, "YOUR_ROOM_CODE")
        
        code = self.game.network.room_code or "Generating..."
        if code and code != "LAN-ONLY":
            r.draw_text(surface, code, 350, 150, theme["primary"], r.big_font)
            r.draw_text(surface, "Share this code with your friend!", 320, 210, (150, 150, 150))
        else:
            r.draw_text(surface, "LAN Mode - Share your IP:", 300, 140, theme["secondary"])
            r.draw_text(surface, f"{self.game.network.local_ip}:{self.game.network.port}", 350, 180, theme["text"])
        
        r.draw_panel(surface, 200, 280, 600, 250, "ROOM_STATUS")
        y = 300
        r.draw_text(surface, f"ROOM: {self.room_name_buffer}", 230, y, theme["secondary"])
        y += 40
        
        r.draw_text(surface, "PLAYERS:", 230, y, theme["text"])
        y += 30
        r.draw_text(surface, "  1. You (HOST)", 230, y, theme["primary"])
        y += 30
        
        if self.game.network.connected:
            name = self.game.network.opponent_name
            r.draw_text(surface, f"  2. {name} ✓", 230, y, (100, 255, 100))
            y += 50
            r.draw_button(surface, "START GAME →", 350, y, True, 250)
            r.draw_text(surface, "Press [ENTER] to start!", 370, y + 45, (100, 255, 100))
        else:
            blink = "●" if self.blink_timer < 30 else "○"
            r.draw_text(surface, f"  2. Waiting for player... {blink}", 230, y, (100, 100, 100))
        
        r.draw_text(surface, "[ESC] Close Room", 50, 650, (150, 100, 100))

    def _draw_join_code(self, surface, r, theme):
        """Enter room code"""
        r.draw_panel(surface, 200, 200, 600, 250, "ENTER_ROOM_CODE")
        r.draw_text(surface, "Enter the room code from host:", 250, 230, theme["text"])
        
        display = self.code_buffer.upper() + ("_" if self.blink_timer < 30 else " ")
        pygame.draw.rect(surface, (20, 20, 20), (280, 280, 400, 60))
        pygame.draw.rect(surface, theme["primary"], (280, 280, 400, 60), 2)
        r.draw_text(surface, display, 320, 295, theme["primary"], r.big_font)
        r.draw_text(surface, "Format: XXXX-XXXX", 400, 360, (100, 100, 100))
        r.draw_button(surface, "CONNECT", 370, 400, True, 200)
        r.draw_text(surface, "[ENTER] Connect  [ESC] Back", 330, 500, (80, 80, 80))

    def _draw_direct(self, surface, r, theme):
        """Direct IP connection"""
        r.draw_panel(surface, 150, 180, 700, 280, "DIRECT_CONNECT")
        
        y = 210
        r.draw_input_field(surface, "HOST IP:", self.ip_buffer, 180, y, 500, self.input_focus == 0)
        y += 80
        r.draw_input_field(surface, "PASSWORD:", self.password_buffer, 180, y, 500, self.input_focus == 1)
        y += 90
        r.draw_button(surface, "CONNECT", 370, y, True, 200)
        r.draw_text(surface, "[TAB] Switch  [ENTER] Connect  [ESC] Back", 200, 520, (80, 80, 80))

    def _draw_joining(self, surface, r, theme):
        """Connecting animation"""
        r.draw_panel(surface, 250, 280, 500, 150, "CONNECTING")
        
        dots = "." * ((self.blink_timer // 10) % 4)
        r.draw_text(surface, f"Connecting{dots}", 400, 340, theme["primary"], r.big_font)
        
        if self.game.network.error_message:
            r.draw_text(surface, self.game.network.error_message, 350, 390, theme["error"])
        
        r.draw_text(surface, "[ESC] Cancel", 440, 450, (80, 80, 80))

    def _draw_client_lobby(self, surface, r, theme):
        """Client waiting room"""
        r.draw_panel(surface, 200, 150, 600, 350, "CONNECTED")
        
        y = 180
        r.draw_text(surface, "✓ CONNECTED TO HOST", 350, y, (100, 255, 100), r.big_font)
        y += 60
        
        r.draw_text(surface, "PLAYERS:", 230, y, theme["secondary"])
        y += 30
        r.draw_text(surface, f"  1. {self.game.network.opponent_name} (HOST)", 230, y, theme["primary"])
        y += 30
        r.draw_text(surface, "  2. You", 230, y, theme["text"])
        y += 50
        
        # Transfer progress
        if self.game.network.transfer_total > 0:
            pct = int(100 * self.game.network.transfer_progress / max(1, self.game.network.transfer_total))
            r.draw_text(surface, f"Receiving song: {pct}%", 230, y, theme["secondary"])
            pygame.draw.rect(surface, theme["grid"], (230, y + 25, 400, 20))
            pygame.draw.rect(surface, theme["primary"], (230, y + 25, int(400 * pct / 100), 20))
            y += 60
        
        # Waiting message
        blink = "●" if self.blink_timer < 30 else "○"
        r.draw_text(surface, f"Waiting for host to start {blink}", 300, y, (150, 150, 150))
        
        # Check if game starting
        if self.game.network.start_timestamp > 0:
            remaining = self.game.network.start_timestamp - time.time()
            if remaining > 0:
                r.draw_text(surface, f"STARTING IN {int(remaining) + 1}...", 350, y + 50, theme["primary"], r.big_font)
        
        r.draw_text(surface, "[ESC] Disconnect", 380, 550, (150, 100, 100))

    def _draw_server_browser(self, surface, r, theme):
        """Server browser"""
        r.draw_panel(surface, 50, 100, 920, 500, "SERVER_BROWSER")
        
        # Header row
        r.draw_text(surface, "ROOM NAME", 80, 130, theme["secondary"])
        r.draw_text(surface, "CODE", 350, 130, theme["secondary"])
        r.draw_text(surface, "HOST", 500, 130, theme["secondary"])
        r.draw_text(surface, "🔒", 750, 130, theme["secondary"])
        r.draw_text(surface, "PLAYERS", 820, 130, theme["secondary"])
        
        pygame.draw.line(surface, theme["grid"], (60, 155), (950, 155), 1)
        
        # Filter indicator
        if self.filter_locked is None:
            filter_text = "ALL"
        elif self.filter_locked:
            filter_text = "LOCKED ONLY"
        else:
            filter_text = "UNLOCKED ONLY"
        r.draw_text(surface, f"Filter: {filter_text}", 700, 80, (100, 100, 100))
        
        # Server list
        filtered = self._get_filtered_servers()
        
        if not filtered:
            if self.refreshing:
                dots = "." * ((self.blink_timer // 10) % 4)
                r.draw_text(surface, f"Searching for servers{dots}", 350, 300, (100, 100, 100))
            else:
                r.draw_text(surface, "No servers found. Press R to refresh.", 300, 300, (100, 100, 100))
        else:
            y = 165
            for i, server in enumerate(filtered[:10]):
                if i == self.server_index:
                    pygame.draw.rect(surface, theme["grid"], (55, y - 3, 910, 32))
                
                name = server.get("name", "Unknown Room")[:25]
                r.draw_text(surface, name, 80, y, theme["primary"] if i == self.server_index else theme["text"])
                
                code = server.get("code", "????-????")
                r.draw_text(surface, code, 350, y, (150, 150, 150))
                
                host = server.get("host", "Unknown")[:15]
                r.draw_text(surface, host, 500, y, (150, 150, 150))
                
                if server.get("password"):
                    r.draw_text(surface, "🔒", 750, y, (255, 100, 100))
                else:
                    r.draw_text(surface, "🔓", 750, y, (100, 255, 100))
                
                players = f"{server.get('players', 1)}/2"
                r.draw_text(surface, players, 840, y, (150, 150, 150))
                
                y += 35
        
        r.draw_text(surface, "[↑/↓] Select  [ENTER] Join  [R] Refresh  [F] Filter  [ESC] Back", 150, 620, (80, 80, 80))

    def _get_filtered_servers(self):
        if self.filter_locked is None:
            return self.servers
        elif self.filter_locked:
            return [s for s in self.servers if s.get("password")]
        else:
            return [s for s in self.servers if not s.get("password")]
    
    def _refresh_servers(self):
        """Scan LAN for servers using P2P broadcast"""
        self.refreshing = True
        self.server_index = 0
        
        import threading
        def scan_thread():
            try:
                self.servers = self.game.network.scan_lan_servers(timeout=3.0)
            except Exception as e:
                print(f"Scan error: {e}")
                self.servers = []
            self.refreshing = False
        
        threading.Thread(target=scan_thread, daemon=True).start()

    def _start_game(self):
        """Transition to game scene"""
        from scenes.game_scene import GameScene
        song = self.game.network.selected_song
        diff = self.game.network.selected_difficulty or "MEDIUM"
        
        params = {
            'song': f"songs/{song}" if song else None,
            'difficulty': diff,
            'mode': 'multiplayer'
        }
        self.game.scene_manager.switch_to(GameScene, params)

    def handle_input(self, event):
        if event.type != pygame.KEYDOWN:
            return
        
        key = event.key
        
        if key == pygame.K_ESCAPE:
            self._handle_back()
            return
        
        if self.state == "MENU":
            self._handle_menu(key)
        elif self.state == "HOST_SETUP":
            self._handle_host_setup(key, event)
        elif self.state == "HOSTING":
            self._handle_hosting(key)
        elif self.state == "JOIN_CODE":
            self._handle_join_code(key, event)
        elif self.state == "SERVER_BROWSER":
            self._handle_server_browser(key, event)
        elif self.state == "DIRECT":
            self._handle_direct(key, event)
        elif self.state == "JOINING":
            pass
        elif self.state == "CLIENT_LOBBY":
            self._handle_client_lobby(key)

    def _handle_back(self):
        self.play_sfx("back")
        
        if self.state == "MENU":
            from scenes.menu_scenes import TitleScene
            self.game.scene_manager.switch_to(TitleScene)
        elif self.state in ["HOSTING", "CLIENT_LOBBY", "JOINING"]:
            self.game.network.close()
            self.state = "MENU"
        elif self.state == "SERVER_BROWSER":
            self.state = "MENU"
        else:
            self.state = "MENU"
    
    def _handle_server_browser(self, key, event):
        filtered = self._get_filtered_servers()
        
        if key == pygame.K_UP and filtered:
            self.server_index = (self.server_index - 1) % len(filtered)
            self.play_sfx("blip")
        elif key == pygame.K_DOWN and filtered:
            self.server_index = (self.server_index + 1) % len(filtered)
            self.play_sfx("blip")
        elif key == pygame.K_r:
            self.play_sfx("accept")
            self._refresh_servers()
        elif key == pygame.K_f:
            self.play_sfx("blip")
            if self.filter_locked is None:
                self.filter_locked = False
            elif self.filter_locked is False:
                self.filter_locked = True
            else:
                self.filter_locked = None
            self.server_index = 0
        elif key == pygame.K_RETURN and filtered:
            self.play_sfx("accept")
            server = filtered[self.server_index]
            self.code_buffer = server.get("code", "")
            if server.get("password"):
                pass  # TODO: Show password prompt
            else:
                self.state = "JOINING"
                self.game.network.join_by_code(self.code_buffer)

    def _handle_menu(self, key):
        if key == pygame.K_UP:
            self.menu_index = (self.menu_index - 1) % len(self.menu_items)
            self.play_sfx("blip")
        elif key == pygame.K_DOWN:
            self.menu_index = (self.menu_index + 1) % len(self.menu_items)
            self.play_sfx("blip")
        elif key == pygame.K_RETURN:
            self.play_sfx("accept")
            item = self.menu_items[self.menu_index]
            if item == "HOST GAME":
                self.state = "HOST_SETUP"
            elif item == "JOIN WITH CODE":
                self.state = "JOIN_CODE"
            elif item == "BROWSE SERVERS":
                self.state = "SERVER_BROWSER"
                self._refresh_servers()
            elif item.startswith("DIRECT"):
                self.state = "DIRECT"
                self.input_focus = 0
            elif item == "BACK":
                self._handle_back()

    def _handle_host_setup(self, key, event):
        if key == pygame.K_TAB:
            self.input_focus = (self.input_focus + 1) % 2
            self.play_sfx("blip")
        elif key == pygame.K_RETURN:
            self.play_sfx("accept")
            self.game.network.host_game(self.room_name_buffer, self.password_buffer)
            self.state = "HOSTING"
        elif key == pygame.K_BACKSPACE:
            if self.input_focus == 0:
                self.room_name_buffer = self.room_name_buffer[:-1]
            else:
                self.password_buffer = self.password_buffer[:-1]
        elif event.unicode.isprintable() and len(event.unicode) == 1:
            if self.input_focus == 0 and len(self.room_name_buffer) < 20:
                self.room_name_buffer += event.unicode.upper()
            elif self.input_focus == 1 and len(self.password_buffer) < 16:
                self.password_buffer += event.unicode

    def _handle_hosting(self, key):
        if key == pygame.K_RETURN and self.game.network.connected:
            self.play_sfx("accept")
            from scenes.menu_scenes import SongSelectScene
            self.game.scene_manager.switch_to(SongSelectScene, {'mode': 'multiplayer'})

    def _handle_join_code(self, key, event):
        if key == pygame.K_RETURN:
            # Need exactly 14 chars (XXXX-XXXX-XXXX) or 12 chars without dashes
            clean_code = self.code_buffer.replace('-', '')
            if len(clean_code) == 12:
                self.play_sfx("accept")
                self.game.network.join_with_code(self.code_buffer)
                self.state = "JOINING"
        elif key == pygame.K_BACKSPACE:
            if self.code_buffer:
                # If deleting the dash, delete the char before it too
                if self.code_buffer.endswith('-'):
                    self.code_buffer = self.code_buffer[:-2]
                else:
                    self.code_buffer = self.code_buffer[:-1]
        elif event.unicode.isalnum() and len(self.code_buffer) < 14:
            # Only allow alphanumeric (hex chars), auto-insert dashes
            char = event.unicode.upper()
            # Only allow valid hex characters
            if char in '0123456789ABCDEF':
                clean = self.code_buffer.replace('-', '')
                if len(clean) < 12:
                    clean += char
                    # Auto-format as XXXX-XXXX-XXXX
                    if len(clean) > 8:
                        self.code_buffer = f"{clean[:4]}-{clean[4:8]}-{clean[8:]}"
                    elif len(clean) > 4:
                        self.code_buffer = f"{clean[:4]}-{clean[4:]}"
                    else:
                        self.code_buffer = clean

    def _handle_direct(self, key, event):
        if key == pygame.K_TAB:
            self.input_focus = (self.input_focus + 1) % 2
            self.play_sfx("blip")
        elif key == pygame.K_RETURN:
            if self.ip_buffer:
                self.play_sfx("accept")
                self.game.network.join_game(self.ip_buffer, self.password_buffer)
                self.state = "JOINING"
        elif key == pygame.K_BACKSPACE:
            if self.input_focus == 0:
                self.ip_buffer = self.ip_buffer[:-1]
            else:
                self.password_buffer = self.password_buffer[:-1]
        elif event.unicode.isprintable() and len(event.unicode) == 1:
            if self.input_focus == 0 and len(self.ip_buffer) < 45:
                self.ip_buffer += event.unicode
            elif self.input_focus == 1 and len(self.password_buffer) < 16:
                self.password_buffer += event.unicode

    def _handle_client_lobby(self, key):
        pass
