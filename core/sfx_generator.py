"""
Sound Effect Generator for TUR
Generates procedural hit sounds, miss sounds, combos, boot sounds, and menu sounds.
"""

import wave
import struct
import math
import os
import random


def generate_sfx(output_dir="sfx"):
    """Generate all game sound effects"""
    os.makedirs(output_dir, exist_ok=True)
    
    sr = 44100
    
    # Hit sounds
    generate_hit_sound(os.path.join(output_dir, "sfx_hit.wav"), sr)
    generate_miss_sound(os.path.join(output_dir, "sfx_miss.wav"), sr)
    generate_perfect_sound(os.path.join(output_dir, "sfx_perfect.wav"), sr)
    generate_combo_sound(os.path.join(output_dir, "sfx_combo.wav"), sr)
    
    # Boot sounds
    generate_startup_beep(os.path.join(output_dir, "sfx_startup.wav"), sr)
    generate_tick_sound(os.path.join(output_dir, "sfx_tick.wav"), sr)
    generate_success_chime(os.path.join(output_dir, "sfx_chime.wav"), sr)
    generate_warning_sound(os.path.join(output_dir, "sfx_warning.wav"), sr)
    
    # Menu/Navigation sounds
    generate_blip_sound(os.path.join(output_dir, "sfx_blip.wav"), sr)
    generate_accept_sound(os.path.join(output_dir, "sfx_accept.wav"), sr)
    generate_back_sound(os.path.join(output_dir, "sfx_back.wav"), sr)
    generate_error_sound(os.path.join(output_dir, "sfx_error.wav"), sr)
    
    # Multiplayer sounds
    generate_search_sound(os.path.join(output_dir, "sfx_search.wav"), sr)
    generate_connect_sound(os.path.join(output_dir, "sfx_connect.wav"), sr)
    generate_disconnect_sound(os.path.join(output_dir, "sfx_disconnect.wav"), sr)
    
    print("All sounds generated!")


def generate_startup_beep(path, sr=44100):
    """Classic BIOS beep sound"""
    if os.path.exists(path):
        return
    
    duration = 0.3
    samples = int(sr * duration)
    data = []
    
    for i in range(samples):
        t = i / sr
        # Quick attack, sustain, quick release
        if t < 0.02:
            env = t / 0.02
        elif t > duration - 0.05:
            env = (duration - t) / 0.05
        else:
            env = 1.0
        
        # Square-ish wave for retro feel
        val = 0.6 * math.sin(2 * math.pi * 800 * t) * env
        val += 0.2 * math.sin(2 * math.pi * 1600 * t) * env
        
        data.append(int(val * 32767 * 0.5))
    
    write_wav(path, data, sr)


def generate_tick_sound(path, sr=44100):
    """Short tick for loading steps"""
    if os.path.exists(path):
        return
    
    duration = 0.05
    samples = int(sr * duration)
    data = []
    
    for i in range(samples):
        t = i / sr
        env = math.exp(-t * 80)
        
        val = 0.8 * math.sin(2 * math.pi * 2000 * t) * env
        val += 0.2 * (random.random() * 2 - 1) * env
        
        data.append(int(val * 32767 * 0.4))
    
    write_wav(path, data, sr)


def generate_success_chime(path, sr=44100):
    """Pleasing success sound with harmony"""
    if os.path.exists(path):
        return
    
    duration = 0.5
    samples = int(sr * duration)
    data = []
    
    # C major chord progression feel
    freqs = [523.25, 659.25, 783.99]  # C5, E5, G5
    
    for i in range(samples):
        t = i / sr
        env = math.exp(-t * 5)
        
        val = 0
        for j, f in enumerate(freqs):
            delay = j * 0.05
            if t > delay:
                local_t = t - delay
                local_env = math.exp(-local_t * 6)
                val += 0.3 * math.sin(2 * math.pi * f * local_t) * local_env
        
        data.append(int(val * 32767 * 0.6))
    
    write_wav(path, data, sr)


