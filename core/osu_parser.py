import os

def parse_osu(file_path):
    """
    Parses a .osu file and returns a dictionary with metadata and notes.
    All key counts are remapped to 4 lanes.
    """
    if not os.path.exists(file_path):
        return None

    data = {
        'title': '',
        'artist': '',
        'difficulty_name': '',
        'audio_filename': '',
        'notes': [],
        'bpm': 120,
        'keys': 4,  # Default key count
        'mode': 0   # 0=std, 3=mania
    }

    current_section = None
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('//'):
                continue
                
            if line.startswith('[') and line.endswith(']'):
                current_section = line[1:-1]
                continue
                
            if current_section == "General":
                if line.startswith("AudioFilename:"):
                    data['audio_filename'] = line.split(":", 1)[1].strip()
                elif line.startswith("Mode:"):
                    data['mode'] = int(line.split(":")[1].strip())
            
            elif current_section == "Difficulty":
                if line.startswith("CircleSize:"):
                    data['keys'] = int(float(line.split(":")[1].strip()))
            
            elif current_section == "Metadata":
                if line.startswith("Title:"):
                    data['title'] = line.split(":", 1)[1].strip()
                elif line.startswith("Artist:"):
                    data['artist'] = line.split(":", 1)[1].strip()
                elif line.startswith("Version:"):
                    data['difficulty_name'] = line.split(":", 1)[1].strip()
            
            elif current_section == "HitObjects":
                # x,y,time,type,hitSound,objectParams,hitSample
                parts = line.split(',')
                if len(parts) >= 5:
                    try:
                        x = int(parts[0])
                        time_ms = int(parts[2])
                        obj_type = int(parts[3])
                        
                        # Calculate lane with key count remapping
                        keys = data['keys']
                        if data['mode'] == 3 and keys > 0:  # Mania mode
                            original_lane = int(x * keys / 512)
                            if keys <= 4:
                                lane = min(3, max(0, original_lane))
                            else:
                                # Remap 5K/6K/7K/8K to 4K
                                lane = int(original_lane * 4 / keys)
                                lane = min(3, max(0, lane))
                        else:
                            # Standard mode - map x to 4 lanes
                            lane = min(3, max(0, int(x / 128)))
                        
                        time_sec = time_ms / 1000.0
                        length = 0.0
                        
                        # Check for hold note (type 128 is mania long note)
                        if obj_type & 128:
                             if ':' in parts[5]:
                                 end_time_ms = int(parts[5].split(':')[0])
                                 length = (end_time_ms - time_ms) / 1000.0
                        
                        data['notes'].append({
                            'time': time_sec,
                            'lane': lane,
                            'length': length
                        })
                    except:
                        continue
    
    # Sort notes by time
    data['notes'].sort(key=lambda x: x['time'])
    
    # Log conversion info
    if data['keys'] != 4:
        print(f"Converted {data['keys']}K map to 4K: {len(data['notes'])} notes")
    
    return data
