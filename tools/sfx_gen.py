import numpy as np
import scipy.io.wavfile as wav
import os
import random

SAMPLE_RATE = 44100
SFX_DIR = "sfx"

if not os.path.exists(SFX_DIR):
    os.makedirs(SFX_DIR)

def generate_triangle_wave(freq, duration, vol=0.5):
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    # Triangle wave: 2 * abs(2 * (t * freq - floor(t * freq + 0.5))) - 1
    # But usually abs(sawtooth) is easier: 
    # value = 2 * np.abs(2 * (t * freq - np.floor(t * freq + 0.5))) - 1
    # Let's stick to a simple mapping
    wave = 2 * np.abs(2 * (t * freq - np.floor(t * freq + 0.5))) - 1
    return wave * vol

def generate_square_wave(freq, duration, vol=0.5):
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    wave = np.sign(np.sin(2 * np.pi * freq * t))
    return wave * vol

def generate_noise(duration, vol=0.5):
    samples = int(SAMPLE_RATE * duration)
    return np.random.uniform(-1, 1, samples) * vol

def apply_envelope(wave, attack=0.01, decay=0.1, sustain_level=1.0, release=0.1):
    total_samples = len(wave)
    attack_samples = int(attack * SAMPLE_RATE)
    decay_samples = int(decay * SAMPLE_RATE) # Decay to sustain
    release_samples = int(release * SAMPLE_RATE)
    
    envelope = np.ones(total_samples)
    
    # Attack (0 -> 1)
    if attack_samples > 0:
        envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
    
    # Decay (1 -> Sustain)?? For simple SFX, we often just want Attack -> Decay to 0
    # If release is specified, we fade out the last X samples
    
    # Let's simplify: Attack -> Hold -> Release
    hold_samples = total_samples - attack_samples - release_samples
    if hold_samples < 0:
        # Overlap, shrink release
        release_samples = total_samples - attack_samples
        hold_samples = 0
    
    if release_samples > 0:
        envelope[-release_samples:] = np.linspace(1, 0, release_samples)
         
    return wave * envelope

def save_wav(filename, wave):
    # Normalize
    if np.max(np.abs(wave)) > 0:
        wave = wave / np.max(np.abs(wave))
    # Convert to 16-bit PCM
    data = (wave * 32767).astype(np.int16)
    wav.write(os.path.join(SFX_DIR, filename), SAMPLE_RATE, data)
    print(f"Generated {filename}")

def main():
    # 1. Selection / Blip (Redesigned)
    # Crisper, lighter "tick" using Triangle wave
    # High pitch, very short
    bg = generate_triangle_wave(880, 0.08, 0.4)
    bg = apply_envelope(bg, attack=0.005, release=0.07) # Almost all decay
    save_wav("sfx_blip.wav", bg)

    # 2. Accept / Click (Redesigned)
    # Tech Chord: A4 (440) + E5 (660) - Perfect 5th
    # Using Triangle for a cleaner, modern sound
    wave1 = generate_triangle_wave(440, 0.1, 0.4)
    wave2 = generate_triangle_wave(660, 0.1, 0.4)
    # Mix
    accept = wave1 + wave2
    accept = apply_envelope(accept, attack=0.005, release=0.08)
    save_wav("sfx_accept.wav", accept)

    # 3. Back / Cancel
    # Descending slide
    t = np.linspace(0, 0.2, int(SAMPLE_RATE * 0.2), endpoint=False)
    freqs = np.linspace(400, 150, len(t))
    phases = 2 * np.pi * np.cumsum(freqs) / SAMPLE_RATE
    cancel = np.sign(np.sin(phases)) * 0.2 # Reduced volume
    cancel = apply_envelope(cancel, 0.01, release=0.1)
    save_wav("sfx_back.wav", cancel)

    # 4. Startup / Boot (Smoother fade)
    duration = 2.5 # Longer tail
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    
    # Bass sweep
    freqs = np.logspace(np.log10(55), np.log10(110), len(t))
    bass_phases = 2 * np.pi * np.cumsum(freqs) / SAMPLE_RATE
    bass = np.sign(np.sin(bass_phases)) * 0.3
    # Bass fade out
    bass = apply_envelope(bass, attack=0.1, release=1.0)
    
    # Arpeggio
    arp_len = 0.1
    c_chord = [523.25, 659.25, 783.99, 1046.50]
    chord_wave = np.array([])
    for f in c_chord:
        w = generate_square_wave(f, arp_len, 0.2)
        w = apply_envelope(w, 0.01, release=0.02) # Short individual notes
        chord_wave = np.concatenate([chord_wave, w])
        
    # Final chord hold
    hold_len = 1.5
    final_f = c_chord
    final_wave = np.zeros(int(SAMPLE_RATE * hold_len))
    for f in c_chord:
        w = generate_square_wave(f, hold_len, 0.1)
        final_wave += w
    
    # Fade out the final chord smoothly
    final_wave = apply_envelope(final_wave, attack=0.1, release=1.0)
    
    chord_wave = np.concatenate([chord_wave, final_wave])
         
    # Combine
    pad_len = max(len(bass), len(chord_wave))
    final_mix = np.zeros(pad_len)
    final_mix[:len(bass)] += bass
    # Start chord slightly later
    offset = int(SAMPLE_RATE * 0.5)
    if offset + len(chord_wave) > pad_len:
        # Extend mix
        final_mix = np.concatenate([final_mix, np.zeros(offset + len(chord_wave) - pad_len)])
    
    final_mix[offset:offset+len(chord_wave)] += chord_wave
    
    save_wav("sfx_boot.wav", final_mix)

    # 5. Type (Short click)
    click = generate_noise(0.03, 0.3)
    click = apply_envelope(click, 0.001, release=0.02)
    save_wav("sfx_type.wav", click)
    
    # 6. Error (Buzzer)
    buzz_dur = 0.3
    buzz_t = np.linspace(0, buzz_dur, int(SAMPLE_RATE * buzz_dur))
    buzz = np.sign(np.sin(2 * np.pi * 150 * buzz_t)) 
    buzz += np.sign(np.sin(2 * np.pi * 155 * buzz_t)) 
    buzz = apply_envelope(buzz, 0.02, release=0.15)
    save_wav("sfx_error.wav", buzz)
    
    # 7. Success
    s_dur = 0.4
    s_wave = np.array([])
    for f in [523, 659, 783, 1046, 1318, 1568]:
        w = generate_triangle_wave(f, 0.08, 0.3)
        w = apply_envelope(w, 0.01, release=0.04)
        s_wave = np.concatenate([s_wave, w])
    save_wav("sfx_success.wav", s_wave)

if __name__ == "__main__":
    main()
