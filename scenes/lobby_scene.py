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
        
        # Navigation - main menu items
        self.menu_index = 0
        self.menu_items = ["LAN", "ONLINE", "LEADERBOARD", "BACK"]
        
        # Server Status (Delegated to MasterClient)
        # self.server_online is now self.game.master_client.server_online
        
        # Check initially handled by on_enter
        
        # Input buffers
        self.code_buffer = ""
        self.ip_buffer = ""
        self.password_buffer = ""
        self.room_name_buffer = "TUR Room"
        self.max_players_buffer = "2"
        self.input_focus = 0 # 0=Name, 1=Password, 2=MaxPlayers
        
        # Server browser
        self.servers = []
        self.server_index = 0
        self.filter_locked = None
        self.refreshing = False
        
        # Animation
        self.blink_timer = 0
        
        # Spectate mode flag
        self.spectate_mode = False
        
        # Clipboard support
        try:
            pygame.scrap.init()
            self.has_clipboard = True
        except:
            self.has_clipboard = False
        
        # Mode Selection Overlay
        self.selected_mode = None  # "LAN", "DIRECT", "ONLINE"
        self.mode_menu_index = 0
        self.mode_menu_items = []
        
        # Reset network state
        self.game.network.reset()

    def on_enter(self, params=None):
        # Start rate-limited health check (every 5s)
        self.game.master_client.start_monitoring()
        
    def on_exit(self):
        # Stop monitoring when leaving multiplayer menu
        self.game.master_client.stop_monitoring()
        
    def update(self):
        self.blink_timer = (self.blink_timer + 1) % 60
        
        # Auto-transition when connected as client
        if self.state == "JOINING" and self.game.network.connected:
            self.state = "CLIENT_LOBBY"
            
        # Check for game start signal (Client side)
        if self.state == "CLIENT_LOBBY" and self.game.network.start_timestamp > 0:
             if self.game.network.selected_song:
                 self._start_game()

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
        elif self.state == "MODE_SELECT":
            self._draw_menu(surface, r, theme)  # Draw background menu
            self._draw_mode_select(surface, r, theme)  # Draw overlay
        elif self.state == "HOST_SETUP":
            self._draw_host_setup(surface, r, theme)
        elif self.state == "HOSTING":
            self._draw_hosting(surface, r, theme)
        elif self.state == "LAN_JOIN":
            self._draw_lan_join(surface, r, theme)
        elif self.state == "DIRECT_JOIN":
            self._draw_direct_join(surface, r, theme)
        elif self.state == "PLAYIT_HOSTING":
            self._draw_playit_hosting(surface, r, theme)
        elif self.state == "PLAYIT_JOIN":
            self._draw_playit_join(surface, r, theme)
        elif self.state == "JOINING":
            self._draw_joining(surface, r, theme)
        elif self.state == "CLIENT_LOBBY":
            self._draw_client_lobby(surface, r, theme)
        elif self.state == "ONLINE_DEV_POPUP":
            self._draw_menu(surface, r, theme)
            self._draw_online_dev_popup(surface, r, theme)

        elif self.state == "ONLINE_BROWSER":
            self._draw_online_browser(surface, r, theme)
        elif self.state == "ONLINE_HOST_SETUP":
            self._draw_online_host_setup(surface, r, theme)
        elif self.state == "PASSWORD_PROMPT":
            self._draw_password_prompt(surface, r, theme)

    def _draw_mode_select(self, surface, r, theme):
        """Draw mode selection overlay"""
        # Dim background
        dim = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 180))
        surface.blit(dim, (0, 0))
        
        title = f"{self.selected_mode} OPTIONS"
        r.draw_panel(surface, 300, 200, 400, 300, title)
        
        y = 250
        for i, item in enumerate(self.mode_menu_items):
            r.draw_button(surface, item, 350, y, i == self.mode_menu_index, 300)
            y += 60
            
        r.draw_text(surface, "[↑/↓] Select  [ENTER] Confirm  [ESC] Back", 320, 520, (150, 150, 150))

    def _draw_menu(self, surface, r, theme):
        """Main menu"""
        r.draw_panel(surface, 100, 180, 400, 280, "SELECT_MODE")
        
        """Main menu"""
        r.draw_panel(surface, 100, 180, 400, 280, "SELECT_MODE")
        
        y = 225 # Increased from 210 to clear title bar (180+32+padding)
        for i, item in enumerate(self.menu_items):
            # Disable ONLINE if server is offline
            is_online = self.game.master_client.server_online
            disabled = (item == "ONLINE" and not is_online)
            r.draw_button(surface, item, 120, y, i == self.menu_index, 360, disabled=disabled)
            y += 50
        
        # Server Status - rate limited check via MasterClient
        is_online = self.game.master_client.server_online
        status_text = "ONLINE" if is_online else "OFFLINE"
        status_color = (100, 255, 100) if is_online else theme["error"]
        
        r.draw_text(surface, f"SERVER: {status_text}", 120, y + 40, status_color)

        # How it works panel
        r.draw_panel(surface, 550, 180, 400, 180, "HOW_IT_WORKS")
        r.draw_text(surface, "HOST:", 580, 220, theme["secondary"]) 
        r.draw_text(surface, "Detailed settings, public list.", 580, 245, (150, 150, 150))
        r.draw_text(surface, "JOIN:", 580, 285, theme["secondary"])
        r.draw_text(surface, "Browse public servers.", 580, 300, (150, 150, 150))
        r.draw_text(surface, "No port forwarding needed!", 580, 330, theme["primary"])
        
        # NAT Type display
        r.draw_panel(surface, 550, 390, 400, 80, "CONNECTIVITY")
        if hasattr(self, 'nat_status'):
            msg, color = self.nat_status
            r.draw_text(surface, msg, 570, 430, color) # Increased from 420 (390+32=422)
        else:
            r.draw_text(surface, "Checking NAT type...", 570, 420, (100, 100, 100))
            self._check_nat_type()
        
        r.draw_text(surface, "[↑/↓] Navigate  [ENTER] Select  [P] Profile  [ESC] Back", 100, 580, (80, 80, 80))
    
    def _check_nat_type(self):
        """NAT check - no longer uses STUN"""
        # STUN was removed - this is now a no-op
        self.nat_status = ("Local network", (150, 150, 150))

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
        """Hosting - simplified for server browser"""
        # Show Room Info
        r.draw_panel(surface, 200, 150, 600, 400, "LOBBY_STATUS")
        
        y = 200
        r.draw_text(surface, f"ROOM: {self.room_name_buffer}", 230, y, theme["primary"])
        y += 40
        # Replace Port display with Password Toggle
        show_pw = getattr(self, 'show_password', False)
        pw_str = self.password_buffer if show_pw else ("****" if self.password_buffer else "NONE")
        pw_col = theme["secondary"] if not show_pw else theme["primary"]
        
        r.draw_text(surface, f"PASSWORD: {pw_str}", 230, y, pw_col)
        y += 60
        
        r.draw_text(surface, "PLAYERS:", 230, y, theme["text"])
        y += 35
        # 1. Self
        label = " (HOST)"
        if self.game.settings.get("is_admin") and not self.game.settings.get("is_stealth"):
            label += " [ROOT ADMIN]"
        r.draw_text(surface, f"  1. You{label}", 230, y, theme["primary"])
        y += 30
        
        # 2. Opponent
        p_name = self.game.network.opponent_name
        p_label = ""
        if getattr(self.game.network, 'opponent_is_admin', False):
            p_label = " [ROOT ADMIN]"
        r.draw_text(surface, f"  2. {p_name}{p_label}", 230, y, theme["text"])
        
        if self.game.network.connected:
            name = self.game.network.opponent_name
            r.draw_text(surface, f"  2. {name} ✓", 230, y, (100, 255, 100))
            y += 50
            r.draw_button(surface, "START GAME →", 350, y, True, 250)
            r.draw_text(surface, "Press [ENTER] to start!", 370, y + 45, (100, 255, 100))
        else:
            blink = "●" if self.blink_timer < 30 else "○"
            r.draw_text(surface, f"  2. Waiting for player... {blink}", 230, y, (100, 100, 100))
        
        r.draw_text(surface, "[ESC] Close Room  [F1] Show/Hide Password", 50, 650, (150, 100, 100))
        
        # Server Status at Bottom Right (replacing old room code location)
        sw, sh = surface.get_width(), surface.get_height()
        # Increased padding from right (sw - 280 -> sw - 360) to prevent clipping
        r.draw_text(surface, "STATUS: ONLINE (HOSTING)", sw - 360, sh - 40, (100, 255, 100))

    def _draw_lan_join(self, surface, r, theme):
        """LAN game browser - shows games on same network"""
        r.draw_panel(surface, 100, 120, 800, 420, "LAN_GAMES")
        
        r.draw_text(surface, "Games on your local network:", 130, 155, theme["secondary"])
        
        # Server list
        filtered = self._get_filtered_servers()
        
        if self.refreshing:
            dots = "." * ((self.blink_timer // 10) % 4)
            r.draw_text(surface, f"Scanning network{dots}", 350, 300, (100, 100, 100))
        elif not filtered:
            r.draw_text(surface, "No games found on LAN.", 350, 280, (100, 100, 100))
            r.draw_text(surface, "Make sure host is on same network.", 310, 310, (80, 80, 80))
        else:
            y = 190
            for i, server in enumerate(filtered[:8]):
                if i == self.server_index:
                    pygame.draw.rect(surface, theme["grid"], (110, y - 3, 780, 32))
                
                name = server.get("name", "TUR Room")[:30]
                ip = server.get("ip", "?")
                r.draw_text(surface, name, 130, y, theme["primary"] if i == self.server_index else theme["text"])
                r.draw_text(surface, ip, 500, y, (150, 150, 150))
                
                if server.get("password"):
                    r.draw_text(surface, "🔒", 700, y, (255, 100, 100))
                y += 40
        
        r.draw_text(surface, "[↑/↓] Select  [ENTER] Join  [R] Refresh  [ESC] Back", 200, 560, (80, 80, 80))

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
        
        """Client waiting room"""
        r.draw_panel(surface, 200, 150, 600, 350, "CONNECTED")
        
        y = 200 # Increased from 180 to clear title bar
        r.draw_text(surface, "✓ CONNECTED TO HOST", 350, y, (100, 255, 100), r.big_font)
        y += 60
        
        r.draw_text(surface, "PLAYERS:", 230, y, theme["secondary"])
        y += 30
        # 1. Host
        h_label = " (HOST)"
        if getattr(self.game.network, 'opponent_is_admin', False):
             h_label += " [ROOT ADMIN]"
        r.draw_text(surface, f"  1. {self.game.network.opponent_name}{h_label}", 230, y, theme["primary"])
        y += 30
        
        # 2. Self (Client)
        p2_label = ""
        if self.game.settings.get("is_admin") and not self.game.settings.get("is_stealth"):
            p2_label = " [ROOT ADMIN]"
        r.draw_text(surface, f"  2. You{p2_label}", 230, y, theme["text"])
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
            'song': song,  # Just the filename, game_scene.py adds 'songs/' prefix
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
        elif self.state == "MODE_SELECT":
            self._handle_mode_select(key)
        elif self.state == "HOST_SETUP":
            self._handle_host_setup(key, event)
        elif self.state == "HOSTING":
            self._handle_hosting(key)
        elif self.state == "LAN_JOIN":
            self._handle_lan_join(key, event)
        elif self.state == "DIRECT_JOIN":
            self._handle_direct_join(key, event)
        elif self.state == "PLAYIT_HOSTING":
            self._handle_playit_hosting(key)
        elif self.state == "PLAYIT_JOIN":
            self._handle_playit_join(key, event)
        elif self.state == "JOINING":
            pass
        elif self.state == "CLIENT_LOBBY":
            self._handle_client_lobby(key)
        elif self.state == "ONLINE_DEV_POPUP":
            self._handle_online_dev_popup(key)

        elif self.state == "ONLINE_BROWSER":
            self._handle_online_browser(key)
        elif self.state == "ONLINE_HOST_SETUP":
            self._handle_online_host_setup(key, event)
        elif self.state == "PASSWORD_PROMPT":
            self._handle_password_prompt(key, event)

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
    


    def _draw_direct_join(self, surface, r, theme):
        """Direct Connect Join UI"""
        r.draw_panel(surface, 150, 150, 700, 300, "DIRECT_CONNECT")
        
        r.draw_text(surface, "Enter Host IP or Room Code (IP:PORT optional):", 180, 190, theme["secondary"])
        
        r.draw_input_field(surface, "ADDRESS/CODE:", self.code_buffer, 180, 230, 600, self.input_focus == 0)
        
        r.draw_button(surface, "CONNECT", 370, 320, True, 200)
        r.draw_text(surface, "[ENTER] Connect  [ESC] Back", 330, 420, (80, 80, 80))

    def _handle_direct_join(self, key, event):
        ctrl = (pygame.key.get_mods() & pygame.KMOD_CTRL)
        
        if key == pygame.K_RETURN:
            if self.code_buffer:
                self.play_sfx("accept")
                # Try to determine if it's a code or IP
                # Only assume IP if it looks like one (has dots)
                if '.' in self.code_buffer or ':' in self.code_buffer:
                    self.game.network.join_game(self.code_buffer)
                else:
                    self.game.network.join_with_code(self.code_buffer)
                
                self.state = "JOINING"
        
        elif key == pygame.K_v and ctrl:
            text = self._get_clipboard()
            if text:
                self.code_buffer += text
                
        elif key == pygame.K_BACKSPACE:
             self.code_buffer = self.code_buffer[:-1]
             
        elif event.unicode.isprintable() and len(self.code_buffer) < 60:
             self.code_buffer += event.unicode
             
        elif key == pygame.K_ESCAPE:
             self.state = "MODE_SELECT"

    def _handle_menu(self, key):
        if key == pygame.K_UP:
            self.menu_index = (self.menu_index - 1) % len(self.menu_items)
            self.play_sfx("blip")
        elif key == pygame.K_DOWN:
            self.menu_index = (self.menu_index + 1) % len(self.menu_items)
            self.play_sfx("blip")
        elif key == pygame.K_p:
            from scenes.profile_scene import ProfileScene
            self.game.scene_manager.switch_to(ProfileScene)
        elif key == pygame.K_RETURN:
            self.play_sfx("accept")
            item = self.menu_items[self.menu_index]
            
            if item == "LAN":
                self.selected_mode = "LAN"
                self.mode_menu_items = ["HOST GAME", "JOIN GAME", "BACK"]
                self.mode_menu_index = 0
                self.state = "MODE_SELECT"
                
            elif item == "ONLINE":
                if not self.game.master_client.server_online:
                     self.play_sfx("back")
                     return
                
                self.selected_mode = "ONLINE"
                self._start_online_mode()
            
            elif item == "LEADERBOARD":
                 from scenes.leaderboard_scene import LeaderboardScene
                 self.game.scene_manager.switch_to(LeaderboardScene)
                    
            elif item == "BACK":
                self.game.scene_manager.pop_scene()

    def _handle_mode_select(self, key):
        if key == pygame.K_UP:
            self.mode_menu_index = (self.mode_menu_index - 1) % len(self.mode_menu_items)
            self.play_sfx("blip")
        elif key == pygame.K_DOWN:
            self.mode_menu_index = (self.mode_menu_index + 1) % len(self.mode_menu_items)
            self.play_sfx("blip")
        elif key == pygame.K_ESCAPE:
            self.state = "MENU"
        elif key == pygame.K_RETURN:
            self.play_sfx("accept")
            item = self.mode_menu_items[self.mode_menu_index]
            
            if item == "BACK":
                self.state = "MENU"
                return

            # Dispatch based on Mode + Item
            if self.selected_mode == "LAN":
                if item == "HOST GAME":
                    self.state = "HOST_SETUP"
                    self.input_focus = 0
                elif item == "JOIN GAME":
                    self.state = "LAN_JOIN"
                    self._refresh_servers()
            
            elif self.selected_mode == "DIRECT":
                if item == "HOST GAME":
                    self.state = "HOST_SETUP"
                    self.input_focus = 0
                elif item == "JOIN GAME":
                    self.state = "DIRECT_JOIN"
                    self.input_focus = 0
            
            if self.selected_mode == "ONLINE":
                if item == "BROWSE SERVERS":
                    self.state = "ONLINE_BROWSER"
                    self.server_index = 0
                    self._refresh_online_servers()
                    
                elif item == "HOST GAME":
                    # Go to setup screen first for room name and password
                    self.state = "ONLINE_HOST_SETUP"
                    self.input_focus = 0
                    # Default to Relay for Online Hosting
                    self.use_playit = True
                    
                elif item == "DIRECT JOIN":
                    self.code_buffer = ""
                    self.state = "DIRECT_JOIN"
                    self.input_focus = 0


    def _handle_host_setup(self, key, event):
        ctrl = (pygame.key.get_mods() & pygame.KMOD_CTRL)
        
        if key == pygame.K_TAB:
            self.input_focus = (self.input_focus + 1) % 2
            self.play_sfx("blip")
        
        elif key == pygame.K_v and ctrl:
            text = self._get_clipboard()
            if text:
                if self.input_focus == 0:
                    self.room_name_buffer += text
                elif self.input_focus == 1:
                    self.password_buffer += text
                    
        elif key == pygame.K_RETURN:
            self.play_sfx("accept")
            room_name = self.room_name_buffer or "TUR Room"
            password = self.password_buffer
            
            # LAN / DIRECT hosting
            self.game.network.host_game(room_name, password)
            self.state = "HOSTING"
                
        elif key == pygame.K_BACKSPACE:
            if self.input_focus == 0:
                self.room_name_buffer = self.room_name_buffer[:-1]
            else:
                self.password_buffer = self.password_buffer[:-1]
        elif event.unicode.isprintable() and not ctrl:
            if self.input_focus == 0 and len(self.room_name_buffer) < 20:
                self.room_name_buffer += event.unicode.upper()
            elif self.input_focus == 1:
                if len(self.password_buffer) < 16:
                    self.password_buffer += event.unicode
        elif key == pygame.K_ESCAPE:
            self.state = "MODE_SELECT"

    def _handle_hosting(self, key):
        if key == pygame.K_RETURN and self.game.network.connected:
            self.play_sfx("accept")
            from scenes.menu_scenes import SongSelectScene
            self.game.scene_manager.switch_to(SongSelectScene, {'mode': 'multiplayer'})
             
        elif key == pygame.K_F1:
            self.show_password = not getattr(self, 'show_password', False)
            self.play_sfx("blip")



    def _handle_lan_join(self, key, event):
        """Handle LAN join browser"""
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
        elif key == pygame.K_RETURN and filtered:
            self.play_sfx("accept")
            server = filtered[self.server_index]
            ip = server.get("ip", "")
            if ip:
                self.game.network.join_game(ip)
                self.state = "JOINING"

    def _get_clipboard(self):
        """Safe clipboard retrieval with multiple fallbacks"""
        text = ""
        
        # Method 1: Pygame Scrap (Primary)
        if getattr(self, 'has_clipboard', False):
            try:
                content = pygame.scrap.get(pygame.SCRAP_TEXT)
                if content:
                    text = content.decode('utf-8').strip('\x00')
            except:
                pass
        
        if text: return text

        # Method 2: Tkinter (Universal Fallback)
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
            text = root.clipboard_get()
            root.destroy()
            if text: return text
        except:
            pass

        # Method 3: Linux System Commands (Wayland/X11)
        import platform
        if platform.system() == "Linux":
            import subprocess
            commands = [
                ['wl-paste'],
                ['xclip', '-o', '-selection', 'clipboard'],
                ['xsel', '-ob']
            ]
            for cmd in commands:
                try:
                    out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, timeout=0.5)
                    text = out.decode('utf-8').strip()
                    if text: return text
                except:
                    continue
                    
        return ""

    def _draw_playit_hosting(self, surface, r, theme):
        """Draw playit hosting UI"""
        center_x = 512  # SCREEN_WIDTH // 2
        
        playit = getattr(self.game, 'playit_manager', None)
        claim_code = playit.claim_code if playit else None
        tunnel_addr = playit.get_tunnel_address() if playit else None
        
        # Downloading state
        if playit and playit.status_message and "Download" in playit.status_message:
            r.draw_panel(surface, center_x - 200, 280, 400, 100, "SETTING_UP")
            r.draw_text(surface, playit.status_message, center_x - 80, 320, theme["primary"])
            return
            
        # Starting / connecting state
        if not claim_code and not tunnel_addr:
            r.draw_panel(surface, center_x - 200, 280, 400, 100, "CONNECTING")
            dots = "." * ((self.blink_timer // 10) % 4)
            r.draw_text(surface, f"Starting tunnel{dots}", center_x - 80, 320, theme["primary"])
            if playit and playit.status_message:
                r.draw_text(surface, playit.status_message[:50], center_x - 100, 350, (150, 150, 150))
            return
            
        # First-time setup - show claim code
        if claim_code and not tunnel_addr:
            big_panel_x = center_x - 350
            r.draw_panel(surface, big_panel_x, 120, 700, 350, "FIRST_TIME_SETUP")
            
            # Store claim URL for copying
            self._claim_url = f"https://playit.gg/claim/{claim_code}"
            
            r.draw_text(surface, "One-time setup required", center_x - 140, 150, theme["primary"], r.big_font)
            
            r.draw_text(surface, "1. Go to this link:", big_panel_x + 50, 200, theme["text"])
            url_text = f"playit.gg/claim/{claim_code}"
            pygame.draw.rect(surface, (20, 30, 20), (big_panel_x + 50, 230, 600, 45))
            pygame.draw.rect(surface, (100, 255, 100), (big_panel_x + 50, 230, 600, 45), 2)
            r.draw_text(surface, url_text, big_panel_x + 70, 242, (100, 255, 100), r.big_font)
            
            r.draw_text(surface, "2. Create a FREE account (no credit card needed)", big_panel_x + 50, 295, theme["text"])
            r.draw_text(surface, "3. Done! Connection starts automatically", big_panel_x + 50, 330, theme["text"])
            
            blink = "●" if self.blink_timer < 30 else "○"
            r.draw_text(surface, f"Waiting for setup... {blink}", center_x - 100, 380, (150, 150, 150))
            r.draw_text(surface, "[O] Open in Browser", center_x - 80, 420, (80, 180, 80))
            return
            
        # Tunnel is ready - show room code
        if tunnel_addr:
            short_code = self._get_short_code(tunnel_addr)
            
            r.draw_panel(surface, center_x - 250, 150, 500, 200, "YOUR_ROOM_CODE")
            r.draw_text(surface, short_code, center_x - len(short_code) * 12, 200, theme["primary"], r.big_font)
            r.draw_text(surface, "Share this code with friends!", center_x - 110, 260, (150, 150, 150))
            r.draw_text(surface, f"Full address: {tunnel_addr}", center_x - 150, 300, (80, 80, 80))
            
            if self.game.network.connected:
                r.draw_text(surface, "● Player Connected!", center_x - 80, 380, (100, 255, 100))
                r.draw_text(surface, "[ENTER] Start Game", center_x - 80, 420, theme["primary"])
            else:
                blink = "●" if self.blink_timer < 30 else "○"
                r.draw_text(surface, f"Waiting for player... {blink}", center_x - 100, 380, (150, 150, 150))

    def _get_short_code(self, tunnel_addr):
        """Extract short code from tunnel address"""
        # tunnel_addr format: abc123.at.playit.gg:12345
        if ".at.playit.gg:" in tunnel_addr:
            parts = tunnel_addr.split(".at.playit.gg:")
            short = parts[0].upper()
            port = parts[1]
            return f"{short}:{port}"
        return tunnel_addr

    def _draw_playit_join(self, surface, r, theme):
        """Draw playit join UI"""
        center_x = 512
        title = "SPECTATE" if getattr(self, 'spectate_mode', False) else "JOIN_ONLINE"
        r.draw_panel(surface, center_x - 300, 180, 600, 280, title)
        
        r.draw_text(surface, "Enter room code:", center_x - 70, 220, theme["text"])
        
        display = self.code_buffer.upper() + ("_" if self.blink_timer < 30 else " ")
        pygame.draw.rect(surface, (20, 20, 20), (center_x - 200, 260, 400, 60))
        pygame.draw.rect(surface, theme["primary"], (center_x - 200, 260, 400, 60), 2)
        r.draw_text(surface, display, center_x - 180, 280, theme["primary"], r.big_font)
        
        r.draw_text(surface, "Format: ABC123:12345", center_x - 80, 340, (100, 100, 100))
        
        btn_text = "SPECTATE" if getattr(self, 'spectate_mode', False) else "JOIN"
        r.draw_button(surface, btn_text, center_x - 75, 380, True, 150)
        r.draw_text(surface, "[ENTER] Connect  [CTRL+V] Paste  [ESC] Back", center_x - 170, 450, (80, 80, 80))

    def _handle_playit_hosting(self, key):
        """Handle input while hosting via playit"""
        if key == pygame.K_RETURN and self.game.network.connected:
            self.play_sfx("accept")
            from scenes.menu_scenes import SongSelectScene
            self.game.scene_manager.switch_to(SongSelectScene, {'mode': 'multiplayer'})
        
        elif key == pygame.K_o:
            if hasattr(self, '_claim_url'):
                import webbrowser
                webbrowser.open(self._claim_url)
                self.play_sfx("blip")

    def _handle_playit_join(self, key, event):
        """Handle playit join input"""
        ctrl = (pygame.key.get_mods() & pygame.KMOD_CTRL)
        
        if key == pygame.K_v and ctrl:
            text = self._get_clipboard()
            if text:
                self.code_buffer += text.strip()
        elif key == pygame.K_RETURN:
            if self.code_buffer:
                self.play_sfx("accept")
                code = self.code_buffer.strip()
                
                # Expand short code to full address if needed
                # Short format: ABC123:12345 -> abc123.at.playit.gg:12345
                if ":" in code and "playit" not in code.lower():
                    parts = code.rsplit(":", 1)
                    short = parts[0].lower()
                    port = parts[1]
                    code = f"{short}.at.playit.gg:{port}"
                
                # Parse host:port format
                if ":" in code:
                    host, port_str = code.rsplit(":", 1)
                    try:
                        port = int(port_str)
                        self.game.network.join_game(host, port)
                        self.game.network.is_spectator = getattr(self, 'spectate_mode', False)
                        self.state = "JOINING"
                    except ValueError:
                        self.game.network.error_message = "Invalid port number"
                else:
                    self.game.network.error_message = "Format: CODE:PORT"
        elif key == pygame.K_BACKSPACE:
            self.code_buffer = self.code_buffer[:-1]
        elif event.unicode.isprintable() and len(self.code_buffer) < 40:
            self.code_buffer += event.unicode

    def _handle_client_lobby(self, key):
        if key == pygame.K_ESCAPE:
            self._handle_back()

    def _draw_online_dev_popup(self, surface, r, theme):
        """Draw 'Online is in development' popup"""
        # Dim background
        dim = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 180))
        surface.blit(dim, (0, 0))
        
        # Draw popup panel
        r.draw_panel(surface, 200, 230, 600, 200, "ONLINE_MULTIPLAYER")
        
        r.draw_text(surface, "⚠ IN DEVELOPMENT ⚠", 360, 280, theme["primary"], r.big_font)
        r.draw_text(surface, "Online multiplayer is coming soon!", 300, 340, theme["text"])
        r.draw_text(surface, "Use LAN or Direct Connect for now.", 290, 375, (150, 150, 150))
        
        r.draw_text(surface, "[ENTER / ESC] Back", 410, 420, (80, 80, 80))

    def _handle_online_dev_popup(self, key):
        """Handle input for the online dev popup"""
        if key in (pygame.K_RETURN, pygame.K_ESCAPE):
            self.play_sfx("back")
            self.state = "MENU"

    def _start_online_mode(self):
        """Show online mode options with server browser"""
        self.selected_mode = "ONLINE"
    def _start_online_mode(self):
        """Show online mode options with server browser"""
        self.selected_mode = "ONLINE"
        self.selected_mode = "ONLINE"
        self.mode_menu_items = ["BROWSE SERVERS", "HOST GAME", "BACK"]
        self.mode_menu_index = 0
        self.state = "MODE_SELECT"

        # Initialize master client
        from core.master_client import get_master_client
        self.master_client = get_master_client()
        
        # Start fetching servers in background
        self.online_servers = []
        self.online_refreshing = False
        self._refresh_online_servers()
    
    def _refresh_online_servers(self):
        """Fetch servers from master server"""
        self.online_refreshing = True
        
        def callback(servers):
            self.online_servers = servers or []
            self.online_refreshing = False
        
        self.master_client.get_servers_async(callback)
    
    # Tailscale Setup Removed

    
    def _draw_tailscale_hosting(self, surface, r, theme):
        """Draw hosting screen with cached IP display"""
        # HUGE panel height to fit everything with comfortable spacing
        r.draw_panel(surface, 50, 50, 924, 668, "") 
        
        r.draw_text(surface, "HOSTING GAME", 360, 90, theme["primary"], r.big_font)
        
        # Use cached IPs (prevents lag from subprocess calls)
        from core.network_manager import get_local_ip
        local_ip = get_local_ip()
        port = self.game.network.port
        # tailscale_ip removed

        
        r.draw_text(surface, "Share this address with your friend:", 260, 150, theme["secondary"])
        
        # Display connection info
        y = 200

        
        # Local IP Panel
        r.draw_panel(surface, 150, y, 724, 110, "LOCAL WIFI (LAN)")
        addr = f"{local_ip}:{port}"
        text_x = 512 - (len(addr) * 9)
        r.draw_text(surface, addr, text_x, y + 35, theme["text"], r.big_font)
        r.draw_text(surface, "Use this if your friend is on the same WiFi", 330, y + 80, (100, 100, 100))
        
        y += 160 # Gap before instructions
        
        # Instructions for friend
        r.draw_text(surface, "YOUR FRIEND SHOULD:", 400, y, theme["text"])
        r.draw_text(surface, "1. Go to Multiplayer > Direct Connect", 330, y + 35, theme["secondary"])
        r.draw_text(surface, "2. Enter the address above", 380, y + 70, (180, 180, 180))
        
        # Connection status
        y_status = 660
        if self.game.network.connected:
            r.draw_text(surface, "PLAYER CONNECTED!", 400, y_status, (50, 255, 50), r.big_font)
        else:
            dots = "." * ((self.blink_timer // 15) % 4)
            r.draw_text(surface, f"Waiting for player{dots}", 400, y_status, theme["secondary"])
        
        r.draw_text(surface, "[ESC] Cancel", 450, 690, (80, 80, 80))
    


    def _draw_online_browser(self, surface, r, theme):
        """Draw online server browser"""
        r.draw_panel(surface, 80, 100, 864, 500, "ONLINE_SERVERS")
        
        r.draw_text(surface, "PUBLIC GAME SERVERS", 350, 140, theme["primary"], r.big_font)
        
        # Server list
        servers = getattr(self, 'online_servers', [])
        refreshing = getattr(self, 'online_refreshing', False)
        
        if refreshing:
            dots = "." * ((self.blink_timer // 10) % 4)
            r.draw_text(surface, f"Loading servers{dots}", 400, 320, (150, 150, 150))
        elif not servers:
            mc_error = getattr(self.master_client, 'error', None)
            if mc_error:
                r.draw_high_viz_popup(surface, "SYSTEM_ERROR", mc_error)
                r.draw_text(surface, "PRESS [R] TO RETRY CONNECTION", 350, 520, (150, 150, 150), r.small_font)
            else:
                r.draw_text(surface, "No servers online.", 420, 280, (150, 150, 150))
                r.draw_text(surface, "Be the first to host!", 400, 320, theme["secondary"])
        else:
            # Header row
            r.draw_text(surface, "NAME", 140, 190, theme["secondary"])
            r.draw_text(surface, "HOST", 460, 190, theme["secondary"])
            r.draw_text(surface, "PLAYERS", 710, 190, theme["secondary"])
            
            y = 220
            visible_count = 8
            start_idx = max(0, getattr(self, 'server_index', 0) - 4)
            if start_idx + visible_count > len(servers):
                start_idx = max(0, len(servers) - visible_count)
            
            for i in range(start_idx, min(start_idx + visible_count, len(servers))):
                srv = servers[i]
                selected = (i == getattr(self, 'server_index', 0))
                
                if selected:
                    pygame.draw.rect(surface, theme["grid"], (90, y - 3, 840, 32))
                
                name = srv.get("name", "TUR Room")[:25]
                host_name = srv.get("host_name", "Anonymous")[:15]
                players = f"{srv.get('player_count', 1)}/{srv.get('max_players', 2)}"
                
                color = theme["primary"] if selected else theme["text"]
                r.draw_text(surface, name, 140, y, color)
                r.draw_text(surface, host_name, 460, y, (150, 150, 150))
                r.draw_text(surface, players, 730, y, (150, 150, 150))
                
                if srv.get("password_protected"):
                    r.draw_text(surface, "🔒", 850, y, (255, 100, 100))
                
                y += 35
        
        # Controls
        r.draw_text(surface, "[↑/↓] Select  [ENTER] Join  [R] Refresh  [ESC] Back", 250, 560, (80, 80, 80))
        
        # Master server status
        mc = getattr(self, 'master_client', None)
        if mc and mc.error:
            r.draw_text(surface, f"⚠ {mc.error}", 100, 620, theme["error"])

    def _handle_online_browser(self, key):
        """Handle input in online server browser"""
        servers = getattr(self, 'online_servers', [])
        
        if key == pygame.K_UP and servers:
            self.server_index = (self.server_index - 1) % len(servers)
            self.play_sfx("blip")
        elif key == pygame.K_DOWN and servers:
            self.server_index = (self.server_index + 1) % len(servers)
            self.play_sfx("blip")
        elif key == pygame.K_r:
            self.play_sfx("accept")
            self._refresh_online_servers()
        elif key == pygame.K_RETURN and servers:
            self.play_sfx("accept")
            srv = servers[self.server_index]
            ip = srv.get("host_ip", "")
            port = srv.get("port", 1337)
            
            if ip:
                # Check if password protected
                if srv.get("password_protected"):
                    # Store server info and prompt for password
                    self.pending_server = srv
                    self.join_password_buffer = ""
                    self.state = "PASSWORD_PROMPT"
                else:
                    # Join directly
                    if str(ip).startswith("relay:"):
                        room_id = ip.split(":")[1]
                        self.game.network.join_relay(room_id)
                    else:
                        self.game.network.join_game(f"{ip}:{port}")
                    self.state = "JOINING"
            else:
                self.game.network.error_message = "Server has invalid address"
        elif key == pygame.K_ESCAPE:
            self.play_sfx("back")
            self.state = "MENU"

    def _draw_online_host_setup(self, surface, r, theme):
        """Online host setup screen with room name and password"""
        r.draw_panel(surface, 150, 120, 700, 300, "HOST_ONLINE_GAME")
        
        r.draw_text(surface, "Configure your game server:", 280, 160, theme["secondary"])
        
        y = 200
        r.draw_input_field(surface, "ROOM NAME:", self.room_name_buffer, 180, y, 500, self.input_focus == 0)
        y += 80
        # Show password as asterisks
        pw_display = "*" * len(self.password_buffer) if self.password_buffer else ""
        r.draw_input_field(surface, "PASSWORD (optional):", pw_display, 180, y, 500, self.input_focus == 1)
        
        y += 80
        r.draw_input_field(surface, "MAX PLAYERS (2-16):", self.max_players_buffer, 180, y, 300, self.input_focus == 2)
        
        y += 80
        r.draw_button(surface, "START HOSTING", 350, y, True, 250)
        
        r.draw_text(surface, "[TAB] Switch  [ENTER] Start  [ESC] Back", 150, 600, (80, 80, 80))
        if self.password_buffer:
            r.draw_text(surface, "🔒 Password protected - players must enter password to join", 200, 560, (150, 200, 150))

    def _handle_online_host_setup(self, key, event):
        """Handle input for online host setup"""
        ctrl = (pygame.key.get_mods() & pygame.KMOD_CTRL)
        
        if key == pygame.K_TAB:
            self.input_focus = (self.input_focus + 1) % 3
            self.play_sfx("blip")
        
        elif key == pygame.K_v and ctrl:
            text = self._get_clipboard()
            if text:
                if self.input_focus == 0:
                    self.room_name_buffer += text
                elif self.input_focus == 1:
                    self.password_buffer += text
                    # No paste for max players
                    
        elif key == pygame.K_RETURN:
            room_name = self.room_name_buffer or "TUR Room"
            password = self.password_buffer
            
            # Validate max players
            try:
                max_players = int(self.max_players_buffer)
            except:
                max_players = 2
            
            if max_players > 16:
                self.game.network.error_message = "Limit is 16 players!"
                self.play_sfx("miss")
                return
            
            if max_players < 2:
                # User requested "let it not go under 2" - auto fix or block?
                # "let it not go under 2 players" implies enforcement
                max_players = 2
                self.max_players_buffer = "2"
            
            # Start hosting with password
            if getattr(self, 'use_playit', False):
                # Use WebSocket Relay (Server-side)
                self.game.network.host_relay(room_name, password)
                
                # Register with master server so it appears in browser
                # For Relay, we register with a special "relay:ROOMID" address
                # Wait for room ID to be generated? It's generated in host_relay immediately.
                time.sleep(0.1) 
                
                from core.master_client import get_master_client
                mc = get_master_client()
                mc.register_server(
                    name=room_name,
                    port=0, # Port 0 indicates relay/virtual
                    password_protected=bool(password),
                    max_players=max_players,
                    public_ip=f"relay:{self.game.network.relay_room_id}"
                )
                
                self.state = "HOSTING"
                
            else:
                # Standard TCP/IP Hosting
                self.game.network.host_game(room_name, password) 
                
                # Register with master server with Public IP (auto-detected by master)
                from core.master_client import get_master_client
                mc = get_master_client()
                mc.register_server(
                    name=room_name,
                    port=self.game.network.port,
                    password_protected=bool(password),
                    max_players=max_players
                )
                self.state = "HOSTING"

            self.play_sfx("accept")
            self.show_password = False # Init toggle state
            
        elif key == pygame.K_ESCAPE:
            self.play_sfx("back")
            self.state = "MODE_SELECT"
            
        elif key == pygame.K_BACKSPACE:
            if self.input_focus == 0 and self.room_name_buffer:
                self.room_name_buffer = self.room_name_buffer[:-1]
            elif self.input_focus == 1 and self.password_buffer:
                self.password_buffer = self.password_buffer[:-1]
            elif self.input_focus == 2 and self.max_players_buffer:
                self.max_players_buffer = self.max_players_buffer[:-1]
                
        elif event.unicode.isprintable() and len(event.unicode) > 0:
            if self.input_focus == 0:
                if len(self.room_name_buffer) < 20:
                    self.room_name_buffer += event.unicode
            elif self.input_focus == 1:
                if len(self.password_buffer) < 16:
                    self.password_buffer += event.unicode
            elif self.input_focus == 2:
                if event.unicode.isdigit() and len(self.max_players_buffer) < 2:
                    self.max_players_buffer += event.unicode

    def _draw_password_prompt(self, surface, r, theme):
        """Draw password entry prompt for joining protected server"""
        r.draw_panel(surface, 200, 180, 600, 200, "ENTER_PASSWORD")
        
        srv = getattr(self, 'pending_server', {})
        srv_name = srv.get("name", "Server")[:25]
        
        r.draw_text(surface, f"Joining: {srv_name}", 350, 220, theme["secondary"])
        r.draw_text(surface, "This server requires a password", 320, 250, (150, 150, 150))
        
        # Password input
        pw = getattr(self, 'join_password_buffer', '')
        pw_display = "*" * len(pw) if pw else ""
        r.draw_input_field(surface, "PASSWORD:", pw_display, 230, 290, 400, True)
        
        r.draw_text(surface, "[ENTER] Join  [ESC] Cancel", 340, 360, (80, 80, 80))

    def _handle_password_prompt(self, key, event):
        """Handle input for password prompt"""
        if key == pygame.K_ESCAPE:
            self.play_sfx("back")
            self.pending_server = None
            self.state = "ONLINE_BROWSER"
            
        elif key == pygame.K_RETURN:
            srv = getattr(self, 'pending_server', {})
            ip = srv.get("host_ip", "")
            port = srv.get("port", 1337)
            pw = getattr(self, 'join_password_buffer', '')
            
            if ip:
                self.play_sfx("accept")
                if str(ip).startswith("relay:"):
                    room_id = ip.split(":")[1]
                    self.game.network.join_relay(room_id, pw)
                else:
                    self.game.network.join_game(f"{ip}:{port}", pw)
                self.state = "JOINING"
            
        elif key == pygame.K_BACKSPACE:
            if hasattr(self, 'join_password_buffer') and self.join_password_buffer:
                self.join_password_buffer = self.join_password_buffer[:-1]
                
        elif event.unicode.isprintable() and len(event.unicode) > 0:
            if not hasattr(self, 'join_password_buffer'):
                self.join_password_buffer = ""
            if len(self.join_password_buffer) < 16:
                self.join_password_buffer += event.unicode
