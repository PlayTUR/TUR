import random
import wave
import struct
import math
import os

class MusicGenerator:
    def __init__(self, sample_rate=44100):
        self.sr = sample_rate
        self.max_amp = 32767 * 0.5

    def generate_all(self, output_dir="songs"):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        tracks = [
            {"name": "story_intro.wav", "bpm": 120, "scale": [261.63, 329.63, 392.00, 523.25]}, # C Major
            {"name": "story_action.wav", "bpm": 150, "scale": [220.00, 261.63, 311.13, 329.63, 440.00]}, # A Minor / Phrygianish
            {"name": "story_boss.wav", "bpm": 180, "scale": [146.83, 174.61, 220.00, 261.63, 311.13]} # D Minor Dark
        ]
        
        generated = []
        for t in tracks:
            path = os.path.join(output_dir, t["name"])
            if not os.path.exists(path):
                print(f"Generating {t['name']}...")
                self.write_track(path, t["bpm"], t["scale"])
                generated.append(t["name"])
        
        return generated

    def write_track(self, filename, bpm, scale, duration=60):
        # 16-bit Mono WAV
        n_samples = int(duration * self.sr)
        
        # Sequencer Grid
        spb = 60.0 / bpm
        samples_per_beat = int(self.sr * spb)
        
        # Buffer
        data = bytearray()
        
        # State
        phase = 0.0
        
        # Simple Composition: 4 Bar loop repeated
        # 1 Bar = 4 Beats
        total_beats = int(duration * bpm / 60)
        
        # Generate Note Sequence
        melody = []
        for _ in range(16): # 16 beat loop
            if random.random() < 0.7:
                melody.append(random.choice(scale))
            else:
                melody.append(0)
                
        # Bass Sequence
        bass_note = scale[0] / 2
        
        for i in range(n_samples):
            # Time
            t = i / self.sr
            
            # Current Beat
            cur_beat = (i / samples_per_beat)
            beat_idx = int(cur_beat) % 16
            
            val = 0.0
            
            # 1. Kick (Every Beat)
            local_t = (i % samples_per_beat) / self.sr
            if local_t < 0.2:
                # Sine sweep
                freq = 150 * (1.0 - (local_t / 0.2))
                val += 0.6 * math.sin(2 * math.pi * freq * local_t)
            
            # 2. Hi-hat (Every half beat)
            hat_t = (i % (samples_per_beat // 2)) / self.sr
            if hat_t < 0.05:
                # Noise
                val += 0.3 * (random.random() * 2 - 1)
                
            # 3. Melody
            note_freq = melody[beat_idx]
            if note_freq > 0:
                # Square wave
                period = self.sr / note_freq
                # Enveloped
                env = max(0, 1.0 - (local_t * 2)) # Decay
                
                # Square
                sq_wave = 1.0 if (i % period) < (period / 2) else -1.0
                val += 0.4 * sq_wave * env
                
            # Clip
            val = max(-1.0, min(1.0, val))
            
            # Convert to 16bit int
            i_val = int(val * self.max_amp)
            data.extend(struct.pack('<h', i_val))
            
        with wave.open(filename, 'w') as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(self.sr)
            f.writeframes(data)

    def generate_sfx(self, filename, freq, duration=0.1, wave_type="SQUARE", slide=0.0):
        # Create a simple tone
        n_samples = int(duration * self.sr)
        data = bytearray()
        
        phase = 0.0
        
        for i in range(n_samples):
            t = i / self.sr
            
            # Frequency Slide
            cur_freq = freq + (slide * t)
            if cur_freq < 20: cur_freq = 20
            
            # Phase accumulation for variable freq
            phase += cur_freq / self.sr
            
            val = 0.0
            if wave_type == "SQUARE":
                val = 1.0 if (phase % 1.0) < 0.5 else -1.0
            elif wave_type == "SINE":
                val = math.sin(2 * math.pi * phase)
            elif wave_type == "SAW":
                val = 2.0 * (phase % 1.0) - 1.0
            elif wave_type == "NOISE":
                val = random.uniform(-1, 1)
            
            # Simple Attack/Release Envelope
            env = 1.0
            if t < 0.01: env = t / 0.01
            elif t > duration - 0.05: env = (duration - t) / 0.05
            env = max(0.0, min(1.0, env))
            
            val *= env
            
            i_val = int(val * self.max_amp * 0.5) # Lower vol for SFX
            data.extend(struct.pack('<h', i_val))
            
        with wave.open(filename, 'w') as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(self.sr)
            f.writeframes(data)
