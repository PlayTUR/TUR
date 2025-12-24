"""
Theme Manager - Custom theme export/import with shareable codes.
Features:
- Export current visual settings to .turtheme files
- Import themes from files
- Generate/apply short share codes for easy sharing
"""

import json
import os
import base64
import zlib

THEMES_DIR = "themes"

# Visual settings that can be exported/imported
EXPORTABLE_SETTINGS = [
    "note_col_1",
    "note_col_2", 
    "theme",
    "note_shape",
    "upscroll",
    "speed",
    "bg_dim",
    "show_hold_ends",
    "hit_sounds",
]


def ensure_themes_dir():
    """Create themes directory if it doesn't exist"""
    if not os.path.exists(THEMES_DIR):
        os.makedirs(THEMES_DIR)


def export_visual_settings(settings_manager):
    """Extract exportable visual settings from settings manager"""
    data = {}
    for key in EXPORTABLE_SETTINGS:
        val = settings_manager.get(key)
        if val is not None:
            # Convert tuples/lists to lists for JSON
            if isinstance(val, (list, tuple)):
                data[key] = list(val)
            else:
                data[key] = val
    return data


def import_visual_settings(settings_manager, data):
    """Apply visual settings from imported data"""
    for key in EXPORTABLE_SETTINGS:
        if key in data:
            settings_manager.set(key, data[key])
    settings_manager.save()


def export_theme_to_file(settings_manager, name="my_theme"):
    """Export current visual settings to a .turtheme file"""
    ensure_themes_dir()
    
    data = export_visual_settings(settings_manager)
    data["name"] = name
    data["version"] = 1
    
    # Sanitize filename
    safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
    if not safe_name:
        safe_name = "custom_theme"
    
    filepath = os.path.join(THEMES_DIR, f"{safe_name}.turtheme")
    
    # Avoid overwriting - add number if exists
    count = 1
    while os.path.exists(filepath):
        filepath = os.path.join(THEMES_DIR, f"{safe_name}_{count}.turtheme")
        count += 1
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    
    return filepath


def import_theme_from_file(settings_manager, filepath):
    """Import visual settings from a .turtheme file"""
    if not os.path.exists(filepath):
        return False, "File not found"
    
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        import_visual_settings(settings_manager, data)
        return True, data.get("name", "Imported Theme")
    except Exception as e:
        return False, str(e)


def list_available_themes():
    """List all .turtheme files in the themes directory"""
    ensure_themes_dir()
    themes = []
    
    for filename in os.listdir(THEMES_DIR):
        if filename.endswith('.turtheme'):
            filepath = os.path.join(THEMES_DIR, filename)
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    themes.append({
                        'filename': filename,
                        'path': filepath,
                        'name': data.get('name', filename[:-9]),
                        'theme': data.get('theme', 'UNKNOWN')
                    })
            except:
                themes.append({
                    'filename': filename,
                    'path': filepath,
                    'name': filename[:-9],
                    'theme': 'UNKNOWN'
                })
    
    return themes


def generate_share_code(settings_manager):
    """
    Generate a short shareable code encoding visual settings.
    Format: TUR-XXXXXXXX (base64 encoded, compressed)
    """
    data = export_visual_settings(settings_manager)
    
    # Convert to minimal JSON
    json_str = json.dumps(data, separators=(',', ':'))
    
    # Compress and encode
    compressed = zlib.compress(json_str.encode('utf-8'), 9)
    encoded = base64.urlsafe_b64encode(compressed).decode('ascii').rstrip('=')
    
    # Format with prefix for easy identification
    return f"TUR-{encoded}"


def apply_share_code(settings_manager, code):
    """
    Apply visual settings from a share code.
    Returns (success, message)
    """
    try:
        # Remove prefix if present
        if code.startswith("TUR-"):
            code = code[4:]
        
        # Remove any whitespace/dashes that might have been added
        code = code.replace('-', '').replace(' ', '')
        
        # Add padding back for base64
        padding = (4 - len(code) % 4) % 4
        code += '=' * padding
        
        # Decode and decompress
        compressed = base64.urlsafe_b64decode(code)
        json_str = zlib.decompress(compressed).decode('utf-8')
        data = json.loads(json_str)
        
        # Apply settings
        import_visual_settings(settings_manager, data)
        
        return True, "Theme applied successfully!"
    except zlib.error:
        return False, "Invalid share code (decompression failed)"
    except json.JSONDecodeError:
        return False, "Invalid share code (bad data)"
    except Exception as e:
        return False, f"Failed to apply: {e}"


def get_theme_preview_colors(data):
    """Get preview colors from theme data"""
    return {
        'col1': tuple(data.get('note_col_1', [50, 255, 50])),
        'col2': tuple(data.get('note_col_2', [255, 180, 50])),
        'base_theme': data.get('theme', 'TERMINAL')
    }
