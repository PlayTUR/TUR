import numpy as np
import soundfile as sf
import os

def generate_techno_beat(filename="songs/test_beat.wav", duration=60, bpm=140):
    sr = 44100
    t = np.linspace(0, duration, int(sr * duration))
    
    # Bass Kick (every beat)
    beat_interval = 60 / bpm
    kick_freq = 50
    kick = np.sin(2 * np.pi * kick_freq * t) * np.exp(-10 * (t % beat_interval)) * 3.0
    
    # Hi-hat (every half beat)
    hat_interval = beat_interval / 2
    noise = np.random.uniform(-1, 1, len(t))
    hat_env = np.exp(-30 * (t % hat_interval))
    hat = noise * hat_env * 0.5
    
    # Melody (simple sine arpeggio)
    melody = np.zeros_like(t)
    notes = [440, 523, 659, 784] # A C E G
    note_duration = beat_interval / 2
    for i, note in enumerate(notes):
        # repeating pattern logic
        segment = (t % (note_duration * 4)) // note_duration
        mask = (segment == i)
        melody[mask] = np.sin(2 * np.pi * note * t[mask]) * 0.3
    
    audio = kick + hat + melody
    # Normalize
    audio = audio / np.max(np.abs(audio))
    
    if not os.path.exists("songs"):
        os.makedirs("songs")
        
    sf.write(filename, audio, sr)
    print(f"Generated {filename}")

if __name__ == "__main__":
    generate_techno_beat()
