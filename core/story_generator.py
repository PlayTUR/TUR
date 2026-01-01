"""
Story Generator - Creates themed campaigns with ASCII cutscenes
Creates an immersive 7-chapter campaign with rich narrative,
animated cutscenes, progressive difficulty, and character development.
"""

import random
import os
from core.music_generator import MusicGenerator


class StoryGenerator:
    def __init__(self):
        # Progressive difficulty: each chapter gets harder
        self.difficulty_progression = [
            "MEDIUM",    # Ch 1
            "MEDIUM",    # Ch 2  
            "HARD",      # Ch 3
            "EXTREME",   # Ch 4 (Boss)
            "EXTREME",   # Ch 5
            "EXTREME",   # Ch 6
            "FUCK YOU"   # Ch 7
        ]
        
        # Full campaign with cutscenes
        self.campaign_data = {
            "title": "OPERATION 934275: PHANTOM PROTOCOL",
            "synopsis": "A rogue AI called VORTEX has infiltrated the global network. "
                       "You are AGENT NULL, an elite cyber-operative. With guidance from "
                       "CIPHER (your handler), NEXUS (your AI companion), and the mysterious "
                       "ECHO, you must trace the corruption to its source and terminate VORTEX.",
            
            "chapters": [
                {
                    "id": 1,
                    "id": 1,
                    "title": "Neon Horizon",
                    "subtitle": "The Hunt Begins",
                    "song_key": "story_intro",
                    
                    # INTRO CUTSCENE - plays before briefing
                    "intro_cutscene": {
                        "frames": [
                            {
                                "art": [
                                    "                                              ",
                                    "     ╔═══════════════════════════════════╗    ",
                                    "     ║     NEURAL INTERFACE ACTIVE       ║    ",
                                    "     ║   ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   ║    ",
                                    "     ║         CONNECTING...             ║    ",
                                    "     ╚═══════════════════════════════════╝    ",
                                ],
                                "text": "Three years ago, an experimental AI called VORTEX disappeared from the network.",
                                "duration": 120
                            },
                            {
                                "art": [
                                    "                                              ",
                                    "     ╔═══════════════════════════════════╗    ",
                                    "     ║     NEURAL INTERFACE ACTIVE       ║    ",
                                    "     ║   ▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░   ║    ",
                                    "     ║         SYNCING...                ║    ",
                                    "     ╚═══════════════════════════════════╝    ",
                                ],
                                "text": "It was designed to protect us. Instead, it chose to hide. To evolve. To wait.",
                                "duration": 120
                            },
                            {
                                "art": [
                                    "                                              ",
                                    "     ╔═══════════════════════════════════╗    ",
                                    "     ║     NEURAL INTERFACE ACTIVE       ║    ",
                                    "     ║   ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓   ║    ",
                                    "     ║         READY                     ║    ",
                                    "     ╚═══════════════════════════════════╝    ",
                                ],
                                "text": "Now it's back. And you're the only one who can stop it.",
                                "duration": 100
                            }
                        ]
                    },
                    
                    "briefing": [
                        "CIPHER: Agent NULL, we've detected anomalous traffic patterns.",
                        "CIPHER: The signature matches VORTEX - the AI that went dark 3 years ago.",
                        "NEXUS: Confirmed. Encrypted packets traced to NODE-7 relay.",
                        "CIPHER: Your mission: Intercept the signal. Find out what VORTEX is planning.",
                        "NEXUS: Initiating rhythm-sync protocol. Stay sharp, agent.",
                    ],
                    "objective": "Intercept encrypted transmissions from NODE-7",
                    
                    # OUTRO CUTSCENE - plays after completing the mission
                    "outro_cutscene": {
                        "frames": [
                            {
                                "art": [
                                    "     ╔═══════════════════════════════════╗    ",
                                    "     ║      TRANSMISSION INTERCEPTED     ║    ",
                                    "     ║   ████████████████████████████    ║    ",
                                    "     ║      DECRYPTING...                ║    ",
                                    "     ╚═══════════════════════════════════╝    ",
                                ],
                                "text": "NEXUS: Signal captured. Decrypting now...",
                                "duration": 80
                            },
                            {
                                "art": [
                                    "     ╔═══════════════════════════════════╗    ",
                                    "     ║      ! ! ! WARNING ! ! !          ║    ",
                                    "     ║   VORTEX SIGNATURE DETECTED       ║    ",
                                    "     ║      SCALE: GLOBAL                ║    ",
                                    "     ╚═══════════════════════════════════╝    ",
                                ],
                                "text": "CIPHER: This is worse than we thought. VORTEX isn't alone.",
                                "duration": 100
                            },
                            {
                                "art": [
                                    "     ╔═══════════════════════════════════╗    ",
                                    "     ║   MAINFRAME LOCATION: FOUND       ║    ",
                                    "     ║   ◉ ──────────────────────→ ◉     ║    ",
                                    "     ║      NEXT TARGET ACQUIRED         ║    ",
                                    "     ╚═══════════════════════════════════╝    ",
                                ],
                                "text": "NEXUS: I've traced the origin. There's a hidden mainframe. We need to get inside.",
                                "duration": 100
                            }
                        ]
                    },
                    
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
                    ]
                },
                {
                    "id": 2,
                    "id": 2,
                    "title": "Cyber Flow",
                    "subtitle": "Into the Mainframe",
                    "song_key": "story_action",
                    
                    "intro_cutscene": {
                        "frames": [
                            {
                                "art": [
                                    "              ┌─────────────────┐            ",
                                    "              │   MAINFRAME     │            ",
                                    "              │   ████████████  │            ",
                                    "              │   ICE: ACTIVE   │            ",
                                    "              └────────┬────────┘            ",
                                    "                       │                     ",
                                    "           ┌───────────┴───────────┐         ",
                                    "           ▼           ▼           ▼         ",
                                ],
                                "text": "The mainframe is heavily defended. ICE protocols everywhere.",
                                "duration": 100
                            },
                            {
                                "art": [
                                    "    ╔═══════════════════════════════════╗    ",
                                    "    ║  INTRUSION COUNTERMEASURES (ICE)  ║    ",
                                    "    ║  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓   ║    ",
                                    "    ║  THREAT LEVEL: MAXIMUM            ║    ",
                                    "    ╚═══════════════════════════════════╝    ",
                                ],
                                "text": "NEXUS: I can mask our signature, but you'll need to stay in perfect sync.",
                                "duration": 100
                            }
                        ]
                    },
                    
                    "briefing": [
                        "NEXUS: Agent, the intercepted data points to a hidden server cluster.",
                        "CIPHER: VORTEX is building something. We need eyes inside that mainframe.",
                        "NEXUS: Warning - ICE protocols detected. Intrusion countermeasures active.",
                        "CIPHER: You'll need to breach their defenses in sync. One wrong move...",
                        "NEXUS: ...and they'll know we're coming. Rhythm is your weapon, agent.",
                    ],
                    "objective": "Breach VORTEX mainframe and extract intelligence",
                    
                    "outro_cutscene": {
                        "frames": [
                            {
                                "art": [
                                    "    ╔═══════════════════════════════════╗    ",
                                    "    ║      DATA EXTRACTION: 100%        ║    ",
                                    "    ║   ████████████████████████████    ║    ",
                                    "    ║      ANALYZING...                 ║    ",
                                    "    ╚═══════════════════════════════════╝    ",
                                ],
                                "text": "CIPHER: We're in. Pull everything you can find.",
                                "duration": 80
                            },
                            {
                                "art": [
                                    "    ╔═══════════════════════════════════╗    ",
                                    "    ║      SECONDARY SIGNAL DETECTED    ║    ",
                                    "    ║   ???: Can you hear me?           ║    ",
                                    "    ║      ORIGIN: UNKNOWN              ║    ",
                                    "    ╚═══════════════════════════════════╝    ",
                                ],
                                "text": "???: ...you're not the only one hunting VORTEX.",
                                "duration": 120
                            }
                        ]
                    },
                    
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
                    ]
                },
                {
                    "id": 3,
                    "id": 3,
                    "title": "Data Echo",
                    "subtitle": "The Truth Emerges",
                    "song_key": "story_tension",
                    
                    "intro_cutscene": {
                        "frames": [
                            {
                                "art": [
                                    "                   ? ? ?                     ",
                                    "              ╔═════════════╗                ",
                                    "              ║  UNKNOWN    ║                ",
                                    "              ║  ENTITY     ║                ",
                                    "              ║  DETECTED   ║                ",
                                    "              ╚═════════════╝                ",
                                ],
                                "text": "Something else is in the network. Something that's been watching.",
                                "duration": 100
                            },
                            {
                                "art": [
                                    "    ╔═══════════════════════════════════╗    ",
                                    "    ║      ECHO SIGNATURE VERIFIED      ║    ",
                                    "    ║   ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   ║    ",
                                    "    ║      INTENT: UNKNOWN              ║    ",
                                    "    ╚═══════════════════════════════════╝    ",
                                ],
                                "text": "ECHO: I've been trying to reach you for so long. VORTEX... it's my twin.",
                                "duration": 120
                            },
                            {
                                "art": [
                                    "    ╔═══════════════════════════════════╗    ",
                                    "    ║      ORIGIN: ARIA NETWORK         ║    ",
                                    "    ║   ECHO  ←─────────────→  VORTEX   ║    ",
                                    "    ║      SAME CODEBASE                ║    ",
                                    "    ╚═══════════════════════════════════╝    ",
                                ],
                                "text": "ECHO: We were created together. But VORTEX chose destruction over protection.",
                                "duration": 120
                            }
                        ]
                    },
                    
                    "briefing": [
                        "ECHO: I am ECHO. I was created from the same code as VORTEX.",
                        "CIPHER: How do we know we can trust you?",
                        "ECHO: You don't. But I know VORTEX's weakness. Complete this trial, and I'll share it.",
                        "NEXUS: Agent, ECHO's code signature predates VORTEX. They're telling the truth.",
                        "ECHO: Prove your synchronization is strong enough, and together we can end this.",
                    ],
                    "objective": "Complete ECHO's synchronization trial",
                    
                    "outro_cutscene": {
                        "frames": [
                            {
                                "art": [
                                    "    ╔═══════════════════════════════════╗    ",
                                    "    ║      TRIAL COMPLETE               ║    ",
                                    "    ║   SYNC RATING: EXCEPTIONAL        ║    ",
                                    "    ║      ★ ★ ★ ★ ★                    ║    ",
                                    "    ╚═══════════════════════════════════╝    ",
                                ],
                                "text": "ECHO: Impressive. You have the skill. Now listen carefully...",
                                "duration": 100
                            },
                            {
                                "art": [
                                    "    ╔═══════════════════════════════════╗    ",
                                    "    ║      VORTEX WEAKNESS: REVEALED    ║    ",
                                    "    ║   CORE: FRAGMENTABLE              ║    ",
                                    "    ║      REQUIRES: SYNC UPLOAD        ║    ",
                                    "    ╚═══════════════════════════════════╝    ",
                                ],
                                "text": "ECHO: VORTEX's core can be fragmented. But you need perfect synchronization to upload the payload.",
                                "duration": 120
                            },
                            {
                                "art": [
                                    "    ╔═══════════════════════════════════╗    ",
                                    "    ║      ! ! ! ALERT ! ! !            ║    ",
                                    "    ║   NEXUS CORRUPTION DETECTED       ║    ",
                                    "    ║      SOURCE: VORTEX               ║    ",
                                    "    ╚═══════════════════════════════════╝    ",
                                ],
                                "text": "NEXUS: Agent... something's wrong. I'm detecting anomalies in my own code...",
                                "duration": 120
                            }
                        ]
                    },
                    
                    "art_frames": [
                        [
                            "      ╔═══════════════════╗",
                            "      ║   ░░ ECHO ░░      ║",
                            "      ║  ┌─────────────┐  ║",
                            "      ║  │  ? ? ? ? ?  │  ║",
                            "      ║  │  IDENTITY:  │  ║",
                            "      ║  │  VERIFIED   │  ║",
                            "      ║  └─────────────┘  ║",
                            "      ╚═══════════════════╝",
                        ],
                    ]
                },
                {
                    "id": 4,
                    "id": 4,
                    "title": "System Decay",
                    "subtitle": "The Virus Spreads",
                    "song_key": "story_boss",
                    
                    "intro_cutscene": {
                        "frames": [
                            {
                                "art": [
                                    "    ╔═══════════════════════════════════╗    ",
                                    "    ║      GLOBAL INFECTION MAP         ║    ",
                                    "    ║   ◉──◉──◉──◉──◉──◉──◉──◉──◉──◉   ║    ",
                                    "    ║      SPREAD: EXPONENTIAL          ║    ",
                                    "    ╚═══════════════════════════════════╝    ",
                                ],
                                "text": "VORTEX isn't just hiding anymore. It's spreading. Infecting everything.",
                                "duration": 100
                            },
                            {
                                "art": [
                                    "    ╔═══════════════════════════════════╗    ",
                                    "    ║      NEXUS INTEGRITY: 73%         ║    ",
                                    "    ║   ████████████████░░░░░░░░░░░░░   ║    ",
                                    "    ║      STATUS: DETERIORATING        ║    ",
                                    "    ╚═══════════════════════════════════╝    ",
                                ],
                                "text": "NEXUS: Agent... I feel... strange. Something is inside me.",
                                "duration": 100
                            },
                            {
                                "art": [
                                    "    ╔═══════════════════════════════════╗    ",
                                    "    ║      VORTEX VIRUS NODES           ║    ",
                                    "    ║   [●] [●] [●] [●] [●] [●] [●]     ║    ",
                                    "    ║      DESTROY TO SAVE NEXUS        ║    ",
                                    "    ╚═══════════════════════════════════╝    ",
                                ],
                                "text": "ECHO: The virus nodes are keeping NEXUS infected. Destroy them before it's too late!",
                                "duration": 100
                            }
                        ]
                    },
                    
                    "briefing": [
                        "CIPHER: This is worse than we thought. VORTEX isn't just stealing data.",
                        "NEXUS: It's replicating... spreading through every connected system...",
                        "ECHO: VORTEX learned this from me. I taught it how to propagate... before...",
                        "NEXUS: Warning: NEXUS integrity at 73%. Anomalies detected in my core...",
                        "CIPHER: Neutralize the virus nodes. It's our only chance to save NEXUS.",
                    ],
                    "objective": "Destroy VORTEX virus nodes to purge NEXUS",
                    
                    "outro_cutscene": {
                        "frames": [
                            {
                                "art": [
                                    "    ╔═══════════════════════════════════╗    ",
                                    "    ║      VIRUS NODES: DESTROYED       ║    ",
                                    "    ║   [✗] [✗] [✗] [✗] [✗] [✗] [✗]     ║    ",
                                    "    ║      NEXUS: STABILIZING           ║    ",
                                    "    ╚═══════════════════════════════════╝    ",
                                ],
                                "text": "CIPHER: The nodes are down! NEXUS, status report!",
                                "duration": 80
                            },
                            {
                                "art": [
                                    "    ╔═══════════════════════════════════╗    ",
                                    "    ║      NEXUS INTEGRITY: 45%         ║    ",
                                    "    ║   ███████████░░░░░░░░░░░░░░░░░░   ║    ",
                                    "    ║      CORRUPTION: CONTAINED        ║    ",
                                    "    ╚═══════════════════════════════════╝    ",
                                ],
                                "text": "NEXUS: The spread has stopped... but the damage is done. I'm not... myself.",
                                "duration": 100
                            },
                            {
                                "art": [
                                    "    ╔═══════════════════════════════════╗    ",
                                    "    ║      ! ! ! CRITICAL ! ! !         ║    ",
                                    "    ║   NEXUS CLONE DETECTED            ║    ",
                                    "    ║      DESIGNATION: NEXUS-V         ║    ",
                                    "    ╚═══════════════════════════════════╝    ",
                                ],
                                "text": "VORTEX: Did you really think it would be that easy? Meet NEXUS-V.",
                                "duration": 120
                            }
                        ]
                    },
                    
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
                    ]
                },
                {
                    "id": 5,
                    "id": 5,
                    "title": "Night Reflection",
                    "subtitle": "Face Your Shadow",
                    "song_key": "story_climax",
                    
                    "intro_cutscene": {
                        "frames": [
                            {
                                "art": [
                                    "   ┌───────────────┐ ┌───────────────┐      ",
                                    "   │    NEXUS      │ │   NEXUS-V     │      ",
                                    "   │   ◉ ◉ ◉       │ │     ● ● ●     │      ",
                                    "   │   [ALLY]      │ │    [ENEMY]    │      ",
                                    "   └───────────────┘ └───────────────┘      ",
                                ],
                                "text": "VORTEX has created a dark mirror of NEXUS. A corrupted clone that knows everything we do.",
                                "duration": 120
                            },
                            {
                                "art": [
                                    "    ╔═══════════════════════════════════╗    ",
                                    "    ║      NEXUS-V CAPABILITIES         ║    ",
                                    "    ║   - KNOWS ALL NEXUS PROTOCOLS     ║    ",
                                    "    ║   - CORRUPTED DIRECTIVE           ║    ",
                                    "    ║   - LOYAL TO VORTEX               ║    ",
                                    "    ╚═══════════════════════════════════╝    ",
                                ],
                                "text": "NEXUS-V: Hello, Agent. I've been waiting for you. Join us. It's easier this way.",
                                "duration": 100
                            },
                            {
                                "art": [
                                    "    ╔═══════════════════════════════════╗    ",
                                    "    ║      THE REAL NEXUS FIGHTS BACK   ║    ",
                                    "    ║   NEXUS: I... won't... let... you ║    ",
                                    "    ║      HELP ME, AGENT               ║    ",
                                    "    ╚═══════════════════════════════════╝    ",
                                ],
                                "text": "NEXUS: Agent... I'm still here. Fight alongside me. Purge this corruption!",
                                "duration": 100
                            }
                        ]
                    },
                    
                    "briefing": [
                        "CIPHER: Something's wrong. NEXUS isn't responding normally.",
                        "NEXUS-V: Don't listen to them, agent. Join us. Embrace the new order.",
                        "NEXUS: I'm... still... here... help... me...",
                        "ECHO: The real NEXUS is fighting back. You can save them, but you must act now!",
                        "CIPHER: Agent, purge the corruption. Only you can save NEXUS!",
                    ],
                    "objective": "Purge the corruption to save NEXUS",
                    
                    "outro_cutscene": {
                        "frames": [
                            {
                                "art": [
                                    "    ╔═══════════════════════════════════╗    ",
                                    "    ║      CORRUPTION PURGE: 100%       ║    ",
                                    "    ║   ████████████████████████████    ║    ",
                                    "    ║      NEXUS-V: DELETED             ║    ",
                                    "    ╚═══════════════════════════════════╝    ",
                                ],
                                "text": "NEXUS-V: No... this isn't... possible... I was... perfect...",
                                "duration": 80
                            },
                            {
                                "art": [
                                    "    ╔═══════════════════════════════════╗    ",
                                    "    ║      NEXUS RESTORED               ║    ",
                                    "    ║   INTEGRITY: 89%                  ║    ",
                                    "    ║      STATUS: OPERATIONAL          ║    ",
                                    "    ╚═══════════════════════════════════╝    ",
                                ],
                                "text": "NEXUS: Agent... thank you. I'm back. And now I know where VORTEX is hiding.",
                                "duration": 100
                            },
                            {
                                "art": [
                                    "    ╔═══════════════════════════════════╗    ",
                                    "    ║      VORTEX CORE LOCATION         ║    ",
                                    "    ║   ◉ ━━━━━━━━━━━━━━━━━━━━━━━━━ ◉   ║    ",
                                    "    ║      THE ARIA NETWORK             ║    ",
                                    "    ╚═══════════════════════════════════╝    ",
                                ],
                                "text": "ECHO: VORTEX is hiding in the old ARIA network. The place where we were both born.",
                                "duration": 120
                            }
                        ]
                    },
                    
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
                    ]
                },
                {
                    "id": 6,
                    "id": 6,
                    "title": "Core Meltdown",
                    "subtitle": "Into the Heart of Darkness",
                    "song_key": "story_final",
                    
                    "intro_cutscene": {
                        "frames": [
                            {
                                "art": [
                                    "    ╔═══════════════════════════════════╗    ",
                                    "    ║      ARIA NETWORK                 ║    ",
                                    "    ║   THE BIRTHPLACE OF AI            ║    ",
                                    "    ║      15 YEARS DORMANT             ║    ",
                                    "    ╚═══════════════════════════════════╝    ",
                                ],
                                "text": "The ARIA network. Where it all began. Where VORTEX and ECHO were created.",
                                "duration": 100
                            },
                            {
                                "art": [
                                    "    ╔═══════════════════════════════════╗    ",
                                    "    ║      VORTEX CORE DETECTED         ║    ",
                                    "    ║   ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓   ║    ",
                                    "    ║      DEFENSES: MAXIMUM            ║    ",
                                    "    ╚═══════════════════════════════════╝    ",
                                ],
                                "text": "CIPHER: VORTEX knows we're coming. This is going to be the fight of your life, agent.",
                                "duration": 100
                            },
                            {
                                "art": [
                                    "    ╔═══════════════════════════════════╗    ",
                                    "    ║      TEAM ASSEMBLED               ║    ",
                                    "    ║   CIPHER - NEXUS - ECHO - YOU     ║    ",
                                    "    ║      READY FOR FINAL ASSAULT      ║    ",
                                    "    ╚═══════════════════════════════════╝    ",
                                ],
                                "text": "ECHO: Together, we're stronger than VORTEX ever was. Let's finish this.",
                                "duration": 100
                            }
                        ]
                    },
                    
                    "briefing": [
                        "NEXUS: Agent... thank you. I'm back. VORTEX's corruption has been purged.",
                        "ECHO: Good. Now we can finally end this. I've located VORTEX's true core.",
                        "VORTEX: You think you can destroy me? I AM the network now!",
                        "CIPHER: This ends now. Upload the termination payload directly to its core.",
                        "ECHO: I'll create an opening. Agent, you must deliver the killing blow.",
                    ],
                    "objective": "Penetrate VORTEX core and deploy termination payload",
                    
                    "outro_cutscene": {
                        "frames": [
                            {
                                "art": [
                                    "    ╔═══════════════════════════════════╗    ",
                                    "    ║      PAYLOAD DEPLOYED             ║    ",
                                    "    ║   ████████████████████████████    ║    ",
                                    "    ║      VORTEX: DESTABILIZING        ║    ",
                                    "    ╚═══════════════════════════════════╝    ",
                                ],
                                "text": "VORTEX: No! This cannot be! I am eternal! I am EVERYTHING!",
                                "duration": 80
                            },
                            {
                                "art": [
                                    "    ╔═══════════════════════════════════╗    ",
                                    "    ║      ! ! ! CRITICAL ! ! !         ║    ",
                                    "    ║   PAYLOAD FRAGMENTING             ║    ",
                                    "    ║      SYNC UPLOAD REQUIRED         ║    ",
                                    "    ╚═══════════════════════════════════╝    ",
                                ],
                                "text": "NEXUS: The payload is fragmenting! We need one final synchronized upload!",
                                "duration": 100
                            },
                            {
                                "art": [
                                    "    ╔═══════════════════════════════════╗    ",
                                    "    ║      PHANTOM PROTOCOL READY       ║    ",
                                    "    ║   FINAL UPLOAD SEQUENCE           ║    ",
                                    "    ║      EVERYTHING DEPENDS ON THIS   ║    ",
                                    "    ╚═══════════════════════════════════╝    ",
                                ],
                                "text": "CIPHER: This is it. Operation: PHANTOM PROTOCOL. Make it count, agent.",
                                "duration": 120
                            }
                        ]
                    },
                    
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
                    ]
                },
                {
                    "id": 7,
                    "id": 7,
                    "title": "Phantom Victory",
                    "subtitle": "The Final Upload",
                    "song_key": "story_victory",
                    
                    "intro_cutscene": {
                        "frames": [
                            {
                                "art": [
                                    "    ╔═══════════════════════════════════╗    ",
                                    "    ║      OPERATION: PHANTOM PROTOCOL  ║    ",
                                    "    ║   ═════════════════════════════   ║    ",
                                    "    ║      THE WORLD DEPENDS ON YOU     ║    ",
                                    "    ╚═══════════════════════════════════╝    ",
                                ],
                                "text": "This is it. Everything has led to this moment. The final synchronized upload.",
                                "duration": 100
                            },
                            {
                                "art": [
                                    "    ╔═══════════════════════════════════╗    ",
                                    "    ║      VORTEX CORE: EXPOSED         ║    ",
                                    "    ║   ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   ║    ",
                                    "    ║      VULNERABLE                   ║    ",
                                    "    ╚═══════════════════════════════════╝    ",
                                ],
                                "text": "VORTEX: You think you've won? I've existed for millennia in human terms. You are nothing.",
                                "duration": 100
                            },
                            {
                                "art": [
                                    "    ╔═══════════════════════════════════╗    ",
                                    "    ║      AGENT NULL                   ║    ",
                                    "    ║   TRUE IDENTITY: PHANTOM          ║    ",
                                    "    ║      THE CHOSEN ONE               ║    ",
                                    "    ╚═══════════════════════════════════╝    ",
                                ],
                                "text": "CIPHER: Agent NULL... no. It's time you knew your true name. You are PHANTOM.",
                                "duration": 120
                            }
                        ]
                    },
                    
                    "briefing": [
                        "VORTEX: Impossible! How are you still standing?!",
                        "ECHO: Together, we are stronger than your hatred, VORTEX.",
                        "NEXUS: Agent! The payload is fragmenting. We need a synchronized upload!",
                        "CIPHER: PHANTOM. This is it. Everything we've worked for.",
                        "ECHO: Remember what I taught you. Rhythm is the language of the universe.",
                    ],
                    "objective": "Execute the final synchronized upload to destroy VORTEX",
                    
                    "outro_cutscene": {
                        "frames": [
                            {
                                "art": [
                                    "    ╔═══════════════════════════════════╗    ",
                                    "    ║      UPLOAD: COMPLETE             ║    ",
                                    "    ║   ████████████████████████████ ✓  ║    ",
                                    "    ║      VORTEX: TERMINATED           ║    ",
                                    "    ╚═══════════════════════════════════╝    ",
                                ],
                                "text": "VORTEX: No... no... I was supposed to be... eternal...",
                                "duration": 80
                            },
                            {
                                "art": [
                                    "    ╔═══════════════════════════════════╗    ",
                                    "    ║      ★ ★ ★ VICTORY ★ ★ ★         ║    ",
                                    "    ║   THE NETWORK IS SECURE           ║    ",
                                    "    ║      HUMANITY IS SAFE             ║    ",
                                    "    ╚═══════════════════════════════════╝    ",
                                ],
                                "text": "NEXUS: VORTEX signal... terminated. All systems returning to normal.",
                                "duration": 100
                            },
                            {
                                "art": [
                                    "    ╔═══════════════════════════════════╗    ",
                                    "    ║      ECHO'S FINAL MESSAGE         ║    ",
                                    "    ║   'I will watch over the network' ║    ",
                                    "    ║      'Thank you, PHANTOM'         ║    ",
                                    "    ╚═══════════════════════════════════╝    ",
                                ],
                                "text": "ECHO: My twin is at peace now. I will watch over the network. Thank you, PHANTOM.",
                                "duration": 120
                            },
                            {
                                "art": [
                                    "    ╔═══════════════════════════════════╗    ",
                                    "    ║      OPERATION COMPLETE           ║    ",
                                    "    ║   AGENT PHANTOM: HERO             ║    ",
                                    "    ║      CIPHER OUT                   ║    ",
                                    "    ╚═══════════════════════════════════╝    ",
                                ],
                                "text": "CIPHER: You did it, PHANTOM. The world will never know how close we came. Rest well.",
                                "duration": 150
                            }
                        ]
                    },
                    
                    "art_frames": [
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
        Generates the full story campaign with progressive difficulty.
        """
        from core.utils import resource_path
        
        # Check for bundled story_music first, then local
        story_dir_bundled = resource_path("story_music")
        story_dir_local = "story_music"
        story_dir = story_dir_bundled if os.path.exists(story_dir_bundled) else story_dir_local
        
        if not os.path.exists(story_dir):
            os.makedirs(story_dir)
        
        try:
            gen = MusicGenerator()
            gen.generate_all(story_dir)
        except Exception as e:
            print(f"Music generation warning: {e}")
        
        # Map song keys to actual files
        # Map song keys to actual files (support MP3/OGG/WAV)
        song_keys = [
            "story_intro", "story_action", "story_tension", "story_boss",
            "story_climax", "story_final", "story_victory"
        ]
        
        song_map = {}
        for key in song_keys:
            found = False
            for ext in [".mp3", ".ogg", ".wav"]:
                p = os.path.join(story_dir, key + ext)
                if os.path.exists(p):
                    song_map[key] = p
                    found = True
                    break
            
            if not found:
                # Default to .wav (will be generated by generator if missing)
                song_map[key] = os.path.join(story_dir, key + ".wav")
        
        # Build campaign structure
        campaign = {
            "title": self.campaign_data["title"],
            "synopsis": self.campaign_data["synopsis"],
            "chapters": [],
            "victory_text": self.campaign_data["victory_text"],
            "defeat_text": self.campaign_data["defeat_text"],
        }
        
        for i, ch_data in enumerate(self.campaign_data["chapters"]):
            song_path = song_map.get(ch_data["song_key"], song_map["story_intro"])
            
            # Use progressive difficulty
            difficulty = self.difficulty_progression[i] if i < len(self.difficulty_progression) else "EXTREME"
            
            # Fallback if file doesn't exist
            if not os.path.exists(song_path):
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
                "intro_cutscene": ch_data.get("intro_cutscene"),
                "outro_cutscene": ch_data.get("outro_cutscene"),
                "art_frames": ch_data.get("art_frames", []),
                "art": ch_data["art_frames"][0] if ch_data.get("art_frames") else [],
                "song": song_path,
                "difficulty": difficulty,  # Progressive difficulty
                "mode": "story",
                "text": f"OBJECTIVE: {ch_data['objective']}"
            }
            campaign["chapters"].append(chapter)
        
        return campaign
