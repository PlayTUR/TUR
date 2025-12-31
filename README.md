# TUR (The Unnamed Rhythm Game)

A community-driven, open-source rhythm game built with Python and Pygame.
**Repository:** [https://github.com/PlayTUR/TUR](https://github.com/PlayTUR/TUR)

## Features
- 🎵 **4-Key Rhythm Gameplay**: Classic vertical scrolling rhythm action.
- 🌐 **Multiplayer**: Play with friends via LAN or Online (Tailscale).
- 🛠️ **Editor**: Built-in beatmap editor to create your own charts.
- 🎨 **Theming**: Fully customizable visuals and UI.

## Installation

1. **Install Python 3.10+**
2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the Game:**
   ```bash
   python main.py
   ```

## Multiplayer Guide

### 1. LAN Mode (Local WiFi)
The easiest way to play with someone in the same room.
- **Host**: Go to **Multiplayer > LAN > HOST GAME**.
- **Join**: Go to **Multiplayer > LAN > JOIN GAME**. The server should appear automatically.

### 2. Online Mode (Tailscale)
Play with friends anywhere in the world using [Tailscale](https://tailscale.com) (a free mesh VPN).

**Setup:**
1. Both players install Tailscale and join the same "Tailnet" (invite your friend).
2. **Host**: 
   - Go to **Multiplayer > ONLINE > HOST GAME**.
   - Share the **Tailscale IP** displayed on screen (e.g., `100.x.x.x:1337`).
3. **Join**:
   - Go to **Multiplayer > ONLINE > JOIN GAME**.
   - Select **DIRECT CONNECT** and enter the Host's IP.

## Controls
- **D F J K**: Hit notes (rebindable in settings)
- **Arrows**: Navigation
- **ENTER**: Select / Chat
- **ESC**: Back / Pause

## Credits
Maintained by **PlayTUR**.
Original code by Wyind.
