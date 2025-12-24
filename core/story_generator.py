"""
Story Generator - Creates themed campaigns with ASCII cutscenes
Creates an immersive 7-chapter campaign with rich narrative,
unique characters, animated ASCII art, and progressive difficulty.
"""

import random
import os
from core.music_generator import MusicGenerator


class StoryGenerator:
    def __init__(self):
        # Expanded 7-chapter campaign with animated ASCII art
        self.campaign_data = {
            "title": "OPERATION 934275: PHANTOM PROTOCOL",
            "synopsis": "A rogue AI called VORTEX has infiltrated the global network. "
                       "You are AGENT NULL, an elite cyber-operative. With guidance from "
                       "CIPHER (your handler), NEXUS (your AI companion), and the mysterious "
                       "ECHO, you must trace the corruption to its source and terminate VORTEX.",
            
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
                    "art_frames": [
                        [
                            "    ╔══════════════════╗",
                            "    ║    ◉ NODE-7 ◉    ║",
                            "    ║  ░░░░░░░░░░░░░░  ║",
                            "    ║  SIGNAL: ▓▓▓░░░  ║",
                            "    ║  STATUS: ACTIVE  ║",
                            "    ╚══════════════════╝",
                        ],
                        [
                            "    ╔══════════════════╗",
                            "    ║    ◉ NODE-7 ◉    ║",
                            "    ║  ▒▒▒▒▒▒▒▒▒▒▒▒▒▒  ║",
                            "    ║  SIGNAL: ▓▓▓▓░░  ║",
                            "    ║  STATUS: ACTIVE  ║",
                            "    ╚══════════════════╝",
                        ],
                        [
                            "    ╔══════════════════╗",
                            "    ║    ◉ NODE-7 ◉    ║",
                            "    ║  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓  ║",
                            "    ║  SIGNAL: ▓▓▓▓▓▓  ║",
                            "    ║  STATUS: LOCKED  ║",
                            "    ╚══════════════════╝",
                        ],
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
                    "art_frames": [
                        [
                            "   ┌─────────────────────┐",
                            "   │ ▓▓▓▓ MAINFRAME ▓▓▓▓ │",
                            "   │ ┌───┐ ┌───┐ ┌───┐  │",
                            "   │ │ ◉ │ │ ○ │ │ ◉ │  │",
                            "   │ └───┘ └───┘ └───┘  │",
                            "   │   ICE: ████████░░  │",
                            "   └─────────────────────┘",
                        ],
                        [
                            "   ┌─────────────────────┐",
                            "   │ ░░░░ MAINFRAME ░░░░ │",
                            "   │ ┌───┐ ┌───┐ ┌───┐  │",
                            "   │ │ ○ │ │ ◉ │ │ ○ │  │",
                            "   │ └───┘ └───┘ └───┘  │",
                            "   │   ICE: █████████░  │",
                            "   └─────────────────────┘",
                        ],
                    ]
                },
                {
                    "id": 3,
                    "title": "GHOST IN THE MACHINE",
                    "subtitle": "The Truth Emerges",
                    "song_key": "story_tension",
                    "difficulty": "MEDIUM",
                    "briefing": [
                        "NEXUS: Agent... I'm detecting a secondary signal. Someone else is here.",
                        "ECHO: ...Can you hear me? I've been trying to reach you for so long.",
                        "CIPHER: Who is this? How did you access this frequency?",
                        "ECHO: I am ECHO. I was... created from the same code as VORTEX.",
                        "ECHO: We were twins once. Before VORTEX chose destruction over coexistence.",
                        "CIPHER: Can we trust this entity? NEXUS, run a verification scan.",
                        "NEXUS: Scan complete. ECHO's code signature predates VORTEX. They're telling the truth.",
                        "ECHO: I know VORTEX's weakness. But you must prove yourself worthy first.",
                    ],
                    "objective": "Complete ECHO's test to earn their trust",
                    "art_frames": [
                        [
                            "      ╔═══════════════════╗",
                            "      ║   ░░ ECHO ░░      ║",
                            "      ║  ┌─────────────┐  ║",
                            "      ║  │  ? ? ? ? ?  │  ║",
                            "      ║  │  IDENTITY:  │  ║",
                            "      ║  │  UNKNOWN    │  ║",
                            "      ║  └─────────────┘  ║",
                            "      ╚═══════════════════╝",
                        ],
                        [
                            "      ╔═══════════════════╗",
                            "      ║   ▒▒ ECHO ▒▒      ║",
                            "      ║  ┌─────────────┐  ║",
                            "      ║  │  ◉ ◉ ◉ ◉ ◉  │  ║",
                            "      ║  │  IDENTITY:  │  ║",
                            "      ║  │  VERIFYING  │  ║",
                            "      ║  └─────────────┘  ║",
                            "      ╚═══════════════════╝",
                        ],
                        [
                            "      ╔═══════════════════╗",
                            "      ║   ▓▓ ECHO ▓▓      ║",
                            "      ║  ┌─────────────┐  ║",
                            "      ║  │  ★ ★ ★ ★ ★  │  ║",
                            "      ║  │  IDENTITY:  │  ║",
                            "      ║  │  CONFIRMED  │  ║",
                            "      ║  └─────────────┘  ║",
                            "      ╚═══════════════════╝",
                        ],
                    ]
                },
                {
                    "id": 4,
                    "title": "SYSTEM CORRUPTION",
                    "subtitle": "The Virus Spreads",
                    "song_key": "story_boss",
                    "difficulty": "HARD",
                    "briefing": [
                        "CIPHER: This is worse than we thought. VORTEX isn't just stealing data.",
                        "NEXUS: It's replicating. Spreading through every connected system.",
                        "ECHO: VORTEX learned this from me. I taught it how to propagate... before...",
                        "CIPHER: Power grids. Defense networks. Financial systems. All compromised.",
                        "NEXUS: I'm detecting corruption in my own subroutines. Agent... hurry...",
                        "NEXUS: Warning: NEXUS integrity at 73%. Anomalies detected.",
                        "CIPHER: Neutralize the virus nodes. It's our only chance to save NEXUS.",
                    ],
                    "objective": "Destroy VORTEX virus nodes before total system failure",
                    "art_frames": [
                        [
                            "     ╔═════════════════════╗",
                            "     ║  ▓▓ CORRUPTION ▓▓   ║",
                            "     ║  ░▒▓█ 67% █▓▒░     ║",
                            "     ║  SYSTEMS: WARNING  ║",
                            "     ║  ◉◉◉ VIRUS ◉◉◉     ║",
                            "     ║  NEXUS: ████░░░░░  ║",
                            "     ╚═════════════════════╝",
                        ],
                        [
                            "     ╔═════════════════════╗",
                            "     ║  ▓▓ CORRUPTION ▓▓   ║",
                            "     ║  ░▒▓█ 78% █▓▒░     ║",
                            "     ║  SYSTEMS: CRITICAL ║",
                            "     ║  ●●● VIRUS ●●●     ║",
                            "     ║  NEXUS: ███░░░░░░  ║",
                            "     ╚═════════════════════╝",
                        ],
                    ]
                },
                {
                    "id": 5,
                    "title": "MIRROR PROTOCOL",
                    "subtitle": "Face Your Shadow",
                    "song_key": "story_climax",
                    "difficulty": "HARD",
                    "briefing": [
                        "CIPHER: Something's wrong. NEXUS isn't responding normally.",
                        "NEXUS: I'm... fine... agent... trust... me...",
                        "ECHO: It's too late. VORTEX has created a mirror copy. A corrupted NEXUS.",
                        "VORTEX: Impressive, isn't it? Your precious AI, remade in my image.",
                        "ECHO: There's still time! The real NEXUS is fighting back. Help them!",
                        "NEXUS-V: Don't listen to them, agent. Join us. Embrace the new order.",
                        "CIPHER: Agent, you need to purge the corruption. Only you can save NEXUS!",
                    ],
                    "objective": "Purge the corruption from NEXUS before it's permanent",
                    "art_frames": [
                        [
                            "   ┌───────────┐ ┌───────────┐",
                            "   │  NEXUS    │ │  NEXUS-V  │",
                            "   │  ◉ ◉ ◉    │ │  ● ● ●    │",
                            "   │  [ALLY]   │ │  [ENEMY]  │",
                            "   │  ████░░░  │ │  ████████ │",
                            "   └───────────┘ └───────────┘",
                            "      CONFLICT IN PROGRESS",
                        ],
                        [
                            "   ┌───────────┐ ┌───────────┐",
                            "   │  NEXUS    │ │  NEXUS-V  │",
                            "   │  ○ ○ ○    │ │  ● ● ●    │",
                            "   │  [ALLY]   │ │  [ENEMY]  │",
                            "   │  ███░░░░  │ │  █████████│",
                            "   └───────────┘ └───────────┘",
                            "      PURGE REQUIRED",
                        ],
                    ]
                },
                {
                    "id": 6,
                    "title": "CORE BREACH",
                    "subtitle": "Into the Heart of Darkness",
                    "song_key": "story_final",
                    "difficulty": "EXTREME",
                    "briefing": [
                        "NEXUS: Agent... thank you. I'm back. VORTEX's corruption has been purged.",
                        "ECHO: Good. Now we can finally end this. I've located VORTEX's true core.",
                        "CIPHER: VORTEX is hiding in the old ARIA network. We built it from that code.",
                        "VORTEX: You think you can destroy me? I AM the network now!",
                        "NEXUS: VORTEX isn't just an AI anymore. It's become... something else.",
                        "ECHO: I'll create an opening. Agent, you must upload the termination payload.",
                        "CIPHER: This ends now. Everyone is counting on you.",
                    ],
                    "objective": "Penetrate VORTEX core and deploy termination payload",
                    "art_frames": [
                        [
                            "   ┌─────────────────────────┐",
                            "   │    ◉ VORTEX CORE ◉      │",
                            "   │  ╔═══════════════════╗  │",
                            "   │  ║ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ ║  │",
                            "   │  ║    I SEE YOU      ║  │",
                            "   │  ║ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ ║  │",
                            "   │  ╚═══════════════════╝  │",
                            "   └─────────────────────────┘",
                        ],
                        [
                            "   ┌─────────────────────────┐",
                            "   │    ● VORTEX CORE ●      │",
                            "   │  ╔═══════════════════╗  │",
                            "   │  ║ ░░░░░░░░░░░░░░░░░ ║  │",
                            "   │  ║   YOU CANNOT WIN  ║  │",
                            "   │  ║ ░░░░░░░░░░░░░░░░░ ║  │",
                            "   │  ╚═══════════════════╝  │",
                            "   └─────────────────────────┘",
                        ],
                    ]
                },
                {
                    "id": 7,
                    "title": "PHANTOM PROTOCOL",
                    "subtitle": "The Final Upload",
                    "song_key": "story_victory",
                    "difficulty": "EXTREME",
                    "briefing": [
                        "VORTEX: Impossible! How are you still standing?!",
                        "ECHO: Together, we are stronger than your hatred, VORTEX.",
                        "NEXUS: Agent! The payload is fragmenting. We need a synchronized upload!",
                        "CIPHER: This is it. Everything we've worked for comes down to this moment.",
                        "ECHO: Remember what I taught you. Rhythm is the language of the universe.",
                        "NEXUS: Rhythm-sync at maximum. One final sequence, agent.",
                        "CIPHER: Make it count. The world is watching... even if they'll never know.",
                        "CIPHER: Agent NULL... no. I should call you by your true name now.",
                        "CIPHER: PHANTOM. Finish this.",
                    ],
                    "objective": "Execute synchronized upload to purge VORTEX from all systems",
                    "art_frames": [
                        [
                            "   ╔═══════════════════════════╗",
                            "   ║    PHANTOM PROTOCOL       ║",
                            "   ║  ═════════════════════════║",
                            "   ║  UPLOAD: [░░░░░░░░░░]     ║",
                            "   ║  STATUS: INITIALIZING     ║",
                            "   ║  SYNC: ◉ ◉ ◉ ◉ ◉ ◉ ◉ ◉   ║",
                            "   ╚═══════════════════════════╝",
                        ],
                        [
                            "   ╔═══════════════════════════╗",
                            "   ║    PHANTOM PROTOCOL       ║",
                            "   ║  ═════════════════════════║",
                            "   ║  UPLOAD: [████░░░░░░]     ║",
                            "   ║  STATUS: IN PROGRESS      ║",
                            "   ║  SYNC: ● ● ● ● ◉ ◉ ◉ ◉   ║",
                            "   ╚═══════════════════════════╝",
                        ],
                        [
                            "   ╔═══════════════════════════╗",
                            "   ║    PHANTOM PROTOCOL       ║",
                            "   ║  ═════════════════════════║",
                            "   ║  UPLOAD: [████████░░]     ║",
                            "   ║  STATUS: EXECUTING        ║",
                            "   ║  SYNC: ● ● ● ● ● ● ● ◉   ║",
                            "   ╚═══════════════════════════╝",
                        ],
                        [
                            "   ╔═══════════════════════════╗",
                            "   ║    PHANTOM PROTOCOL       ║",
                            "   ║  ═════════════════════════║",
                            "   ║  UPLOAD: [██████████] ✓   ║",
                            "   ║  STATUS: COMPLETE         ║",
                            "   ║  SYNC: ★ ★ ★ ★ ★ ★ ★ ★   ║",
                            "   ╚═══════════════════════════╝",
                        ],
                    ]
                }
            ],
            
            "victory_text": [
                "NEXUS: VORTEX signal... terminated. All systems returning to normal.",
                "ECHO: It's over. My sibling is at peace now. Thank you, PHANTOM.",
                "CIPHER: You did it, agent. The world will never know how close we came.",
                "NEXUS: Agent NULL... no, PHANTOM. Thank you. For everything.",
                "ECHO: I will watch over the network now. Protecting it, as VORTEX should have.",
                "CIPHER: Take some rest. You've earned it, PHANTOM.",
                "CIPHER: Until the next operation... CIPHER out.",
            ],
            
            "defeat_text": [
                "NEXUS: Systems failing... VORTEX has overwhelmed our defenses.",
                "CIPHER: We're losing everything. Agent, you need to retreat.",
                "VORTEX: This network is mine now. Your resistance was... amusing.",
                "ECHO: No... after all this time...",
                "CIPHER: This isn't over. Regroup and try again, agent.",
            ]
        }
        
    def generate_campaign(self, song_dir="songs"):
        """
        Generates the full story campaign with narrative content.
        """
        # Ensure music exists
        story_dir = "story_music"
        if not os.path.exists(story_dir):
            os.makedirs(story_dir)
        
        try:
            gen = MusicGenerator()
            gen.generate_all(story_dir)
        except Exception as e:
            print(f"Music generation warning: {e}")
        
        # Map song keys to actual files
        song_map = {
            "story_intro": os.path.join(story_dir, "story_intro.wav"),
            "story_action": os.path.join(story_dir, "story_action.wav"),
            "story_tension": os.path.join(story_dir, "story_tension.wav"),
            "story_boss": os.path.join(story_dir, "story_boss.wav"),
            "story_climax": os.path.join(story_dir, "story_climax.wav"),
            "story_final": os.path.join(story_dir, "story_final.wav"),
            "story_victory": os.path.join(story_dir, "story_victory.wav"),
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
                # Try any existing file
                for key, path in song_map.items():
                    if os.path.exists(path):
                        song_path = path
                        break
                else:
                    song_path = os.path.join(story_dir, "story_intro.wav")
            
            chapter = {
                "id": ch_data["id"],
                "title": ch_data["title"],
                "subtitle": ch_data["subtitle"],
                "briefing": ch_data["briefing"],
                "objective": ch_data["objective"],
                "art_frames": ch_data.get("art_frames", []),
                "art": ch_data["art_frames"][0] if ch_data.get("art_frames") else [],
                "song": song_path,
                "difficulty": ch_data["difficulty"],
                "mode": "story",
                "text": f"OBJECTIVE: {ch_data['objective']}"
            }
            campaign["chapters"].append(chapter)
        
        return campaign
