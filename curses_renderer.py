import curses
import time

class MockFont:
    def render(self, text, antialias, color):
        import pygame
        return pygame.Surface((1,1))
    def size(self, text):
        return (len(text)*10, 20)

class CursesRenderer:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        # ... (colors)
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_GREEN, -1)
        curses.init_pair(2, curses.COLOR_WHITE, -1)
        curses.init_pair(3, curses.COLOR_RED, -1)
        curses.init_pair(4, curses.COLOR_YELLOW, -1)
        curses.init_pair(5, curses.COLOR_BLUE, -1)
        
        # Dimensions
        self.rows, self.cols = stdscr.getmaxyx()
        self.ref_w = 1024
        self.ref_h = 768

    def update_dimensions(self):
        self.rows, self.cols = self.stdscr.getmaxyx()

    def map_coords(self, x, y):
        cx = int((x / self.ref_w) * self.cols)
        cy = int((y / self.ref_h) * self.rows)
        return cx, cy

    def draw_text(self, surface, text, x, y, color=None, font=None):
        # surface arg is ignored (it's stdscr)
        cx, cy = self.map_coords(x, y)
        if 0 <= cy < self.rows and 0 <= cx < self.cols:
            # Map RGB color to closest Pair? 
            # Simplified: Green mapped to pair 1, White to 2, etc.
            pair = 2
            if color:
                if color[1] > 200 and color[0] < 100: pair = 1 # Green
                elif color[0] > 200 and color[1] < 100: pair = 3 # Red
                elif color[0] > 200 and color[1] > 200 and color[2] < 100: pair = 4 # Yellow
                elif color[2] > 200: pair = 5 # Blues
                
            try:
                # Curses addstr can fail if writing to bottom-right corner
                self.stdscr.addstr(cy, cx, str(text), curses.color_pair(pair))
            except:
                pass

    def draw_lanes(self, surface, upscroll=False):
        # Draw vertical lines for lanes
        center_row = self.rows // 2
        center_col = self.cols // 2
        
        # Lane width in chars
        lane_w = 400 / self.ref_w * self.cols / 4
        start_col = center_col - (lane_w * 2)
        
        for i in range(5):
            x = int(start_col + i * lane_w)
            if 0 <= x < self.cols:
                for y in range(self.rows):
                    try: self.stdscr.addch(y, x, '|')
                    except: pass
                    
        # Hit Line (Top or Bottom)
        hit_row = int(self.rows * (0.15 if upscroll else 0.85))
        for x in range(int(start_col), int(start_col + lane_w * 4)):
             if 0 <= x < self.cols:
                 try: self.stdscr.addch(hit_row, x, '-')
                 except: pass

    def draw_notes(self, surface, notes, song_time, scroll_speed, upscroll=False):
        # Scale speed: pixels/sec -> rows/sec
        # A row is ~20 pixels height-wise visually? 
        row_factor = self.rows / self.ref_h
        speed_rows = scroll_speed * row_factor
        
        center_col = self.cols // 2
        lane_w = 400 / self.ref_w * self.cols / 4
        start_col = center_col - (lane_w * 2)
        
        hit_row = int(self.rows * (0.15 if upscroll else 0.85))

        for note in notes:
            if note.get('hit', False): continue
            
            dt = note['time'] - song_time
            if dt < -0.2 or dt > 2.0: continue
            
            # y offset in rows
            dy = int(dt * speed_rows)
            y = hit_row + dy if upscroll else hit_row - dy
            
            lane = note['lane']
            x = int(start_col + lane * lane_w + lane_w/2)
            
            if 0 <= y < self.rows and 0 <= x < self.cols:
                 char = "O"
                 try: self.stdscr.addstr(y, x-1, "( )", curses.color_pair(3 if lane in [0,3] else 5))
                 except: pass
    
    def draw_effects(self, surface):
        pass # simplified

    def clear(self):
        self.stdscr.clear()

    def present(self):
        self.stdscr.refresh()