def generate_warning_sound(path, sr=44100):
    """Alert/error buzz"""
    if os.path.exists(path):
        return
    
    duration = 0.2
    samples = int(sr * duration)
    data = []
    
    for i in range(samples):
        t = i / sr
        env = 1.0 if t < 0.15 else (0.2 - t) / 0.05
        env = max(0, env)
        
        # Harsh buzzy tone
        val = 0.5 * math.sin(2 * math.pi * 200 * t) * env
        val += 0.3 * math.sin(2 * math.pi * 400 * t) * env
        val += 0.2 * (random.random() * 2 - 1) * env
        
        data.append(int(val * 32767 * 0.6))
    
    write_wav(path, data, sr)


def generate_hit_sound(path, sr=44100):
    """Deep 8-bit drum hit sound with punch"""
    if os.path.exists(path):
        os.remove(path) # Force recreate
    
    duration = 0.12 # Slightly longer
    samples = int(sr * duration)
    data = []
    
    for i in range(samples):
        t = i / sr
        # Punch Envelope
        env = math.exp(-t * 40)
        
        # 1. Low Kick Punch (Pitch slide 150Hz -> 50Hz)
        freq = 150 * math.exp(-t * 20)
        kick = 0.8 * math.sin(2 * math.pi * freq * t) * env
        
        # 2. 8-Bit Noise Snap
        noise = (random.random() * 2 - 1) * math.exp(-t * 100)
        noise = bit_crush(noise, 4) # Very crunchy
        
        # Combine
        val = kick + 0.3 * noise
        val = bit_crush(val, 8) # Overall 8-bit feel
        
        data.append(int(val * 32767 * 0.7))
    
    write_wav(path, data, sr)


def generate_miss_sound(path, sr=44100):
    """Low thud/buzz for miss"""
    if os.path.exists(path):
        return
    
    duration = 0.15
    samples = int(sr * duration)
    data = []
    
    for i in range(samples):
        t = i / sr
        env = math.exp(-t * 20)
        
        # Low frequency buzz
        val = 0.6 * math.sin(2 * math.pi * 80 * t) * env
        val += 0.4 * math.sin(2 * math.pi * 120 * t) * env
        
        data.append(int(val * 32767 * 0.6))
    
    write_wav(path, data, sr)


def generate_perfect_sound(path, sr=44100):
    """Sparkle/chime for perfect hit"""
    if os.path.exists(path):
        return
    
    duration = 0.2
    samples = int(sr * duration)
    data = []
    
    for i in range(samples):
        t = i / sr
        env = math.exp(-t * 15)
        
        # High harmonics
        val = 0.5 * math.sin(2 * math.pi * 880 * t) * env
        val += 0.3 * math.sin(2 * math.pi * 1320 * t) * env
        val += 0.2 * math.sin(2 * math.pi * 1760 * t) * env
        
        data.append(int(val * 32767 * 0.7))
    
    write_wav(path, data, sr)


def generate_combo_sound(path, sr=44100):
    """Rising tone for combo milestone"""
    if os.path.exists(path):
        return
    
    duration = 0.25
    samples = int(sr * duration)
    data = []
    
    for i in range(samples):
        t = i / sr
        env = math.exp(-t * 8)
        
        freq = 400 + (t / duration) * 400
        val = 0.7 * math.sin(2 * math.pi * freq * t) * env
        val += 0.3 * math.sin(2 * math.pi * (freq * 1.5) * t) * env
        
        data.append(int(val * 32767 * 0.6))
    
    write_wav(path, data, sr)


def square_wave(t, freq):
    """Generate square wave value (-1 to 1)"""
    return 1.0 if (t * freq) % 1.0 < 0.5 else -1.0


def bit_crush(val, bits=8):
    """Reduce bit depth for 8-bit sound"""
    levels = 2 ** bits
    return round(val * levels) / levels


def generate_blip_sound(path, sr=44100):
    """Short 8-bit blip for menu navigation"""
    if os.path.exists(path):
        return
    
    duration = 0.05
    samples = int(sr * duration)
    data = []
    
    for i in range(samples):
        t = i / sr
        env = math.exp(-t * 80)
        val = 0.7 * square_wave(t, 800) * env
        val = bit_crush(val, 6)
        data.append(int(val * 32767 * 0.4))
    
    write_wav(path, data, sr)


