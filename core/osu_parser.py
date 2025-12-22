import os

def parse_osu(file_path):
    """
    Parses a .osu file and returns a dictionary with metadata and notes.
    """
    if not os.path.exists(file_path):
        return None

    data = {
        'title': '',
        'artist': '',
        'difficulty_name': '',
        'audio_filename': '',
        'notes': [],
        'bpm': 120 # Default or computed from timing points
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
                        
                        # Map X (0-512) to 4 lanes (0-3)
                        # We use 512 as the max X in osu!
                        lane = min(3, max(0, int(x / 128)))
                        
                        time_sec = time_ms / 1000.0
                        length = 0.0
                        
                        # Check for hold note (slider or long note)
                        # type 128 is a long note in mania
                        # types are bitmasks: 1=circle, 2=slider, 8=spinner, 128=mania_long
                        if obj_type & 128:
                             # mania long note: x,y,time,type,hitSound,endTime:hitSample...
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
    
    # Sort notes by time just in case
    data['notes'].sort(key=lambda x: x['time'])
    return data
