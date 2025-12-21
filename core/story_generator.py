import random
import os
import json
from core.music_generator import MusicGenerator

class StoryGenerator:
    def __init__(self):
        # ... (Plots and Arts kept same)
        self.plots = [
            "Intercept encrypted signal.",
            "Breach the mainframe.",
            "Defend the datastream.",
            "Neutralize the virus.",
            "Upload the payload."
        ]
        
        self.arts = [
            [
                "   .---.",
                "  /     \\",
                " |  (O)  |",
                "  \\     /",
                "   `---`"
            ],
            [
                " [DATA]",
                " 010101",
                " 101010"
            ],
            [
                "  /\\_/\\",
                " ( o.o )",
                "  > ^ <"
            ],
            [
                " .--.",
                " |__| .-------.",
                " |=.| |.-----.|",
                " |--| ||     ||",
                " |  | |'-----'|",
                " '  ' '-------'"
            ]
        ]
        
    def generate_campaign(self, song_dir="songs"):
        """
        Generates a sequence of levels (Campaign).
        """
        # Ensure songs exist in story_music folder
        story_dir = "story_music"
        gen = MusicGenerator()
        new_songs = gen.generate_all(story_dir)
        
        # Find available songs
        songs = []
        if os.path.exists(story_dir):
            songs = [os.path.join(story_dir, f) for f in os.listdir(story_dir) if f.lower().endswith(('.mp3', '.wav', '.ogg'))]
            # Prefer generated ones for story order?
            # Sort to put story_intro first, then action, then boss
            
        # Sort logic: intro -> action -> boss -> others
        # Now using full paths, so we check path basename (ignoring extension)
        story_order = ["story_intro", "story_action", "story_boss"]
        sorted_songs = []
        
        # Create a map for easier sorting: Stem -> List of full paths (in case of dupes?)
        # Let's assume one file per stem.
        song_map = {}
        rest = []
        
        for p in songs:
             base = os.path.basename(p)
             stem = os.path.splitext(base)[0]
             if stem in story_order:
                 song_map[stem] = p
             else:
                 rest.append(p)
        
        for key in story_order:
            if key in song_map:
                sorted_songs.append(song_map[key])
                
        sorted_songs.extend(rest) 
        songs = sorted_songs
        
        if not songs:
            songs = [os.path.join(story_dir, "story_intro.wav")] # Fallback
            
        campaign = {
            "title": f"OPERATION {random.randint(100, 999)}",
            "chapters": []
        }
        
        # Create Chapters
        num_chapters = min(len(songs), 5)
        
        for i in range(num_chapters):
            song = songs[i]
            diff = ["EASY", "MEDIUM", "HARD", "EXTREME"][min(i, 3)] 
            
            plot = random.choice(self.plots)
            art = random.choice(self.arts)
            
            chapter = {
                "id": i + 1,
                "title": f"SEQUENCE {i+1}",
                "text": f"OBJECTIVE: {plot} AUTHORIZATION ALPHA.",
                "song": song,
                "difficulty": diff,
                "mode": "story",
                "art": art
            }
            campaign["chapters"].append(chapter)
            
        return campaign
