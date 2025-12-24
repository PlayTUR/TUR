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
    generate_great_sound(os.path.join(output_dir, "sfx_great.wav"), sr)
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
    """
    Premium 3-layer hit sound:
    1. Low kick punch (pitch-sliding sine)
    2. Mid click transient (short burst)
    3. High snap/attack (noise + high freq)
    """
    # Force regenerate
    if os.path.exists(path):
        os.remove(path)
    
    duration = 0.15
    samples = int(sr * duration)
    data = []
    
    for i in range(samples):
        t = i / sr
        
        # Layer 1: Kick punch (pitch slide 200Hz -> 40Hz)
        kick_env = math.exp(-t * 35)
        kick_freq = 200 * math.exp(-t * 25) + 40
        kick = 0.7 * math.sin(2 * math.pi * kick_freq * t) * kick_env
        
        # Layer 2: Mid click transient (800Hz, very short)
        click_env = math.exp(-t * 150)
        click = 0.4 * math.sin(2 * math.pi * 800 * t) * click_env
        click += 0.2 * math.sin(2 * math.pi * 1200 * t) * click_env
        
        # Layer 3: High snap (noise + 2kHz, ultra short)
        snap_env = math.exp(-t * 200)
        snap = 0.25 * (random.random() * 2 - 1) * snap_env
        snap += 0.15 * math.sin(2 * math.pi * 2000 * t) * snap_env
        
        # Combine layers
        val = kick + click + snap
        
        # Soft clip for warmth
        val = math.tanh(val * 1.2)
        
        # 8-bit crunch
        val = bit_crush(val, 10)
        
        data.append(int(val * 32767 * 0.8))
    
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
    """
    Premium perfect hit sound:
    - Sparkle chime with harmonics
    - Shimmering overtones
    - Satisfying high-end sparkle
    """
    # Force regenerate
    if os.path.exists(path):
        os.remove(path)
    
    duration = 0.25
    samples = int(sr * duration)
    data = []
    
    # Harmonic series based on A5 (880Hz)
    base_freq = 880
    harmonics = [1.0, 2.0, 3.0, 4.0, 5.0]  # Fundamental + overtones
    harmonic_amps = [0.4, 0.25, 0.15, 0.1, 0.08]
    
    for i in range(samples):
        t = i / sr
        
        # Main envelope with quick attack
        attack = min(1.0, t / 0.005)  # 5ms attack
        decay = math.exp(-t * 12)
        env = attack * decay
        
        val = 0
        
        # Add harmonics with slight detuning for shimmer
        for h, amp in zip(harmonics, harmonic_amps):
            freq = base_freq * h
            # Slight vibrato for shimmer
            vibrato = 1.0 + 0.002 * math.sin(t * 40)
            val += amp * math.sin(2 * math.pi * freq * vibrato * t) * env
        
        # High sparkle layer (noise + very high freq)
        sparkle_env = math.exp(-t * 30)
        sparkle = 0.08 * (random.random() * 2 - 1) * sparkle_env
        sparkle += 0.1 * math.sin(2 * math.pi * 3520 * t) * sparkle_env  # A7
        
        val += sparkle
        
        # Soft clip
        val = math.tanh(val * 1.1)
        
        data.append(int(val * 32767 * 0.75))
    
    write_wav(path, data, sr)


def generate_great_sound(path, sr=44100):
    """
    Deep, punchy great hit sound:
    - Lower frequency than perfect (satisfying thump)
    - More body and punch
    - Distinct mid-range tone
    """
    # Force regenerate
    if os.path.exists(path):
        os.remove(path)
    
    duration = 0.18
    samples = int(sr * duration)
    data = []
    
    for i in range(samples):
        t = i / sr
        
        # Layer 1: Deep bass thump (60-100Hz, pitch slide)
        thump_env = math.exp(-t * 25)
        thump_freq = 100 * math.exp(-t * 10) + 60
        thump = 0.6 * math.sin(2 * math.pi * thump_freq * t) * thump_env
        
        # Layer 2: Mid punch (300-400Hz)
        punch_env = math.exp(-t * 40)
        punch = 0.35 * math.sin(2 * math.pi * 350 * t) * punch_env
        punch += 0.2 * math.sin(2 * math.pi * 500 * t) * punch_env
        
        # Layer 3: Light click (subtle high end)
        click_env = math.exp(-t * 80)
        click = 0.15 * math.sin(2 * math.pi * 1200 * t) * click_env
        
        # Combine
        val = thump + punch + click
        
        # Soft saturation for warmth
        val = math.tanh(val * 1.3)
        
        data.append(int(val * 32767 * 0.85))
    
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

