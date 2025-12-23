#!/usr/bin/env python3
"""
Advanced Procedural Music Generator for TUR
Generates synthwave/chiptune tracks with proper song structure,
chord progressions, arpeggios, and multiple instrument layers.
"""

import wave
import struct
import math
import random
import os

class AdvancedMusicGenerator:
    def __init__(self, sample_rate=44100):
        self.sr = sample_rate
        self.max_amp = 32767 * 0.7
        
        # Musical scales (frequencies in Hz)
        self.scales = {
            'C_MAJOR': [261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88],
            'A_MINOR': [220.00, 246.94, 261.63, 293.66, 329.63, 349.23, 392.00],
            'D_MINOR': [293.66, 329.63, 349.23, 392.00, 440.00, 466.16, 523.25],
            'E_MINOR': [329.63, 369.99, 392.00, 440.00, 493.88, 523.25, 587.33],
            'F_LYDIAN': [349.23, 392.00, 440.00, 493.88, 523.25, 587.33, 659.26],
        }
        
        # Chord progressions (scale degree indices, 0-indexed)
        self.progressions = {
            'pop': [(0, 3, 4, 0), (0, 4, 5, 3)],
            'dark': [(0, 5, 3, 4), (0, 2, 5, 4)],
            'epic': [(0, 3, 4, 5), (5, 4, 3, 0)],
            'chill': [(0, 4, 1, 5), (0, 3, 4, 3)],
        }

    def get_frequency(self, scale_name, degree, octave_offset=0):
        """Get frequency from scale degree with octave offset"""
        scale = self.scales.get(scale_name, self.scales['C_MAJOR'])
        freq = scale[degree % len(scale)]
        return freq * (2 ** octave_offset)

    def envelope(self, t, attack=0.02, decay=0.1, sustain=0.7, release=0.2, duration=1.0):
        """ADSR envelope"""
        if t < attack:
            return t / attack
        elif t < attack + decay:
            return 1.0 - (1.0 - sustain) * ((t - attack) / decay)
        elif t < duration - release:
            return sustain
        else:
            return sustain * (1.0 - (t - (duration - release)) / release)

    def oscillator(self, phase, wave_type='square'):
        """Generate oscillator sample"""
        p = phase % 1.0
        if wave_type == 'square':
            return 1.0 if p < 0.5 else -1.0
        elif wave_type == 'saw':
            return 2.0 * p - 1.0
        elif wave_type == 'sine':
            return math.sin(2 * math.pi * p)
        elif wave_type == 'triangle':
            return 4.0 * abs(p - 0.5) - 1.0
        elif wave_type == 'pulse25':
            return 1.0 if p < 0.25 else -1.0
        elif wave_type == 'noise':
            return random.uniform(-1, 1)
        return 0.0

    def generate_kick(self, duration=0.2):
        """Generate a punchy kick drum"""
        samples = []
        n = int(duration * self.sr)
        for i in range(n):
            t = i / self.sr
            # Pitch envelope: start high, drop quickly
            freq = 150 * math.exp(-t * 20) + 50
            phase = freq * t
            # Body: sine with quick decay
            body = math.sin(2 * math.pi * phase) * math.exp(-t * 8)
            # Click: noise transient
            click = random.uniform(-1, 1) * math.exp(-t * 100) * 0.3
            samples.append((body + click) * 0.9)
        return samples

    def generate_snare(self, duration=0.15):
        """Generate a snappy snare"""
        samples = []
        n = int(duration * self.sr)
        for i in range(n):
            t = i / self.sr
            # Body: sine at ~180Hz
            body = math.sin(2 * math.pi * 180 * t) * math.exp(-t * 15) * 0.5
            # Noise burst
            noise = random.uniform(-1, 1) * math.exp(-t * 20) * 0.7
            samples.append(body + noise)
        return samples

    def generate_hihat(self, duration=0.05, open_hat=False):
        """Generate hi-hat"""
        samples = []
        decay = 3 if open_hat else 25
        n = int(duration * self.sr)
        for i in range(n):
            t = i / self.sr
            noise = random.uniform(-1, 1) * math.exp(-t * decay)
            # High-pass feel via mixing with sine
            hp = math.sin(2 * math.pi * 8000 * t) * 0.3
            samples.append((noise * 0.7 + hp * noise) * 0.4)
        return samples

    def generate_bass_note(self, freq, duration=0.5):
        """Generate a thick bass note"""
        samples = []
        n = int(duration * self.sr)
        phase = 0.0
        for i in range(n):
            t = i / self.sr
            phase += freq / self.sr
            # Mix saw and square for thickness
            saw = self.oscillator(phase, 'saw')
            sq = self.oscillator(phase * 0.5, 'square')  # Octave down
            env = self.envelope(t, 0.01, 0.1, 0.8, 0.1, duration)
            sample = (saw * 0.5 + sq * 0.5) * env * 0.6
            samples.append(sample)
        return samples

    def generate_lead_note(self, freq, duration=0.25, wave='pulse25'):
        """Generate a lead synth note"""
        samples = []
        n = int(duration * self.sr)
        phase = 0.0
        for i in range(n):
            t = i / self.sr
            # Slight vibrato
            vibrato = 1.0 + 0.02 * math.sin(2 * math.pi * 5 * t)
            phase += (freq * vibrato) / self.sr
            osc = self.oscillator(phase, wave)
            env = self.envelope(t, 0.02, 0.1, 0.6, 0.15, duration)
            samples.append(osc * env * 0.4)
        return samples

    def generate_arpeggio(self, freqs, duration=1.0, note_length=0.125):
        """Generate an arpeggio pattern"""
        samples = [0.0] * int(duration * self.sr)
        notes_per_cycle = len(freqs)
        note_samples = int(note_length * self.sr)
        
        i = 0
        note_idx = 0
        while i < len(samples):
            freq = freqs[note_idx % notes_per_cycle]
            note = self.generate_lead_note(freq, note_length, 'triangle')
            for j, s in enumerate(note):
                if i + j < len(samples):
                    samples[i + j] += s * 0.5
            i += note_samples
            note_idx += 1
        return samples

    def generate_pad(self, freqs, duration=2.0):
        """Generate a warm pad chord"""
        samples = [0.0] * int(duration * self.sr)
        for freq in freqs:
            phase = random.random()  # Random phase for thickness
            for i in range(len(samples)):
                t = i / self.sr
                phase += freq / self.sr
                # Slow attack, long sustain
                env = self.envelope(t, 0.5, 0.3, 0.6, 0.5, duration)
                # Filtered saw approximation
                osc = self.oscillator(phase, 'sine')
                osc += 0.3 * self.oscillator(phase * 2, 'sine')
                samples[i] += osc * env * 0.15
        return samples

    def mix_at(self, main_buffer, source, start_sample):
        """Mix source into main buffer at given position"""
        for i, s in enumerate(source):
            pos = start_sample + i
            if pos < len(main_buffer):
                main_buffer[pos] += s

    def generate_track(self, name, bpm, scale_name, progression_type, duration=90, 
                       style='synthwave'):
        """Generate a complete track"""
        print(f"Generating: {name} ({bpm} BPM, {scale_name}, {style})")
        
        n_samples = int(duration * self.sr)
        buffer = [0.0] * n_samples
        
        spb = 60.0 / bpm  # Seconds per beat
        samples_per_beat = int(spb * self.sr)
        total_beats = int(duration / spb)
        
        scale = self.scales[scale_name]
        progression = random.choice(self.progressions[progression_type])
        
        # Generate patterns
        for beat in range(total_beats):
            beat_start = beat * samples_per_beat
            bar = beat // 4
            beat_in_bar = beat % 4
            section = (beat // 16) % 4  # Intro, Verse, Chorus, Bridge cycle
            
            # Drums (most sections)
            if section > 0 or beat >= 8:  # Skip drums for intro
                # Kick on 1 and 3
                if beat_in_bar in [0, 2]:
                    kick = self.generate_kick()
                    self.mix_at(buffer, kick, beat_start)
                
                # Snare on 2 and 4
                if beat_in_bar in [1, 3]:
                    snare = self.generate_snare()
                    self.mix_at(buffer, snare, beat_start)
                
                # Hi-hats on every 8th note
                for hh in range(2):
                    hh_start = beat_start + hh * (samples_per_beat // 2)
                    hat = self.generate_hihat(open_hat=(hh == 1 and beat_in_bar == 3))
                    self.mix_at(buffer, hat, hh_start)
            
            # Bass (follows chord progression)
            if beat_in_bar == 0:
                chord_idx = progression[bar % len(progression)]
                bass_freq = scale[chord_idx] / 2  # Octave down
                bass = self.generate_bass_note(bass_freq, spb * 2)
                self.mix_at(buffer, bass, beat_start)
            
            # Arpeggios (chorus sections)
            if section == 2 and beat_in_bar == 0:
                chord_idx = progression[bar % len(progression)]
                root = scale[chord_idx]
                third = scale[(chord_idx + 2) % 7] * (1.5 if (chord_idx + 2) >= 7 else 1)
                fifth = scale[(chord_idx + 4) % 7] * (1.5 if (chord_idx + 4) >= 7 else 1)
                arp = self.generate_arpeggio([root, third, fifth, third], spb * 4, spb / 2)
                self.mix_at(buffer, arp, beat_start)
            
            # Melody (verse and chorus)
            if section in [1, 2] and random.random() < 0.6:
                melody_degree = random.randint(0, 6)
                melody_freq = scale[melody_degree] * (2 if random.random() < 0.3 else 1)
                lead = self.generate_lead_note(melody_freq, spb * random.choice([0.5, 1, 2]))
                offset = random.randint(0, samples_per_beat // 2)
                self.mix_at(buffer, lead, beat_start + offset)
            
            # Pads (bridge and intro)
            if section in [0, 3] and beat_in_bar == 0 and bar % 2 == 0:
                chord_idx = progression[bar % len(progression)]
                root = scale[chord_idx]
                third = scale[(chord_idx + 2) % 7]
                fifth = scale[(chord_idx + 4) % 7]
                pad = self.generate_pad([root, third, fifth], spb * 8)
                self.mix_at(buffer, pad, beat_start)
        
        # Normalize and convert to 16-bit
        max_val = max(abs(s) for s in buffer) or 1.0
        normalized = [s / max_val * 0.85 for s in buffer]
        
        return normalized

    def save_wav(self, samples, filename):
        """Save samples to WAV file"""
        data = bytearray()
        for s in samples:
            clamped = max(-1.0, min(1.0, s))
            i_val = int(clamped * self.max_amp)
            data.extend(struct.pack('<h', i_val))
        
        with wave.open(filename, 'w') as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(self.sr)
            f.writeframes(data)
        
        print(f"  Saved: {filename}")


def main():
    generator = AdvancedMusicGenerator()
    
    # Track definitions
    tracks = [
        {
            'name': 'cyber_chase.wav',
            'bpm': 160,
            'scale': 'D_MINOR',
            'progression': 'dark',
            'duration': 120,
            'style': 'action'
        },
        {
            'name': 'neon_dreams.wav',
            'bpm': 100,
            'scale': 'F_LYDIAN',
            'progression': 'chill',
            'duration': 120,
            'style': 'chill'
        },
        {
            'name': 'data_storm.wav',
            'bpm': 180,
            'scale': 'E_MINOR',
            'progression': 'epic',
            'duration': 90,
            'style': 'intense'
        },
        {
            'name': 'terminal_groove.wav',
            'bpm': 130,
            'scale': 'A_MINOR',
            'progression': 'pop',
            'duration': 120,
            'style': 'funky'
        },
        {
            'name': 'midnight_protocol.wav',
            'bpm': 90,
            'scale': 'D_MINOR',
            'progression': 'dark',
            'duration': 120,
            'style': 'ambient'
        }
    ]
    
    output_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("=" * 50)
    print("TUR Advanced Music Generator")
    print("=" * 50)
    print()
    
    for track in tracks:
        samples = generator.generate_track(
            track['name'],
            track['bpm'],
            track['scale'],
            track['progression'],
            track['duration'],
            track['style']
        )
        
        filepath = os.path.join(output_dir, track['name'])
        generator.save_wav(samples, filepath)
        print()
    
    print("=" * 50)
    print("All tracks generated successfully!")
    print(f"Output directory: {output_dir}")
    print("=" * 50)


if __name__ == '__main__':
    main()
