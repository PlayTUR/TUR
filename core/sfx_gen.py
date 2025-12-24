import numpy as np
import scipy.io.wavfile as wavfile
import os
import random

def generate_sine_sweep(duration, start_freq, end_freq, sample_rate=44100):
    t = np.linspace(0, duration, int(sample_rate * duration))
    # Frequency sweep (Linear)
    # Phase is integral of freq: f(t) = start + (end-start)*t/dur
    # phi = start*t + 0.5*(end-start)*t^2/dur
    phase = 2 * np.pi * (start_freq * t + 0.5 * (end_freq - start_freq) * t**2 / duration)
    return np.sin(phase)

def apply_envelope(wave, duration, sample_rate=44100, attack=0.005, decay=0.1):
    t = np.linspace(0, duration, len(wave))
    envelope = np.ones_like(t)
    
    # Attack
    attack_samples = int(attack * sample_rate)
    envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
    
    # Decay (Exponential)
    decay_samples = len(wave) - attack_samples
    if decay_samples > 0:
        envelope[attack_samples:] = np.exp(-t[attack_samples:] * (1.0/decay))
        
    return wave * envelope

def generate_kick(sample_rate=44100):
    duration = 0.2
    # Deep Kick: 150Hz -> 40Hz
    kick = generate_sine_sweep(duration, 150, 40, sample_rate)
    kick = apply_envelope(kick, duration, sample_rate, attack=0.002, decay=0.08)
    
    # Add initial click (noise)
    noise_dur = 0.01
    noise = np.random.uniform(-1, 1, int(sample_rate * noise_dur)) * 0.5
    noise = apply_envelope(noise, noise_dur, sample_rate, attack=0.001, decay=0.005)
    
    # Pad noise
    noise_padded = np.zeros_like(kick)
    noise_padded[:len(noise)] = noise
    
    final = kick + noise_padded
    return final

def generate_perfect_click(sample_rate=44100):
    # Woodblock-ish: Sine 800Hz, very short
    duration = 0.05
    block = np.sin(2 * np.pi * 800 * np.linspace(0, duration, int(sample_rate * duration)))
    block = apply_envelope(block, duration, sample_rate, attack=0.001, decay=0.01)
    
    # Add Kick underbelly for "Deep"
    kick = generate_kick(sample_rate)
    # Mix: High kick + Click
    
    # Let's make Perfect = Kick + Click (Woodblock)
    # Hit = Just Kick (Softer)
    
    # Align lengths
    final = np.zeros_like(kick)
    final += kick * 0.8
    block_padded = np.zeros_like(kick)
    block_padded[:len(block)] = block * 0.5
    final += block_padded
    
    return final

def save_wav(filename, data, sample_rate=44100):
    # Normalize
    data = data / np.max(np.abs(data))
    # Convert to 16-bit PCM
    data_int = (data * 32767).astype(np.int16)
    wavfile.write(filename, sample_rate, data_int)
    print(f"Generated {filename}")

if __name__ == "__main__":
    if not os.path.exists("sfx"):
        os.makedirs("sfx")
        
    sr = 44100
    
    # 1. Hit Sound (Great): Deep Kick
    kick = generate_kick(sr)
    save_wav("sfx/sfx_hit.wav", kick, sr)
    
    # 2. Perfect Sound: Kick + Click (Sharper)
    perfect = generate_perfect_click(sr)
    save_wav("sfx/sfx_perfect.wav", perfect, sr)
    
    # 3. Miss: Low thud?
    miss = generate_sine_sweep(0.3, 100, 20, sr) * 0.3
    save_wav("sfx/sfx_miss.wav", miss, sr)
    
    print("SFX Generation Complete.")
