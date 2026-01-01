import pygame
import os
import sys
from core.config import *

class PygameRenderer:
    # Renamed from CursesRenderer to reflect V8 engine
    def __init__(self, ref_w=1024, ref_h=768):
        self.ref_w = ref_w
        self.ref_h = ref_h
        
        # Resource Helper
        def resource_path(relative_path):
            """ Get absolute path to resource, works for dev and for PyInstaller """
            if hasattr(sys, '_MEIPASS'):
                return os.path.join(sys._MEIPASS, relative_path)
            return os.path.join(os.path.abspath("."), relative_path)
        
        # Cross-platform font fallback order
        # Windows: Consolas, Courier New, Lucida Console
        # Linux: monospace, DejaVu Sans Mono
        # Mac: Monaco, Menlo
        FONT_FALLBACKS = [
            "consolas",      # Windows
            "couriernew",    # Windows  
            "lucidaconsole", # Windows
            "monospace",     # Linux
            "dejavusansmono",# Linux
            "monaco",        # Mac
            "menlo",         # Mac
            None             # pygame default
        ]
        
        def get_system_font(size, bold=True):
            """Get a monospace font that works on any platform"""
            for font_name in FONT_FALLBACKS:
                try:
                    font = pygame.font.SysFont(font_name, size, bold=bold)
                    if font:
                        return font
                except:
                    continue
            # Ultimate fallback - pygame's default font
            return pygame.font.Font(None, size)
        
        # Fonts - try bundled font first, then system fonts
        self.font_path = resource_path(os.path.join("assets", "font.ttf"))
        if os.path.exists(self.font_path):
            try:
                self.font = pygame.font.Font(self.font_path, 20)
                self.big_font = pygame.font.Font(self.font_path, 40)
                self.small_font = pygame.font.Font(self.font_path, 16)
                self.ascii_font = pygame.font.Font(self.font_path, 14)
            except:
                # Font file exists but failed to load
                self.font = get_system_font(20)
                self.big_font = get_system_font(40)
                self.small_font = get_system_font(16)
                self.ascii_font = get_system_font(14)
        else:
            # Use cross-platform system font fallback
            self.font = get_system_font(20)
            self.big_font = get_system_font(40)
            self.small_font = get_system_font(16)
            self.ascii_font = get_system_font(14)
             
        # Cache key states
        self.key_states = [False] * 4
        
        # Visual Effects
        self.effects = []
        
        # Post-processing state
        self.shake_offset = [0, 0]  # [x, y] shake offset
        self.shake_intensity = 0.0  # Current shake amount
        self.flash_alpha = 0  # Flash overlay alpha (0-255)
        self.flash_color = (255, 255, 255)  # Flash color
        
        # Camera State
        self.camera_zoom = 1.0
        self.camera_offset_x = 0
        self.camera_offset_y = 0
        self.target_zoom = 1.0
        self.target_offset_x = 0
        self.target_offset_y = 0
        
        # Glow State
        self.active_glow = None # (color, duration)
        
        # Font Cache for CJK/Localization
        self.fonts = {
            "default": self.font,
            "default": self.font,
            "big_default": self.big_font,
            "small": self.small_font,
            "ascii": self.ascii_font
        }
        self.last_lang = None

    def _get_localized_fonts(self):
        """Get appropriate fonts for current language"""
        lang = "EN"
        if hasattr(self, 'game') and self.game:
            lang = self.game.settings.get("language")
        
        if lang == self.last_lang:
            return self.fonts["current_font"], self.fonts["current_big_font"]
        
        self.last_lang = lang
        
        # Default fallback
        f = self.fonts["default"]
        bf = self.fonts["big_default"]
        
        if lang == "JP":
            # Try to find a CJK font
            cjk_candidates = ["notosanscjkjp", "notosansgothic", "notosanscjksc", "takaoexgothic", "msgothic"]
            all_fonts = pygame.font.get_fonts()
            
            for candidate in cjk_candidates:
                if candidate in all_fonts:
                    try:
                        f = pygame.font.SysFont(candidate, 20, bold=True)
                        bf = pygame.font.SysFont(candidate, 40, bold=True)
                        break
                    except: continue
        
        self.fonts["current_font"] = f
        self.fonts["current_big_font"] = bf
        return f, bf

    def get_screen_size(self):
        """Get current screen dimensions dynamically"""
        try:
            display_surface = pygame.display.get_surface()
            if display_surface:
                return display_surface.get_width(), display_surface.get_height()
        except:
            pass
        return self.ref_w, self.ref_h
    
    def get_screen_width(self):
        return self.get_screen_size()[0]
    
    def get_screen_height(self):
        return self.get_screen_size()[1]

    def update_dimensions(self):
        """Update reference dimensions to current window size"""
        w, h = self.get_screen_size()
        self.ref_w = w
        self.ref_h = h

    def clear(self):
        # Main loop handles fill
        pass

    def present(self):
        # Main loop handles flip
        pass

    def update_effects(self):
        # Update particles/text
        alive = []
        for e in self.effects:
            e['x'] += e.get('vx', 0)
            e['y'] += e.get('vy', 0)
            e['life'] -= 1
            if e['life'] > 0:
                alive.append(e)
        self.effects = alive
        
        # Update post-processing
        # Decay shake
        if self.shake_intensity > 0:
            import random
            self.shake_offset[0] = random.uniform(-self.shake_intensity, self.shake_intensity)
            self.shake_offset[1] = random.uniform(-self.shake_intensity, self.shake_intensity)
            self.shake_intensity *= 0.85  # Decay
            if self.shake_intensity < 0.5:
                self.shake_intensity = 0
                self.shake_offset = [0, 0]
        
        # Decay flash
        if self.flash_alpha > 0:
            self.flash_alpha = max(0, self.flash_alpha - 25)
            
        # Camera Interpolation
        self.camera_zoom += (self.target_zoom - self.camera_zoom) * 0.1
        self.camera_offset_x += (self.target_offset_x - self.camera_offset_x) * 0.1
        self.camera_offset_y += (self.target_offset_y - self.camera_offset_y) * 0.1
        
        # Decay Glow
        if self.active_glow:
            color, life = self.active_glow
            life -= 1
            if life <= 0:
                self.active_glow = None
            else:
                self.active_glow = (color, life)
    
    def trigger_shake(self, intensity=8.0):
        """Trigger screen shake effect"""
        self.shake_intensity = max(self.shake_intensity, intensity)
    
    def trigger_flash(self, color=(255, 255, 255), alpha=80):
        """Trigger screen flash effect"""
        self.flash_color = color
        self.flash_alpha = alpha

    def trigger_zoom(self, zoom, duration=1.0):
        self.target_zoom = zoom

    def trigger_pan(self, x, y):
        self.target_offset_x = x
        self.target_offset_y = y
        
    def trigger_glow(self, color, duration=30):
        self.active_glow = (color, duration)
    
    def apply_post_effects(self, surface):
        """Apply post-processing effects to the surface"""
        # Apply flash overlay
        if self.flash_alpha > 0:
            flash_surf = pygame.Surface((self.ref_w, self.ref_h))
            flash_surf.fill(self.flash_color)
            flash_surf.set_alpha(self.flash_alpha)
            surface.blit(flash_surf, (0, 0))
    
    def get_shake_offset(self):
        """Get current shake offset for rendering"""
        return self.shake_offset

    def draw_text(self, surface, text, x, y, color=(255, 255, 255), font=None):
        if not font:
            f, bf = self._get_localized_fonts()
            font = f
            # If someone passed font=renderer.big_font, we should probably handle it?
            # But usually they pass renderer.big_font directly.
            # Let's check for equality to our cached defaults.
            # Actually, better to just check if it's big_default.
            
        if font == self.fonts["big_default"]:
             _, bf = self._get_localized_fonts()
             font = bf
        elif font == self.fonts["ascii"]:
             pass # ASCII font stays same
             
        if not surface: return
        surf = font.render(str(text), False, color)
        surface.blit(surf, (x, y))

    def get_theme(self):
        try:
            name = self.game.settings.get("theme")
        except (AttributeError, Exception):
            name = "TERMINAL"
        
        # Start with base theme
        base = THEMES.get(name, THEMES["TERMINAL"])
        theme = dict(base)  # Make a copy to avoid modifying the original
        
        # Apply custom color overrides if set
        try:
            s = self.game.settings
            if s.get("custom_primary"):
                theme["primary"] = tuple(s.get("custom_primary"))
            if s.get("custom_secondary"):
                theme["secondary"] = tuple(s.get("custom_secondary"))
            if s.get("custom_bg"):
                theme["bg"] = tuple(s.get("custom_bg"))
            if s.get("custom_text"):
                theme["text"] = tuple(s.get("custom_text"))
        except (AttributeError, Exception):
            pass
        
        return theme

    # === Text Wrapping Helpers ===
    # === UI Helper Methods ===
    
    def wrap_text(self, text, max_chars=60):
        """Word-wrap text to max characters per line"""
        words = text.split(' ')
        lines = []
        current = ""
        for word in words:
            if len(current) + len(word) + 1 <= max_chars:
                current += (" " if current else "") + word
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines
    
    def draw_wrapped_text(self, surface, text, x, y, max_chars=60, color=None, line_height=25):
        current_line = ""
        
        for word in words:
            if len(current_line) + len(word) + 1 <= max_chars:
                current_line += (" " if current_line else "") + word
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines
    
    def draw_wrapped_text(self, surface, text, x, y, max_chars=60, color=None, 
                          line_height=25, font=None):
        """Draw text with automatic word wrapping. Returns final y position."""
        theme = self.get_theme()
        if color is None:
            color = theme["text"]
        lines = self.wrap_text(text, max_chars)
        for i, line in enumerate(lines):
            self.draw_text(surface, line, x, y + i * line_height, color)
        
        lines = self.wrap_text(text, max_chars)
        for i, line in enumerate(lines):
            self.draw_text(surface, line, x, y + i * line_height, color, font)
        
        return y + len(lines) * line_height
    
    def draw_panel(self, surface, x, y, w, h, title=None, color=None):
        """Draw a styled window panel with title bar"""
        theme = self.get_theme()
        bg_col = color if color else theme["bg"]
        
        # 1. Main Background (Semi-transparent dark fill for depth)
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        s.fill((*bg_col, 240)) # 240 alpha
        surface.blit(s, (x, y))
        
        # 2. Border
        pygame.draw.rect(surface, theme["grid"], (x, y, w, h), 2)
        
        # 3. Title Bar
        content_y = y
        if title:
            title_h = 32
            # Title bar bg
            pygame.draw.rect(surface, theme["grid"], (x, y, w, title_h))
            # Title text
            self.draw_text(surface, f" {title}", x + 5, y + 6, theme["text"])
            # Decoration line
            pygame.draw.line(surface, theme["primary"], (x, y + title_h), (x + w, y + title_h), 1)
            content_y += title_h
            
        return x, content_y # Return content start position

    def draw_styled_rect(self, surface, x, y, w, h, color, outline_color=None, thickness=1):
        """Draw a rect with optional alpha and outline"""
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        if len(color) == 3: color = (*color, 255)
        s.fill(color)
        surface.blit(s, (x, y))
        if outline_color:
            pygame.draw.rect(surface, outline_color, (x, y, w, h), thickness)

    def draw_centered_text(self, surface, text, center_x, y, color=None, font=None, shadow=True):
        """Draw text centered horizontally"""
        if not font: font = self.font
        if not color: color = (255, 255, 255)
        
        surf = font.render(str(text), False, color)
        w, h = surf.get_size()
        x = center_x - w // 2
        
        if shadow:
            s_surf = font.render(str(text), False, (0, 0, 0))
            surface.blit(s_surf, (x + 2, y + 2))
            
        surface.blit(surf, (x, y))
        return h

    def draw_button(self, surface, text, x, y, selected=False, width=200, height=40, disabled=False):
        """Draw a styled button"""
        theme = self.get_theme()
        
        rect = pygame.Rect(x, y, width, height)
        
        # Disabled state
        if disabled:
            pygame.draw.rect(surface, (30, 30, 30), rect)
            pygame.draw.rect(surface, (50, 50, 50), rect, 1)
            self.draw_text(surface, text, x + 15, y + 10, (100, 100, 100))
            return height + 5
        
        # Dynamic pulse if selected
        pulse = 0
        if selected:
            pulse = (pygame.time.get_ticks() % 1000) / 1000.0 # 0.0 to 1.0
        
        # Background
        if selected:
            # Gradient-ish or brighter bg
            bg_col = theme["grid"]
            # Add pulse to bg
            bg_col = (
                min(255, bg_col[0] + int(20 * pulse)),
                min(255, bg_col[1] + int(20 * pulse)),
                min(255, bg_col[2] + int(20 * pulse))
            )
            pygame.draw.rect(surface, bg_col, rect)
            # Active Border
            pygame.draw.rect(surface, theme["primary"], rect, 2)
            
            # Indicator triangle
            self.draw_text(surface, "▶", x + 10, y + 10, theme["primary"])
            text_x = x + 35
            text_col = theme["primary"]
        else:
            pygame.draw.rect(surface, theme["bg"], rect)
            pygame.draw.rect(surface, tuple(max(0, c - 50) for c in theme["grid"]), rect, 1)
            text_x = x + 15
            text_col = theme["text"]
            
        # Draw Text (Clipped)
        original_clip = surface.get_clip()
        surface.set_clip(rect)
        self.draw_text(surface, text, text_x, y + 10, text_col)
        surface.set_clip(original_clip)
        
        return height + 5 # Return height + margin
    
    def draw_input_field(self, surface, label, value, x, y, width=300, focused=False):
        """Draw a text input field"""
        theme = self.get_theme()
        
        # Label
        self.draw_text(surface, label, x, y, theme["secondary"])
        
        # Box geometry
        box_y = y + 25
        box_h = 30
        rect = pygame.Rect(x, box_y, width, box_h)
        
        # Draw Box
        border = theme["primary"] if focused else theme["grid"]
        pygame.draw.rect(surface, (20, 20, 20), rect)
        pygame.draw.rect(surface, border, rect, 2)
        
        # Draw Text (Clipped)
        original_clip = surface.get_clip()
        # Clip to inner rect (padding 2px for border)
        inner_rect = pygame.Rect(x + 2, box_y + 2, width - 4, box_h - 4)
        surface.set_clip(inner_rect)
        
        display = value + ("_" if focused else "")
        
        # Dynamic Vertical Centering
        font = self.fonts["default"]
        fh = font.get_height()
        text_y = box_y + (box_h - fh) // 2
        
        # Ensure we don't draw too high if font is weird
        text_y = max(text_y, box_y + 2)
        
        self.draw_text(surface, display, x + 8, text_y, theme["text"])
        
        surface.set_clip(original_clip)
        
        return 60

    def _transform_point(self, x, y):
        """Apply camera zoom and offset to a point"""
        cx, cy = self.ref_w // 2, self.ref_h // 2
        
        # Offset
        x += self.camera_offset_x + self.shake_offset[0]
        y += self.camera_offset_y + self.shake_offset[1]
        
        # Zoom relative to center
        dx = x - cx
        dy = y - cy
        
        x = cx + dx * self.camera_zoom
        y = cy + dy * self.camera_zoom
        
        return int(x), int(y)

    def draw_lanes(self, surface, upscroll=False, pulse=0.0):
        theme = self.get_theme()
        
        # Draw 4 Lanes
        center_x = self.ref_w // 2
        lane_w = 100 # Pixels
        start_x = center_x - (lane_w * 2)
        
        # Dynamic Background Pulse
        bg_col = list(theme["bg"])
        if pulse > 0:
            bg_col[1] = min(255, int(bg_col[1] + 20 * pulse))
        
        # Apply Glow if active
        if self.active_glow:
            glow_col, _ = self.active_glow
            # Blend glow color with bg
            bg_col = [min(255, c + gc*0.2) for c, gc in zip(bg_col, glow_col)]
            
        # We need to draw a large background to cover shakes/zooms
        # Transform corners
        tl = self._transform_point(start_x, 0)
        tr = self._transform_point(start_x + lane_w * 4, 0)
        bl = self._transform_point(start_x, self.ref_h)
        br = self._transform_point(start_x + lane_w * 4, self.ref_h)
        
        pygame.draw.polygon(surface, bg_col, [tl, tr, br, bl])
        
        # Lane Dividers
        grid_col = theme["grid"]
        for i in range(5):
            x = start_x + i * lane_w
            pt1 = self._transform_point(x, 0)
            pt2 = self._transform_point(x, self.ref_h)
            pygame.draw.line(surface, grid_col, pt1, pt2, 2)

            
        # Receptor Line
        hit_y = int(self.ref_h * (0.15 if upscroll else 0.85))
        thick = 4 + int(2 * pulse)
        # Receptor color usually primary
        pygame.draw.line(surface, theme["primary"], (start_x, hit_y), (start_x + lane_w * 4, hit_y), thick)
        
        # Key receptors
        note_shape = self.game.settings.get("note_shape") or "BAR"
        
        for i in range(4):
            x = start_x + i * lane_w
            
            if note_shape == "ARROW":
                # Draw simple outline arrow
                cx, cy = x + lane_w//2, hit_y
                size = 40 # Increased from 28 to match BAR
                outline_col = theme["primary"] if self.key_states[i] else grid_col
                
                points = []
                if i == 0: points = [(-size, 0), (size, -size), (size, size)]
                elif i == 1: points = [(0, size), (-size, -size), (size, -size)]
                elif i == 2: points = [(0, -size), (-size, size), (size, size)]
                elif i == 3: points = [(size, 0), (-size, -size), (-size, size)]
                
                poly = [(cx + px, cy + py) for px, py in points]
                width = 0 if self.key_states[i] else 2
                pygame.draw.polygon(surface, outline_col, poly, width)
                
            elif note_shape == "CIRCLE":
                cx, cy = x + lane_w//2, hit_y
                radius = 42 # Increased from 24 (Diameter 84)
                outline_col = theme["primary"] if self.key_states[i] else grid_col
                width = 0 if self.key_states[i] else 2
                pygame.draw.circle(surface, outline_col, (cx, cy), radius, width)
                
            else:
                # BAR Default
                h = 24
                rect = pygame.Rect(x + 10, hit_y - h//2, lane_w - 20, h)
                if self.key_states[i]:
                    pygame.draw.rect(surface, theme["primary"], rect)
                else:
                    pygame.draw.rect(surface, grid_col, rect, 2)

    def draw_progress(self, surface, current, total):
        theme = self.get_theme()
        if total <= 0: return
        pct = min(1.0, current / total)
        
        h = 10
        y = self.ref_h - h if not False else 0 # Bottom usually
        
        # Background
        pygame.draw.rect(surface, theme["bg"], (0, y, self.ref_w, h))
        # Fill
        pygame.draw.rect(surface, theme["primary"], (0, y, int(self.ref_w * pct), h))

    # (draw_notes kept mostly same, as it uses Settings for specific colors)
    # Actually wait, draw_notes uses note_col_1. 
    # Maybe switching theme should UPDATE note_col_1 in settings?
    # I'll handle that in SettingsScene.

    def draw_notes(self, surface, notes, song_time, scroll_speed, upscroll=False):
        theme = self.get_theme()
        
        center_x = self.ref_w // 2
        lane_w = 100
        start_x = center_x - (lane_w * 2)
        hit_y = int(self.ref_h * (0.15 if upscroll else 0.85))
        
        c1 = self.game.settings.get("note_col_1")
        c2 = self.game.settings.get("note_col_2")
        note_shape = self.game.settings.get("note_shape") or "BAR"
        show_ends = self.game.settings.get("show_hold_ends")
        
        max_dist = self.ref_h + 100
        
        for note in notes:
            t_diff = note['time'] - song_time
            length = note.get('length', 0)
            dist = t_diff * scroll_speed
            
            if upscroll:
                y = hit_y + dist
            else:
                y = hit_y - dist

            # Culling logic:
            # If hit, we still draw if it's a hold note and hasn't finished
            if note.get('hit'):
                if length > 0:
                    # If it's a hold, check if tail hasn't passed hit_y
                    if upscroll:
                        # In upscroll, tail is at y_tail = y + tail_pixels
                        # It passes when y_tail < hit_y
                        if (y + (length * scroll_speed)) < hit_y: continue
                    else:
                        # In downscroll, tail is at y_tail = y - tail_pixels
                        # It passes when y_tail > hit_y
                        if (y - (length * scroll_speed)) > hit_y: continue
                else:
                    continue # Regular note hit, disappear
            
            # For culling, use end time if it's a hold note
            end_t_diff = t_diff + length
            if end_t_diff < -0.3: continue # Only skip if the TAIL has passed
            
            if dist > max_dist: continue
                
            lane = note['lane']
            x = start_x + lane * lane_w
            cx = x + lane_w // 2
            
            # Apply Camera Transform
            tx, ty = self._transform_point(x, y)
            tcx, _ = self._transform_point(cx, y)
            
            # Scale dimensions
            scaled_w = int(lane_w * self.camera_zoom)
            scaled_h = int(30 * self.camera_zoom)
            
            color = c1 if lane in [1, 2] else c2
            if self.active_glow:
                 gc, _ = self.active_glow
                 color = [min(255, c + g*0.5) for c, g in zip(color, gc)]
                 
            dark_color = tuple(max(0, c - 60) for c in color)

            
            # Draw hold note body
            if length > 0:
                tail_pixels = int(length * scroll_speed)
                if upscroll:
                    tail_end = y + tail_pixels # Tail follows BELOW head
                else:
                    tail_end = y - tail_pixels # Tail follows ABOVE head
                
                # Determine body rect points
                if upscroll:
                    top_y = y
                    bottom_y = tail_end
                else:
                    top_y = tail_end
                    bottom_y = y
                
                 # Styled Body Rendering
                # Always BAR style
                b_w = lane_w - 40
                body_rect = pygame.Rect(cx - b_w//2, int(min(y, tail_end)), b_w, int(abs(y - tail_end)))
                pygame.draw.rect(surface, dark_color, body_rect)
                pygame.draw.rect(surface, color, body_rect, 2)
                pygame.draw.line(surface, color, (cx, int(y)), (cx, int(tail_end)), 3)
                
                # End marker (TAIL) styling
                if show_ends:
                    # Draw the same shape as the head at the tail position
                    if note_shape == "ARROW":
                        self._draw_arrow_note(surface, x, int(tail_end), lane_w, color, lane, False)
                    elif note_shape == "CIRCLE":
                        self._draw_circle_note(surface, x, int(tail_end), lane_w, color, False)
                    else:
                        # BAR style tail
                        t_h = 24
                        t_rect = pygame.Rect(x + 10, int(tail_end) - t_h//2, lane_w - 20, t_h)
                        pygame.draw.rect(surface, dark_color, t_rect)
                        pygame.draw.rect(surface, color, t_rect, 2)
                        # Center line
                        pygame.draw.line(surface, (0, 0, 0), (x+5, int(tail_end)), (x+lane_w-5, int(tail_end)), 2)
            
            # Draw note HEAD 
            # If hit_y is within the hold duration, stick the head to hit_y
            head_y = y
            is_active_hold = (length > 0 and t_diff <= 0 and end_t_diff > 0)
            if is_active_hold:
                head_y = hit_y
            
            # Draw the head (unless it's a hold that already fully passed hit_y)
            show_head = True
            if note.get('hit') and not is_active_hold:
                 show_head = False
            
            if show_head:
                if note_shape == "ARROW":
                    self._draw_arrow_note(surface, x, int(head_y), lane_w, color, lane, length > 0)
                elif note_shape == "CIRCLE":
                    self._draw_circle_note(surface, x, int(head_y), lane_w, color, length > 0)
                else:
                    self._draw_bar_note(surface, x, int(head_y), lane_w, color, length > 0)
    
    def _draw_bar_note(self, surface, x, y, lane_w, color, is_long=False):
        """Draw bar-style note (8-bit styled)"""
        rect = pygame.Rect(x + 5, y - 15, lane_w - 10, 30)
        pygame.draw.rect(surface, color, rect)
        pygame.draw.rect(surface, (255, 255, 255), rect, 2)
        # Center line
        pygame.draw.line(surface, (0, 0, 0), (x+5, y), (x+lane_w-5, y), 2)
        if is_long:
            pygame.draw.rect(surface, (255, 255, 255), 
                pygame.Rect(x + 30, y - 5, lane_w - 60, 10))
                
    def _draw_arrow_note(self, surface, x, y, lane_w, color, lane, is_long=False):
        """Draw arrow note pointing in lane direction"""
        cx = x + lane_w // 2
        cy = y
        size = 40 # Increased from 25
        
        # Directions: 0=Left, 1=Down, 2=Up, 3=Right
        # Points relative to center (0,0)
        points = []
        if lane == 0: # Left
            points = [(-size, 0), (size, -size), (size, size)]
        elif lane == 1: # Down
            points = [(0, size), (-size, -size), (size, -size)]
        elif lane == 2: # Up
            points = [(0, -size), (-size, size), (size, size)]
        elif lane == 3: # Right
            points = [(size, 0), (-size, -size), (-size, size)]
            
        # Transform to screen coords
        poly = [(cx + px, cy + py) for px, py in points]
        
        pygame.draw.polygon(surface, color, poly)
        pygame.draw.polygon(surface, (255, 255, 255), poly, 2)
        
    def _draw_circle_note(self, surface, x, y, lane_w, color, is_long=False):
        """Draw circle style note"""
        cx = x + lane_w // 2
        radius = 42 # Increased from 20
        pygame.draw.circle(surface, color, (cx, int(y)), radius)
        pygame.draw.circle(surface, (255, 255, 255), (cx, int(y)), radius, 2)
        if is_long:
            pygame.draw.circle(surface, (255, 255, 255), (cx, int(y)), radius//2)
    
    def draw_effects(self, surface):
        # Effects have their own color embedded
        for e in self.effects:
            if e['type'] == 'text':
                # Float calculation logic in update_effects, we just draw x,y
                # Alpha fade
                # Pygame font rendering with alpha is tricky without intermediate surface
                # Simple approach: standard blit.
                self.draw_text(surface, e['text'], int(e['x']), int(e['y']), e['color'])
            
            elif e['type'] == 'particle':
                 # Draw small rects
                 r = pygame.Rect(int(e['x']), int(e['y']), e['size'], e['size'])
                 pygame.draw.rect(surface, e['color'], r)

    def add_hit_effect(self, text, lane, upscroll=False, color=None):
        theme = self.get_theme()
        
        # Lane X calc:
        center_x = self.ref_w // 2
        lane_w = 100
        start_x = center_x - (lane_w * 2)
        x = start_x + lane * lane_w + lane_w // 2
        
        # Hit Line Y
        hit_y = int(self.ref_h * (0.15 if upscroll else 0.85))
        y = hit_y
        
        # Color Logic
        col = color if color else theme["primary"]
        if text == "MISS": col = theme["error"]
        
        # Add Text Effect
        # For text, we center it.
        # estimate width
        txt_w = len(text) * 15 
        
        self.effects.append({
            'type': 'text',
            'x': x - txt_w // 2,
            'y': y - 40 if not upscroll else y + 20,
            'vx': 0,
            'vy': -1 if not upscroll else 1, # Float away from receptor
            'life': 40,
            'text': text,
            'color': col
        })
        
        # Add Pixel Explosion
        import random
        count = 8 if text == "PERFECT" else 4
        if text == "MISS": count = 2
        
        for _ in range(count):
            size = random.randint(4, 10)
            vx = random.uniform(-6, 6) 
            # Particles should explode OUTWARDS from hit line.
            # If downscroll (hit bottom), they should fly UP (-vy) mostly?
            # Or just fountain? Fountain is nice.
            vy = random.uniform(-10, -2) if not upscroll else random.uniform(2, 10)
            
            self.effects.append({
                'type': 'particle',
                'x': x + random.randint(-20, 20),
                'y': y,
                'vx': vx,
                'vy': vy,
                'life': random.randint(20, 40),
                'color': col,
                'size': size
            })
