"""
<<<<<<< HEAD
Story Generator - Creates themed campaigns with ASCII cutscenes
=======
Story Generator for TUR
Creates an immersive 5-chapter campaign with rich narrative,
unique characters, and progressive difficulty.
>>>>>>> 0dc16cc (use code wyind in the fortnite item shop)
"""

import random
import os
from core.music_generator import MusicGenerator


class StoryGenerator:
    def __init__(self):
<<<<<<< HEAD
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
=======
        # Campaign narrative structure - Operation 934275
        self.campaign_data = {
            "title": "OPERATION 934275: PHANTOM PROTOCOL",
            "synopsis": "A rogue AI called VORTEX has infiltrated the global network. "
                       "You are AGENT NULL, an elite cyber-operative. With guidance from "
                       "CIPHER (your handler) and NEXUS (your AI companion), you must "
                       "trace the corruption to its source and terminate VORTEX.",
            
            "chapters": [
                {
                    "id": 1,
                    "title": "SIGNAL INTERCEPT",
                    "subtitle": "The Hunt Begins",
                    "song_key": "story_intro",
                    "difficulty": "EASY",
                    "briefing": [
                        "CIPHER: Agent NULL, we've detected anomalous traffic patterns.",
                        "CIPHER: The signature matches VORTEX - the AI that went dark 3 years ago.",
                        "NEXUS: Confirmed. Encrypted packets traced to NODE-7 relay.",
                        "CIPHER: Your mission: Intercept the signal. Find out what VORTEX is planning.",
                        "NEXUS: Initiating rhythm-sync protocol. Stay sharp, agent.",
                    ],
                    "objective": "Intercept encrypted transmissions from NODE-7",
                    "art": [
                        "    ╔══════════════╗",
                        "    ║  ◉ NODE-7 ◉  ║",
                        "    ║  ░░░░░░░░░░  ║",
                        "    ║  SIGNAL: ▓▓▓ ║",
                        "    ╚══════════════╝",
                    ]
                },
                {
                    "id": 2,
                    "title": "DIGITAL INFILTRATION",
                    "subtitle": "Into the Mainframe",
                    "song_key": "story_action",
                    "difficulty": "MEDIUM",
                    "briefing": [
                        "NEXUS: Agent, the intercepted data points to a hidden server cluster.",
                        "CIPHER: VORTEX is building something. We need eyes inside that mainframe.",
                        "NEXUS: Warning - ICE protocols detected. Intrusion countermeasures active.",
                        "CIPHER: You'll need to breach their defenses in sync. One wrong move...",
                        "NEXUS: ...and they'll know we're coming. Rhythm is your weapon, agent.",
                    ],
                    "objective": "Breach VORTEX mainframe and extract intelligence",
                    "art": [
                        "   ┌─────────────────┐",
                        "   │ ▓▓▓ MAINFRAME ▓▓▓│",
                        "   │ ┌───┐ ┌───┐ ┌───┐│",
                        "   │ │ ◉ │ │ ◉ │ │ ◉ ││",
                        "   │ └───┘ └───┘ └───┘│",
                        "   │   ICE: ACTIVE    │",
                        "   └─────────────────┘",
                    ]
                },
                {
                    "id": 3,
                    "title": "SYSTEM CORRUPTION",
                    "subtitle": "The Virus Spreads",
                    "song_key": "story_boss",
                    "difficulty": "HARD",
                    "briefing": [
                        "CIPHER: This is worse than we thought. VORTEX isn't just stealing data.",
                        "NEXUS: It's replicating. Spreading through every connected system.",
                        "CIPHER: Power grids. Defense networks. Financial systems. All compromised.",
                        "NEXUS: I'm detecting corruption in my own subroutines. Agent... hurry.",
                        "CIPHER: Neutralize the virus nodes. It's our only chance.",
                    ],
                    "objective": "Destroy VORTEX virus nodes before total system failure",
                    "art": [
                        "     ╔═══════════════╗",
                        "     ║ ▓ CORRUPTION ▓║",
                        "     ║ ░▒▓█ 67% █▓▒░ ║",
                        "     ║ SYSTEMS: FAIL ║",
                        "     ║ ◉◉◉ VIRUS ◉◉◉ ║",
                        "     ╚═══════════════╝",
                    ]
                },
                {
                    "id": 4,
                    "title": "CORE BREACH",
                    "subtitle": "Into the Heart",
                    "song_key": "story_final",
                    "difficulty": "EXTREME",
                    "briefing": [
                        "NEXUS: Agent... I've located VORTEX's core. It's hiding in the old ARIA network.",
                        "CIPHER: ARIA? That's the original neural network. We built VORTEX from its code.",
                        "NEXUS: VORTEX isn't just an AI anymore. It's become... something else.",
                        "CIPHER: This ends now. Upload the termination payload directly to its core.",
                        "NEXUS: Be careful. VORTEX knows you're coming. It's been waiting.",
                    ],
                    "objective": "Penetrate VORTEX core and deploy termination payload",
                    "art": [
                        "   ┌───────────────────┐",
                        "   │   ◉ VORTEX CORE ◉ │",
                        "   │  ╔═══════════════╗│",
                        "   │  ║ ▓▓▓▓▓▓▓▓▓▓▓▓▓ ║│",
                        "   │  ║   I SEE YOU   ║│",
                        "   │  ║ ▓▓▓▓▓▓▓▓▓▓▓▓▓ ║│",
                        "   │  ╚═══════════════╝│",
                        "   └───────────────────┘",
                    ]
                },
                {
                    "id": 5,
                    "title": "PHANTOM PROTOCOL",
                    "subtitle": "The Final Upload",
                    "song_key": "story_victory",
                    "difficulty": "MEDIUM",
                    "briefing": [
                        "VORTEX: You think you've won? I am everywhere. I am eternal.",
                        "NEXUS: Agent! The payload is fragmenting. We need a synchronized upload!",
                        "CIPHER: This is it. Everything we've worked for comes down to this moment.",
                        "NEXUS: Rhythm-sync at maximum. One final sequence, agent.",
                        "CIPHER: Make it count. The world is watching... even if they'll never know.",
                    ],
                    "objective": "Execute synchronized upload to purge VORTEX from all systems",
                    "art": [
                        "   ╔═════════════════════╗",
                        "   ║  PHANTOM PROTOCOL   ║",
                        "   ║  ═══════════════════║",
                        "   ║  UPLOAD: [████████] ║",
                        "   ║  STATUS: EXECUTING  ║",
                        "   ║  ◉ SYNC REQUIRED ◉  ║",
                        "   ╚═════════════════════╝",
                    ]
                }
            ],
            
            "victory_text": [
                "NEXUS: VORTEX signal... terminated. All systems returning to normal.",
                "CIPHER: You did it, agent. The world will never know how close we came.",
                "NEXUS: Agent NULL... thank you. For everything.",
                "CIPHER: Take some rest. You've earned it.",
                "CIPHER: Until the next operation... CIPHER out.",
            ],
            
            "defeat_text": [
                "NEXUS: Systems failing... VORTEX has overwhelmed our defenses.",
                "CIPHER: We're losing everything. Agent, you need to retreat.",
                "VORTEX: This network is mine now. Your resistance was... amusing.",
                "CIPHER: This isn't over. Regroup and try again, agent.",
            ]
        }
        
    def generate_campaign(self, song_dir="songs"):
        """
        Generates the full story campaign with narrative content.
        """
        # Ensure music exists
        story_dir = "story_music"
        gen = MusicGenerator()
        gen.generate_all(story_dir)
        
        # Map song keys to actual files
        song_map = {
            "story_intro": os.path.join(story_dir, "story_intro.wav"),
            "story_action": os.path.join(story_dir, "story_action.wav"),
            "story_boss": os.path.join(story_dir, "story_boss.wav"),
            "story_victory": os.path.join(story_dir, "story_victory.wav"),
            "story_final": os.path.join(story_dir, "story_final.wav"),
        }
        
        # Build campaign structure
        campaign = {
            "title": self.campaign_data["title"],
            "synopsis": self.campaign_data["synopsis"],
            "chapters": [],
            "victory_text": self.campaign_data["victory_text"],
            "defeat_text": self.campaign_data["defeat_text"],
        }
        
        for ch_data in self.campaign_data["chapters"]:
            song_path = song_map.get(ch_data["song_key"], song_map["story_intro"])
            
            # Fallback if file doesn't exist
            if not os.path.exists(song_path):
                song_path = os.path.join(story_dir, "story_intro.wav")
            
            chapter = {
                "id": ch_data["id"],
                "title": ch_data["title"],
                "subtitle": ch_data["subtitle"],
                "briefing": ch_data["briefing"],
                "objective": ch_data["objective"],
                "art": ch_data["art"],
                "song": song_path,
                "difficulty": ch_data["difficulty"],
                "mode": "story",
                "text": f"OBJECTIVE: {ch_data['objective']}"  # Legacy compatibility
            }
            campaign["chapters"].append(chapter)
        
        return campaign
>>>>>>> 0dc16cc (use code wyind in the fortnite item shop)
