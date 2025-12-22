"""
Story Generator - Creates themed campaigns with ASCII cutscenes
"""

import random
import os
from core.music_generator import MusicGenerator


class StoryGenerator:
    def __init__(self):
        # Themed chapters with story and ASCII art
        self.chapters = [
            {
                "title": "INITIALIZATION",
                "subtitle": "The journey begins...",
                "song_key": "story_intro",
                "difficulty": "EASY",
                "briefing": [
                    "CIPHER: Agent, welcome to the network.",
                    "CIPHER: Your first task is simple - calibrate your systems.",
                    "CIPHER: Follow the rhythm protocol to synchronize.",
                    "AGENT: Understood. Beginning calibration sequence."
                ],
                "objective": "Complete the calibration sequence.",
                "art": [
                    "  ╔══════════════╗",
                    "  ║  SYSTEM v1.0 ║",
                    "  ║   [ONLINE]   ║",
                    "  ║  ████░░░░ 42%║",
                    "  ╚══════════════╝"
                ]
            },
            {
                "title": "BREACH PROTOCOL",
                "subtitle": "First contact with the enemy",
                "song_key": "story_action",
                "difficulty": "MEDIUM",
                "briefing": [
                    "NEXUS: Hostile firewall detected ahead.",
                    "NEXUS: We need you to breach their defenses.",
                    "CIPHER: Use aggressive tempo - match their encryption.",
                    "AGENT: Initiating breach sequence now."
                ],
                "objective": "Break through the enemy firewall.",
                "art": [
                    "   ░▒▓█ FIREWALL █▓▒░",
                    "   ╔═══════════════╗",
                    "   ║ ▓▓▓▓░░░░░░░░░ ║",
                    "   ║   ENCRYPTED   ║",
                    "   ╚═══════════════╝"
                ]
            },
            {
                "title": "DATA EXTRACTION",
                "subtitle": "The core is exposed",
                "song_key": "story_boss",
                "difficulty": "HARD",
                "briefing": [
                    "VORTEX: The mainframe is vulnerable.",
                    "VORTEX: Extract the data before they detect us.",
                    "CIPHER: Warning - security escalation imminent.",
                    "AGENT: I'll handle it. Starting extraction."
                ],
                "objective": "Extract critical data from the mainframe.",
                "art": [
                    "      ┌─────────┐",
                    "    ┌─┤MAINFRAME├─┐",
                    "    │ └────┬────┘ │",
                    "  ┌─┴─┐  ┌─┴─┐  ┌─┴─┐",
                    "  │ A │  │ B │  │ C │",
                    "  └───┘  └───┘  └───┘"
                ]
            }
        ]
        
    def generate_campaign(self, song_dir="songs"):
        """Generate story campaign with songs"""
        story_dir = "story_music"
        
        # Ensure story music exists
        if not os.path.exists(story_dir):
            os.makedirs(story_dir)
        
        try:
            gen = MusicGenerator()
            gen.generate_all(story_dir)
        except Exception as e:
            print(f"Music generation warning: {e}")
        
        # Find available songs
        songs = {}
        if os.path.exists(story_dir):
            for f in os.listdir(story_dir):
                if f.lower().endswith(('.mp3', '.wav', '.ogg')):
                    stem = os.path.splitext(f)[0]
                    songs[stem] = os.path.join(story_dir, f)
        
        # Build chapters with song assignments
        campaign_chapters = []
        for ch in self.chapters:
            song_key = ch["song_key"]
            song_path = songs.get(song_key)
            
            if not song_path and songs:
                song_path = list(songs.values())[0]
            elif not song_path:
                song_path = "story_music/story_intro.wav"
            
            campaign_chapters.append({
                "title": ch["title"],
                "subtitle": ch.get("subtitle", ""),
                "song": song_path,
                "difficulty": ch["difficulty"],
                "text": " ".join(ch.get("briefing", [])),
                "briefing": ch.get("briefing", []),
                "objective": ch.get("objective", "Complete the mission."),
                "art": ch.get("art", [])
            })
        
        return {
            "title": "OPERATION PHANTOM",
            "chapters": campaign_chapters
        }
