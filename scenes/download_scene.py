"""
Download Scene - Song Downloader UI
Download songs from URLs with progress tracking.
"""

import pygame
from core.scene_manager import Scene
from core.config import *
from core.song_downloader import SongDownloader


class DownloadScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.downloader = SongDownloader("songs")
        self.url_buffer = ""
        self.input_focused = True
        self.blink_timer = 0
        self.message = ""
        self.message_color = (150, 150, 150)
        
        # Sample URLs
        self.samples = [
            ("Free Music Archive", "https://example.com/song.mp3"),
        ]
    
    def on_enter(self, params=None):
        self.url_buffer = ""
        self.message = "Enter a direct URL to an audio file (.mp3, .wav, .ogg)"
        self.message_color = (150, 150, 150)

    def update(self):
        self.blink_timer = (self.blink_timer + 1) % 60
        
        # Check download status
        if self.downloader.downloading:
            if self.downloader.download_total > 0:
                pct = int(100 * self.downloader.download_progress / self.downloader.download_total)
                self.message = f"Downloading... {pct}%"
            else:
                self.message = "Downloading..."
            self.message_color = (100, 200, 255)
        elif self.downloader.download_error:
            self.message = f"Error: {self.downloader.download_error[:50]}"
            self.message_color = (255, 100, 100)
        elif self.downloader.download_filename and not self.downloader.downloading:
            self.message = f"Downloaded: {self.downloader.download_filename}"
            self.message_color = (100, 255, 100)

    def draw(self, surface):
        r = self.game.renderer
        theme = r.get_theme()
        
        # 1. Animated Grid Background
        t = pygame.time.get_ticks()
        surface.fill(theme["bg"])
        grid_offset_y = (t * 0.1) % 40
        grid_col = theme["grid"]
        
        for y in range(0, SCREEN_HEIGHT + 40, 40):
            line_y = y + grid_offset_y - 40
            pygame.draw.line(surface, grid_col, (0, line_y), (SCREEN_WIDTH, line_y))
        for x in range(0, SCREEN_WIDTH, 40):
            pygame.draw.line(surface, grid_col, (x, 0), (x, SCREEN_HEIGHT))
        
        # Header (Standardized position)
        r.draw_text(surface, "◉ SONG DOWNLOADER ◉", 50, 40, theme["primary"], r.big_font)
        
        # URL Input panel (Standardized sizing)
        r.draw_panel(surface, 50, 100, 920, 150, "ENTER_URL")
        r.draw_text(surface, "Direct Audio URL:", 70, 130, theme["secondary"])
        
        # Input field
        border_color = theme["primary"] if self.input_focused else theme["grid"]
        pygame.draw.rect(surface, (20, 25, 30), (70, 160, 880, 40))
        pygame.draw.rect(surface, border_color, (70, 160, 880, 40), 2)
        
        display_url = self.url_buffer
        if len(display_url) > 85:
            display_url = "..." + display_url[-82:]
        cursor = "_" if self.blink_timer < 30 else ""
        r.draw_text(surface, display_url + cursor, 80, 170, theme["text"])
        
        r.draw_text(surface, "[ENTER] Download  [CTRL+V] Paste  [ESC] Back", 70, 215, (80, 80, 80))
        
        # Progress/Status panel (Standardized sizing)
        r.draw_panel(surface, 50, 280, 920, 100, "STATUS")
        
        # Show status from downloader
        if self.downloader.downloading:
            self.message = self.downloader.status_text or "Downloading..."
            self.message_color = (100, 200, 255)
        elif self.downloader.download_error:
            self.message = f"Error: {self.downloader.download_error}"
            self.message_color = (255, 100, 100)
        elif self.downloader.download_filename:
            self.message = f"Done! Press F5 in Song Select to refresh."
            self.message_color = (100, 255, 100)
        
        r.draw_text(surface, self.message, 70, 320, self.message_color)
        
        # Progress bar
        if self.downloader.downloading:
            pct = self.downloader.download_progress / 100
            pygame.draw.rect(surface, theme["grid"], (70, 350, 880, 15))
            pygame.draw.rect(surface, theme["primary"], (70, 350, int(880 * pct), 15))
        
        # Info panel (Standardized sizing)
        r.draw_panel(surface, 50, 410, 920, 220, "INFORMATION")
        
        info = [
            "◉ Paste YouTube, SoundCloud, or other URLs",
            "◉ Uses yt-dlp (install: pip install yt-dlp)",
            "◉ Auto-converts to MP3 and saves to 'songs' folder",
            "◉ Beatmaps are auto-generated on first play",
            "◉ Use Ctrl+V to paste from clipboard",
            "◉ REMINDER: Press F5 in Song Select to see new songs!"
        ]
        
        y = 445
        for line in info:
            r.draw_text(surface, line, 70, y, (120, 120, 120))
            y += 30
        
        # Bottom hint (Standardized)
        r.draw_text(surface, "[ENTER] Start Download  [ESC] Back to Song Select", 50, 680, (80, 80, 80))

    def handle_input(self, event):
        if event.type != pygame.KEYDOWN:
            return
        
        if event.key == pygame.K_ESCAPE:
            self.play_sfx("back")
            from scenes.menu_scenes import SongSelectScene
            self.game.scene_manager.switch_to(SongSelectScene)
        
        elif event.key == pygame.K_RETURN:
            if self.url_buffer and not self.downloader.downloading:
                self.play_sfx("accept")
                
                # Split buffer into multiple URLs if present
                urls = [u.strip() for u in self.url_buffer.replace(',', '\n').split('\n') if u.strip()]
                
                if len(urls) > 1:
                    self.downloader.download_batch(urls)
                    self.message = f"Starting batch download of {len(urls)} songs..."
                else:
                    url = urls[0]
                    # Try to extract filename from URL
                    filename = None
                    if "/" in url:
                        potential = url.split("/")[-1].split("?")[0]
                        if "." in potential:
                            filename = potential
                    self.downloader.download_from_url(url, filename)
                    self.message = "Starting download..."
                
                self.message_color = (255, 200, 50)
        
        elif event.key == pygame.K_BACKSPACE:
            self.url_buffer = self.url_buffer[:-1]
        
        elif event.key == pygame.K_v and (event.mod & (pygame.KMOD_CTRL | pygame.KMOD_META)):
            # Try multiple clipboard methods
            text = ""
            
            # Method 1: Centralized helper (subprocess-based)
            try:
                from core.utils import get_clipboard
                text = get_clipboard()
            except:
                pass
            
            # Method 2: pygame.scrap fallback
            if not text:
                try:
                    pygame.scrap.init()
                    clipboard_data = pygame.scrap.get(pygame.SCRAP_TEXT)
                    if clipboard_data:
                        text = clipboard_data.decode('utf-8', errors='ignore').strip('\x00')
                except:
                    pass
            
            if text:
                self.url_buffer += text
                self.message = f"Pasted {len(text)} characters"
                self.message_color = (100, 200, 255)
        
        elif event.unicode.isprintable() and len(event.unicode) == 1:
            if len(self.url_buffer) < 500:
                self.url_buffer += event.unicode