def generate_accept_sound(path, sr=44100):
    """8-bit confirm - rising arpeggio"""
    if os.path.exists(path):
        return
    
    duration = 0.12
    samples = int(sr * duration)
    data = []
    
    # 3-note arpeggio: C-E-G
    notes = [523, 659, 784]
    note_dur = duration / 3
    
    for i in range(samples):
        t = i / sr
        note_idx = min(2, int(t / note_dur))
        freq = notes[note_idx]
        local_t = t - note_idx * note_dur
        env = math.exp(-local_t * 30)
        val = 0.6 * square_wave(t, freq) * env
        val = bit_crush(val, 6)
        data.append(int(val * 32767 * 0.4))
    
    write_wav(path, data, sr)


def generate_back_sound(path, sr=44100):
    """8-bit cancel - falling tone"""
    if os.path.exists(path):
        return
    
    duration = 0.08
    samples = int(sr * duration)
    data = []
    
    for i in range(samples):
        t = i / sr
        env = math.exp(-t * 40)
        freq = 600 - t * 400
        val = 0.5 * square_wave(t, freq) * env
        val = bit_crush(val, 6)
        data.append(int(val * 32767 * 0.4))
    
    write_wav(path, data, sr)


def generate_error_sound(path, sr=44100):
    """Error buzz"""
    if os.path.exists(path):
        return
    
    duration = 0.2
    samples = int(sr * duration)
    data = []
    
    for i in range(samples):
        t = i / sr
        env = 1.0 if t < 0.15 else max(0, (0.2 - t) / 0.05)
        val = 0.4 * math.sin(2 * math.pi * 150 * t) * env
        val += 0.3 * math.sin(2 * math.pi * 100 * t) * env
        data.append(int(val * 32767 * 0.6))
    
    write_wav(path, data, sr)


def generate_search_sound(path, sr=44100):
    """Searching/scanning sound - pulsing"""
    if os.path.exists(path):
        return
    
    duration = 0.5
    samples = int(sr * duration)
    data = []
    
    for i in range(samples):
        t = i / sr
        pulse = (1 + math.sin(t * 30)) / 2
        env = pulse * math.exp(-t * 3)
        val = 0.5 * math.sin(2 * math.pi * 800 * t) * env
        data.append(int(val * 32767 * 0.4))
    
    write_wav(path, data, sr)


def generate_connect_sound(path, sr=44100):
    """Connection success - harmonious rising chord"""
    if os.path.exists(path):
        return
    
    duration = 0.4
    samples = int(sr * duration)
    data = []
    
    freqs = [440, 550, 660]  # A, C#, E (A major)
    
    for i in range(samples):
        t = i / sr
        env = math.exp(-t * 5)
        val = 0
        for j, f in enumerate(freqs):
            delay = j * 0.08
            if t > delay:
                local_env = math.exp(-(t - delay) * 6)
                val += 0.25 * math.sin(2 * math.pi * f * (t - delay)) * local_env
        data.append(int(val * 32767 * 0.7))
    
    write_wav(path, data, sr)


def generate_disconnect_sound(path, sr=44100):
    """Disconnect - falling dissonant"""
    if os.path.exists(path):
        return
    
    duration = 0.3
    samples = int(sr * duration)
    data = []
    
    for i in range(samples):
        t = i / sr
        env = math.exp(-t * 8)
        freq = 600 - t * 400
        val = 0.5 * math.sin(2 * math.pi * freq * t) * env
        val += 0.3 * math.sin(2 * math.pi * (freq * 0.5) * t) * env
        data.append(int(val * 32767 * 0.5))
    
    write_wav(path, data, sr)


def write_wav(path, data, sr):
    """Write samples to WAV file"""
    with wave.open(path, 'w') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sr)
        for sample in data:
            f.writeframes(struct.pack('<h', max(-32768, min(32767, sample))))


if __name__ == "__main__":
    generate_sfx()
    print("Done!")

