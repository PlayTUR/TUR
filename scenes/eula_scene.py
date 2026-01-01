import pygame
import sys
from core.scene_manager import Scene
from scenes.menu_scenes import TitleScene

class EULAScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.scrolle_y = 0
        self.scroll_speed = 40
        
        self.title = "SYSTEM NOTIFICATION: EULA"
        
        self.lines = [
            "END USER LICENSE AGREEMENT (EULA)",
            "=================================",
            "Last Updated: December 31, 2025",
            "",
            "IMPORTANT -- READ CAREFULLY: This End User License Agreement",
            "('Agreement') is a legal agreement between you (either an",
            "individual or a single entity) and the developers of",
            "TUR (The Unnamed Rhythm Game) ('Licensor').",
            "",
            "By installing, copying, or otherwise using the Software,",
            "you agree to be bound by the terms of this Agreement.",
            "If you do not agree to the terms of this Agreement, do not",
            "install or use the Software.",
            "",
            "1. LICENSE GRANT",
            "   Subject to the terms of this Agreement, Licensor grants you",
            "   a limited, non-exclusive, non-transferable license to",
            "   download, install, and use the Software for your personal,",
            "   non-commercial use.",
            "",
            "2. RESTRICTIONS",
            "   You agree not to, and you will not permit others to:",
            "   a) License, sell, rent, lease, transfer, assign, distribute,",
            "      host, or otherwise commercially exploit the Software;",
            "   b) Modify, translate, adapt, merge, make derivative works",
            "      of, disassemble, decompile, reverse compile or reverse",
            "      engineer any part of the Software, except to the extent",
            "      the foregoing restrictions are expressly prohibited by",
            "      applicable law;",
            "   c) Remove or destroy any copyright notices or other",
            "      proprietary markings contained on or in the Software.",
            "",
            "3. ONLINE CONDUCT & FAIR PLAY",
            "   The Software includes online multiplayer features.",
            "   To ensure a fair environment, you agree explicitly that:",
            "   a) AUTOMATION: The use of macros, bots, auto-clickers,",
            "      hardware assistance, or any automation software is",
            "      strictly prohibited in all online modes.",
            "   b) INTEGRITY: You will not intercept, emulate, or redirect",
            "      communication protocols used by Licensor.",
            "   c) BEHAVIOR: You will not harass, threaten, or abuse other",
            "      users.",
            "",
            "4. SECURITY & ENFORCEMENT (ZERO TOLERANCE)",
            "   WARNING: The server actively monitors for anomalies.",
            "   Any attempt to hack, tamper, injection, or submission",
            "   of falsified data will result in an IMMEDIATE,",
            "   PERMANENT ACCOUNT BAN.",
            "",
            "   CRITICAL SECURITY WARNING:",
            "   We will NOT hesitate to SUE or involve LAW ENFORCEMENT",
            "   against anyone attempting to DDoS, exploit, or damage",
            "   server infrastructure in any way. We treat infrastructure",
            "   attacks as criminal offenses.",
            "   We WILL send the police to your door.",
            "",
            "5. OWNERSHIP",
            "   The Software is licensed, not sold. Licensor retains all",
            "   ownership rights, title, and interest in and to the",
            "   Software, including all intellectual property rights.",
            "",
            "6. DATA COLLECTION & PRIVACY",
            "   By using the Software, you consent to the collection of",
            "   technical data and related information, including but",
            "   not limited to technical information about your device,",
            "   system and application software, and peripherals.",
            "   This data, including Account Identifiers and gameplay",
            "   telemetry, is collected solely to facilitate software",
            "   updates, product support, and for anti-cheat enforcement.",
            "",
            "7. TERMINATION",
            "   This Agreement is effective until terminated. Your rights",
            "   under this Agreement will terminate automatically without",
            "   notice from Licensor if you fail to comply with any term(s)",
            "   of this Agreement. Upon termination, you shall cease all",
            "   use of the Software and destroy all copies, full or partial,",
            "   of the Software.",
            "",
            "8. DISCLAIMER OF WARRANTIES",
            "   THE SOFTWARE IS PROVIDED 'AS IS', WITH ALL FAULTS AND",
            "   WITHOUT WARRANTY OF ANY KIND. LICENSOR HEREBY DISCLAIMS",
            "   ALL WARRANTIES AND CONDITIONS WITH RESPECT TO THE SOFTWARE,",
            "   EXPRESS, IMPLIED OR STATUTORY.",
            "",
            "9. LIMITATION OF LIABILITY",
            "   IN NO EVENT SHALL LICENSOR BE LIABLE FOR ANY INCIDENTAL,",
            "   SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES WHATSOEVER,",
            "   INCLUDING, WITHOUT LIMITATION, DAMAGES FOR LOSS OF PROFITS,",
            "   LOSS OF DATA, OR KEYBOARD DESTRUCTION DUE TO INTENSE",
            "   RHYTHM GAMEPLAY.",
            "",
            "10. GOVERNING LAW",
            "    This Agreement shall be governed by the laws of the",
            "    Internet and Common Sense, excluding its conflicts of",
            "    law rules.",
            "",
            "=================================",
            "END OF DOCUMENT",
            "",
            "DO YOU ACCEPT THESE TERMS?"
        ]
        
        self.has_read_bottom = False
        
        # Calculate content height
        # Font size ~30px? usually renderer uses standard font
        # We need to render once to know height, or just estimate.
    
    def on_enter(self, params=None):
        self.game.discord.update("Reading EULA", "Reviewing Terms...")
        self.scroll_y = 0
        self.has_read_bottom = False

    def handle_input(self, event):
        theme = self.game.renderer.get_theme()
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.scroll_y = max(0, self.scroll_y - self.scroll_speed)
                self.play_sfx("blip")
            elif event.key == pygame.K_DOWN:
                self.scroll_y += self.scroll_speed # Limit check in draw or update
                self.play_sfx("blip")
            
            # Acceptance logic
            if self.has_read_bottom:
                if event.key == pygame.K_y:
                    self.play_sfx("accept")
                    self.game.settings.set("eula_accepted", True)
                    
                    if not self.game.settings.get("setup_complete"):
                        from scenes.setup_scene import SetupScene
                        self.manager.switch_to(SetupScene)
                    else:
                        from scenes.menu_scenes import TitleScene
                        self.manager.switch_to(TitleScene)
                        self.game.play_menu_bgm()
                elif event.key == pygame.K_n or event.key == pygame.K_ESCAPE:
                    self.play_sfx("shutdown")
                    pygame.quit()
                    sys.exit()

    def update(self):
        pass

    def draw(self, surface):
        theme = self.game.renderer.get_theme()
        surface.fill(theme["bg"])
        
        sw = surface.get_width()
        sh = surface.get_height()
        
        # Panel Background
        r = self.game.renderer
        margin_x = 100
        margin_y = 80
        panel_w = sw - 2 * margin_x
        panel_h = sh - 2 * margin_y
        
        # Draw Border
        pygame.draw.rect(surface, theme["text"], (margin_x - 2, margin_y - 2, panel_w + 4, panel_h + 4), 2)
        
        # Header
        r.draw_text(surface, self.title, margin_x, margin_y - 40, theme["primary"], r.big_font)
        
        # Clip area for text
        clip_rect = pygame.Rect(margin_x, margin_y, panel_w, panel_h)
        surface.set_clip(clip_rect)
        
        # Render Lines
        start_y = margin_y + 20 - self.scroll_y
        line_height = 30
        
        max_y = 0
        
        for i, line in enumerate(self.lines):
            y = start_y + i * line_height
            col = theme["text"]
            
            # Highlight specific lines
            if "WARNING" in line or "BAN" in line or "LEGAL" in line or "SUE" in line or "POLICE" in line:
                col = theme["error"]
            elif "DO YOU ACCEPT" in line:
                col = theme["primary"]
                
            if y + line_height > margin_y and y < margin_y + panel_h:
                r.draw_text(surface, line, margin_x + 20, y, col)
            
            max_y = y
            
        surface.set_clip(None)
        
        # Content Height logic
        content_height = len(self.lines) * line_height + 40
        max_scroll = max(0, content_height - panel_h)
        
        # Clamp scroll
        if self.scroll_y > max_scroll:
            self.scroll_y = max_scroll
            
        # Check if bottom reached (allow some margin of error)
        if self.scroll_y >= max_scroll - 10:
            self.has_read_bottom = True
            
        # Draw Scrollbar
        if max_scroll > 0:
            sb_x = margin_x + panel_w - 20
            sb_y = margin_y
            sb_h = panel_h
            
            # Track
            pygame.draw.rect(surface, (30, 30, 30), (sb_x, sb_y, 10, sb_h))
            
            # Thumb
            thumb_pct = panel_h / content_height
            thumb_h = max(20, int(panel_h * thumb_pct))
            scroll_pct = self.scroll_y / max_scroll if max_scroll else 0
            thumb_y = sb_y + int((sb_h - thumb_h) * scroll_pct)
            
            pygame.draw.rect(surface, theme["secondary"], (sb_x, thumb_y, 10, thumb_h))

        # Bottom Instructions
        if self.has_read_bottom:
            msg = "[Y] ACCEPT (LAUNCH SYSTEM)    [N] DECLINE (SHUTDOWN)"
            col = theme["secondary"]
            
            # blink effect
            import time
            if int(time.time() * 2) % 2 == 0:
                col = theme["primary"]
                
            text_w = r.font.size(msg)[0]
            r.draw_text(surface, msg, (sw - text_w)//2, sh - 60, col)
        else:
            msg = "[ARROW KEYS] SCROLL TO BOTTOM TO PROCEED"
            text_w = r.font.size(msg)[0]
            r.draw_text(surface, msg, (sw - text_w)//2, sh - 60, (100, 100, 100))
