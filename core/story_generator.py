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
        # Ensure songs exist
        gen = MusicGenerator()
        new_songs = gen.generate_all(song_dir)
        
        # Find available songs
        songs = []
        if os.path.exists(song_dir):
            songs = [f for f in os.listdir(song_dir) if f.lower().endswith(('.mp3', '.wav', '.ogg'))]
            # Prefer generated ones for story order?
            # Sort to put story_intro first, then action, then boss
            
        # Sort logic: intro -> action -> boss -> others
        story_order = ["story_intro.wav", "story_action.wav", "story_boss.wav"]
        sorted_songs = []
        for key in story_order:
            if key in songs:
                sorted_songs.append(key)
                songs.remove(key)
        sorted_songs.extend(songs) # Append rest
        songs = sorted_songs
        
        if not songs:
            songs = ["story_intro.wav"] # Should exist now
            
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
