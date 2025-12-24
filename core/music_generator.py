"""
Professional-Quality Procedural Music Generator for TUR
Features: ADSR envelopes, multiple oscillators, chord progressions,
arpeggios, multi-layer instruments, and proper song structure.
"""

import random
import wave
import struct
import math
import os

class MusicGenerator:
    def __init__(self, sample_rate=44100):
        self.sr = sample_rate
        self.max_amp = 32767 * 0.75
        
        # Musical scales (MIDI note numbers -> frequencies)
        self.scales = {
            'D_MINOR': [293.66, 329.63, 349.23, 392.00, 440.00, 466.16, 523.25],
            'A_MINOR': [220.00, 246.94, 261.63, 293.66, 329.63, 349.23, 392.00],
            'E_PHRYGIAN': [329.63, 349.23, 392.00, 440.00, 493.88, 523.25, 587.33],
            'C_MAJOR': [261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88],
            'G_MINOR': [392.00, 440.00, 466.16, 523.25, 587.33, 622.25, 698.46],
        }
        
        # Chord progressions (scale degrees, 0-indexed)
        self.progressions = {
            'mysterious': [(0, 2, 4), (5, 0, 2), (3, 5, 0), (4, 6, 1)],
            'driving': [(0, 2, 4), (3, 5, 0), (4, 6, 1), (0, 2, 4)],
            'epic': [(0, 2, 4), (5, 0, 2), (4, 6, 1), (3, 5, 0)],
            'triumph': [(0, 2, 4), (4, 6, 1), (3, 5, 0), (0, 2, 4)],
            'emotional': [(0, 2, 4), (3, 5, 0), (5, 0, 2), (4, 6, 1)],
        }

    def envelope(self, t, attack=0.02, decay=0.1, sustain=0.7, release=0.2, duration=1.0):
        """ADSR envelope"""
        if t < 0:
            return 0.0
        if t < attack:
            return t / attack
        elif t < attack + decay:
            return 1.0 - (1.0 - sustain) * ((t - attack) / decay)
        elif t < duration - release:
            return sustain
        elif t < duration:
            return sustain * max(0, 1.0 - (t - (duration - release)) / release)
        return 0.0

    def oscillator(self, phase, wave_type='sine'):
        """Generate oscillator sample with anti-aliasing approximation"""
        p = phase % 1.0
        if wave_type == 'sine':
            return math.sin(2 * math.pi * p)
        elif wave_type == 'square':
            # Soft square for less harshness
            return math.tanh(4 * math.sin(2 * math.pi * p))
        elif wave_type == 'saw':
            return 2.0 * p - 1.0
        elif wave_type == 'triangle':
            return 4.0 * abs(p - 0.5) - 1.0
        elif wave_type == 'pulse':
            return 1.0 if p < 0.25 else -1.0
        return 0.0

    def low_pass(self, samples, cutoff_ratio=0.3):
        """Simple low-pass filter for warmth"""
        filtered = []
        prev = 0.0
        alpha = cutoff_ratio
        for s in samples:
            prev = alpha * s + (1 - alpha) * prev
            filtered.append(prev)
        return filtered

    # === Instrument Generators ===
    
    def gen_kick(self, duration=0.25):
        """Punchy kick drum with pitch envelope"""
        samples = []
        n = int(duration * self.sr)
        for i in range(n):
            t = i / self.sr
            # Pitch drops from 150Hz to 50Hz
            freq = 150 * math.exp(-t * 25) + 50
            phase = freq * t
            body = math.sin(2 * math.pi * phase) * math.exp(-t * 6)
            click = random.uniform(-0.3, 0.3) * math.exp(-t * 80)
            samples.append((body * 0.8 + click) * 0.9)
        return samples

    def gen_snare(self, duration=0.18):
        """Snappy snare drum"""
        samples = []
        n = int(duration * self.sr)
        for i in range(n):
            t = i / self.sr
            body = math.sin(2 * math.pi * 200 * t) * math.exp(-t * 18) * 0.5
            noise = random.uniform(-1, 1) * math.exp(-t * 15) * 0.6
            samples.append(body + noise)
        return samples

    def gen_hihat(self, duration=0.06, open_hat=False):
        """Hi-hat cymbal"""
        samples = []
        decay = 5 if open_hat else 30
        n = int(duration * self.sr)
        for i in range(n):
            t = i / self.sr
            noise = random.uniform(-1, 1) * math.exp(-t * decay) * 0.35
            samples.append(noise)
        return samples

    def gen_bass(self, freq, duration=0.5):
        """Sub bass with filtered saw"""
        samples = []
        n = int(duration * self.sr)
        phase = 0.0
        for i in range(n):
            t = i / self.sr
            phase += freq / self.sr
            # Layered waveforms
            sub = self.oscillator(phase * 0.5, 'sine') * 0.5  # Sub octave
            saw = self.oscillator(phase, 'saw') * 0.3
            env = self.envelope(t, 0.01, 0.1, 0.8, 0.1, duration)
            samples.append((sub + saw) * env * 0.7)
        return self.low_pass(samples, 0.2)

    def gen_lead(self, freq, duration=0.3):
        """Synth lead with vibrato"""
        samples = []
        n = int(duration * self.sr)
        phase = 0.0
        for i in range(n):
            t = i / self.sr
            vibrato = 1.0 + 0.015 * math.sin(2 * math.pi * 5.5 * t)
            phase += (freq * vibrato) / self.sr
            # Detuned oscillators
            osc1 = self.oscillator(phase, 'pulse') * 0.4
            osc2 = self.oscillator(phase * 1.005, 'square') * 0.3
            env = self.envelope(t, 0.02, 0.15, 0.5, 0.15, duration)
            samples.append((osc1 + osc2) * env * 0.5)
        return samples

    def gen_pad(self, freqs, duration=2.0):
        """Warm pad chord"""
        samples = [0.0] * int(duration * self.sr)
        for freq in freqs:
            phase = random.random()
            for i in range(len(samples)):
                t = i / self.sr
                phase += freq / self.sr
                env = self.envelope(t, 0.6, 0.4, 0.5, 0.5, duration)
                osc = self.oscillator(phase, 'sine')
                osc += 0.2 * self.oscillator(phase * 2.01, 'sine')  # Slight detune
                samples[i] += osc * env * 0.12
        return samples

    def gen_arp(self, freqs, duration=2.0, note_len=0.125):
        """Arpeggiator pattern"""
        samples = [0.0] * int(duration * self.sr)
        note_samples = int(note_len * self.sr)
        num_notes = len(freqs)
        
        pos = 0
        note_idx = 0
        while pos < len(samples):
            freq = freqs[note_idx % num_notes]
            note = self.gen_lead(freq, note_len * 0.9)
            for j, s in enumerate(note):
                if pos + j < len(samples):
                    samples[pos + j] += s * 0.6
            pos += note_samples
            note_idx += 1
        return samples

    # === Track Mixing ===
    
    def mix_at(self, buffer, source, start):
        """Mix source into buffer at position"""
        for i, s in enumerate(source):
            pos = start + i
            if 0 <= pos < len(buffer):
                buffer[pos] += s

    def normalize(self, samples):
        """Normalize to prevent clipping"""
        peak = max(abs(s) for s in samples) or 1.0
        return [s / peak * 0.85 for s in samples]

    def save_wav(self, samples, filename):
        """Save to WAV file"""
        data = bytearray()
        for s in samples:
            clamped = max(-1.0, min(1.0, s))
            data.extend(struct.pack('<h', int(clamped * self.max_amp)))
        
        with wave.open(filename, 'w') as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(self.sr)
            f.writeframes(data)

    # === Track Generation ===

    def generate_track(self, bpm, scale_name, progression_type, duration=90, mood='neutral'):
        """Generate a complete track with proper structure"""
        n_samples = int(duration * self.sr)
        buffer = [0.0] * n_samples
        
        spb = 60.0 / bpm
        samples_per_beat = int(spb * self.sr)
        total_beats = int(duration / spb)
        
        scale = self.scales[scale_name]
        prog = self.progressions[progression_type]
        
        # Generate melodic motif (reused for coherence)
        motif = [random.choice([0, 2, 4, 5]) for _ in range(4)]
        
        for beat in range(total_beats):
            beat_start = beat * samples_per_beat
            bar = beat // 4
            beat_in_bar = beat % 4
            section = (beat // 32) % 4  # 8-bar sections
            
            chord_idx = bar % len(prog)
            chord_degrees = prog[chord_idx]
            root_freq = scale[chord_degrees[0]] / 2  # Bass octave
            
            # === DRUMS ===
            if section >= 1:  # Drums enter after intro
                drum_intensity = 1.0 if section >= 2 else 0.7
                
                # Kick on 1 and 3
                if beat_in_bar in [0, 2]:
                    kick = self.gen_kick()
                    self.mix_at(buffer, [s * drum_intensity for s in kick], beat_start)
                
                # Snare on 2 and 4
                if beat_in_bar in [1, 3]:
                    snare = self.gen_snare()
                    self.mix_at(buffer, [s * drum_intensity for s in snare], beat_start)
                
                # Hi-hats
                for hh in range(4):  # 16th notes
                    hh_pos = beat_start + hh * (samples_per_beat // 4)
                    is_open = (hh == 2 and beat_in_bar == 3)
                    hat = self.gen_hihat(open_hat=is_open)
                    self.mix_at(buffer, [s * drum_intensity * 0.7 for s in hat], hh_pos)
            
            # === BASS ===
            if beat_in_bar == 0:
                bass = self.gen_bass(root_freq, spb * 1.5)
                self.mix_at(buffer, bass, beat_start)
            
            # === CHORDS/PADS ===
            if section in [0, 3] and beat_in_bar == 0 and bar % 2 == 0:
                chord_freqs = [scale[d] for d in chord_degrees]
                pad = self.gen_pad(chord_freqs, spb * 8)
                self.mix_at(buffer, pad, beat_start)
            
            # === ARPEGGIOS ===
            if section == 2 and beat_in_bar == 0:
                arp_freqs = [scale[d] * 2 for d in chord_degrees]  # High octave
                arp = self.gen_arp(arp_freqs, spb * 4, spb * 0.25)
                self.mix_at(buffer, arp, beat_start)
            
            # === MELODY ===
            if section >= 1 and random.random() < 0.4:
                m_deg = motif[beat_in_bar % len(motif)]
                m_freq = scale[m_deg] * random.choice([1, 2])
                lead = self.gen_lead(m_freq, spb * random.choice([0.5, 1.0, 1.5]))
                offset = random.randint(0, samples_per_beat // 4)
                self.mix_at(buffer, lead, beat_start + offset)
        
        return self.normalize(buffer)

    # === Story Mode Tracks ===

    def generate_all(self, output_dir="story_music"):
        """Generate all story mode tracks"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        tracks = [
            {"name": "story_intro.wav", "bpm": 95, "scale": "D_MINOR", 
             "prog": "mysterious", "duration": 120, "mood": "atmospheric"},
            {"name": "story_action.wav", "bpm": 140, "scale": "A_MINOR",
             "prog": "driving", "duration": 120, "mood": "intense"},
            {"name": "story_tension.wav", "bpm": 110, "scale": "E_PHRYGIAN",
             "prog": "mysterious", "duration": 120, "mood": "suspense"},
            {"name": "story_boss.wav", "bpm": 170, "scale": "E_PHRYGIAN",
             "prog": "epic", "duration": 120, "mood": "aggressive"},
            {"name": "story_climax.wav", "bpm": 180, "scale": "G_MINOR",
             "prog": "epic", "duration": 120, "mood": "intense"},
            {"name": "story_victory.wav", "bpm": 120, "scale": "C_MAJOR",
             "prog": "triumph", "duration": 90, "mood": "uplifting"},
            {"name": "story_final.wav", "bpm": 150, "scale": "G_MINOR",
             "prog": "emotional", "duration": 120, "mood": "climactic"},
        ]
        
        generated = []
        for t in tracks:
            path = os.path.join(output_dir, t["name"])
            if not os.path.exists(path):
                print(f"Generating {t['name']} ({t['bpm']} BPM, {t['scale']})...")
                samples = self.generate_track(
                    t["bpm"], t["scale"], t["prog"], t["duration"], t["mood"]
                )
                self.save_wav(samples, path)
                generated.append(t["name"])
                print(f"  -> Saved {t['name']}")
        
        return generated

    # === SFX Generation (kept for compatibility) ===
    
    def generate_sfx(self, filename, freq, duration=0.1, wave_type="SQUARE", slide=0.0):
        """Generate simple sound effect"""
        n_samples = int(duration * self.sr)
        samples = []
        phase = 0.0
        
        for i in range(n_samples):
            t = i / self.sr
            cur_freq = max(20, freq + slide * t)
            phase += cur_freq / self.sr
            
            if wave_type == "SQUARE":
                val = 1.0 if (phase % 1.0) < 0.5 else -1.0
            elif wave_type == "SINE":
                val = math.sin(2 * math.pi * phase)
            elif wave_type == "SAW":
                val = 2.0 * (phase % 1.0) - 1.0
            elif wave_type == "NOISE":
                val = random.uniform(-1, 1)
            else:
                val = 0.0
            
            env = self.envelope(t, 0.01, 0.02, 0.8, 0.05, duration)
            samples.append(val * env * 0.5)
        
        self.save_wav(samples, filename)


if __name__ == "__main__":
    gen = MusicGenerator()
    gen.generate_all("story_music")
