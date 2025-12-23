"""
OSU to TUR Converter
Converts osu! beatmap files (.osu) to TUR bundle format (.tur)
Supports osu!mania (4K) beatmaps for best compatibility.
"""

import os
import re
import base64


def parse_osu_file(osu_path):
    """
    Parse an .osu file and extract beatmap data.
    
    Returns:
        dict with title, artist, audio, bpm, notes, etc.
    """
    data = {
        'title': '',
        'artist': '',
        'audio': '',
        'bpm': 120,
        'notes': [],
        'mode': 0,  # 0=std, 1=taiko, 2=catch, 3=mania
        'keys': 4,
    }
    
    with open(osu_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    section = None
    timing_points = []
    
    for line in lines:
        line = line.strip()
        
        # Section headers
        if line.startswith('[') and line.endswith(']'):
            section = line[1:-1]
            continue
        
        if not line or line.startswith('//'):
            continue
        
        # General section
        if section == 'General':
            if line.startswith('AudioFilename:'):
                data['audio'] = line.split(':', 1)[1].strip()
            elif line.startswith('Mode:'):
                data['mode'] = int(line.split(':')[1].strip())
        
        # Metadata
        elif section == 'Metadata':
            if line.startswith('Title:'):
                data['title'] = line.split(':', 1)[1].strip()
            elif line.startswith('Artist:'):
                data['artist'] = line.split(':', 1)[1].strip()
        
        # Difficulty
        elif section == 'Difficulty':
            if line.startswith('CircleSize:'):
                data['keys'] = int(float(line.split(':')[1].strip()))
        
        # Timing points for BPM
        elif section == 'TimingPoints':
            parts = line.split(',')
            if len(parts) >= 2:
                try:
                    offset = float(parts[0])
                    beat_length = float(parts[1])
                    if beat_length > 0:  # Positive = BPM definition
                        bpm = 60000 / beat_length
                        timing_points.append((offset, bpm))
                except:
                    pass
        
        # Hit objects (notes)
        elif section == 'HitObjects':
            parts = line.split(',')
            if len(parts) >= 4:
                try:
                    x = int(parts[0])
                    time_ms = int(parts[2])
                    obj_type = int(parts[3])
                    
                    # Calculate lane from x position
                    # For any key count, remap to 4 lanes
                    keys = data['keys']
                    if data['mode'] == 3 and keys > 0:  # Mania mode
                        # Calculate original lane from x position
                        original_lane = int(x * keys / 512)
                        # Remap to 4 lanes (compress higher key counts)
                        if keys <= 4:
                            lane = min(3, original_lane)
                        else:
                            # Map 5K/6K/7K/8K etc to 4K
                            lane = int(original_lane * 4 / keys)
                            lane = min(3, max(0, lane))
                    else:
                        # Standard mode - map x to 4 lanes
                        lane = min(3, int(x / 128))
                    
                    note = {
                        'time': time_ms / 1000.0,  # Convert to seconds
                        'lane': lane,
                        'length': 0
                    }
                    
                    # Check for long note (hold)
                    if obj_type & 128:  # Mania hold note
                        if len(parts) >= 6:
                            end_time = parts[5].split(':')[0]
                            try:
                                note['length'] = (int(end_time) - time_ms) / 1000.0
                            except:
                                pass
                    
                    data['notes'].append(note)
                except:
                    pass
    
    # Get BPM from first timing point
    if timing_points:
        data['bpm'] = timing_points[0][1]
    
    # Sort notes by time
    data['notes'].sort(key=lambda n: n['time'])
    
    # Calculate duration
    if data['notes']:
        data['duration'] = data['notes'][-1]['time'] + data['notes'][-1].get('length', 0) + 5
    else:
        data['duration'] = 180
    
    return data


def convert_osu_to_tur(osu_path, output_dir=None, embed_audio=True):
    """
    Convert an .osu file to .tur format.
    
    Args:
        osu_path: Path to .osu file
        output_dir: Directory for output (defaults to same as osu file)
        embed_audio: Whether to embed audio in the .tur file
    
    Returns:
        Path to created .tur file, or None on failure
    """
    import json
    
    if not os.path.exists(osu_path):
        print(f"OSU file not found: {osu_path}")
        return None
    
    # Parse osu file
    data = parse_osu_file(osu_path)
    
    if not data['notes']:
        print(f"No notes found in: {osu_path}")
        return None
    
    # Determine output path
    if output_dir is None:
        output_dir = os.path.dirname(osu_path)
    
    base_name = os.path.splitext(os.path.basename(osu_path))[0]
    tur_path = os.path.join(output_dir, f"{base_name}.tur")
    
    # Build TUR data
    tur_data = {
        'format': 'TUR_BUNDLE_v2',
        'title': data['title'] or base_name,
        'artist': data['artist'] or 'Unknown',
        'difficulty': 'IMPORTED',
        'bpm': int(data['bpm']),
        'duration': int(data['duration']),
        'source': 'osu!',
        'notes': data['notes']
    }
    
    # Try to embed audio
    if embed_audio and data['audio']:
        audio_path = os.path.join(os.path.dirname(osu_path), data['audio'])
        if os.path.exists(audio_path):
            try:
                with open(audio_path, 'rb') as af:
                    audio_bytes = af.read()
                tur_data['audio_data'] = base64.b64encode(audio_bytes).decode('ascii')
                tur_data['audio_ext'] = os.path.splitext(data['audio'])[1]
                tur_data['audio_size'] = len(audio_bytes)
                print(f"Embedded audio: {len(audio_bytes)} bytes")
            except Exception as e:
                print(f"Could not embed audio: {e}")
                tur_data['audio'] = data['audio']
        else:
            tur_data['audio'] = data['audio']
    else:
        tur_data['audio'] = data['audio']
    
    # Write TUR file
    with open(tur_path, 'w') as f:
        json.dump(tur_data, f)
    
    print(f"Converted: {os.path.basename(osu_path)} -> {os.path.basename(tur_path)}")
    print(f"  Notes: {len(data['notes'])}, BPM: {int(data['bpm'])}")
    
    return tur_path


def batch_convert_osu(source_dir, output_dir=None):
    """
    Convert all .osu files in a directory.
    
    Returns:
        List of created .tur paths
    """
    if output_dir is None:
        output_dir = source_dir
    
    os.makedirs(output_dir, exist_ok=True)
    
    converted = []
    for filename in os.listdir(source_dir):
        if filename.lower().endswith('.osu'):
            osu_path = os.path.join(source_dir, filename)
            result = convert_osu_to_tur(osu_path, output_dir)
            if result:
                converted.append(result)
    
    return converted


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        path = sys.argv[1]
        if os.path.isdir(path):
            batch_convert_osu(path)
        else:
            convert_osu_to_tur(path)
    else:
        print("Usage: python osu_converter.py <file.osu or directory>")
