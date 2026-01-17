"""
Secure Token Storage
Stores auth tokens in a separate file with basic obfuscation.
"""

import os
import base64

TOKEN_FILE = "session.dat"

def _get_token_path():
    """Get path to token file, works in dev and bundled mode."""
    # Store in game root (parent of core/)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, TOKEN_FILE)

def save_token(token: str) -> bool:
    """Save token to file with obfuscation."""
    path = _get_token_path()
    if not token:
        # If empty token provided, clear the file
        if os.path.exists(path):
            os.remove(path)
            print(f"DEBUG: Token cleared from {path}")
        return True
    try:
        # Simple obfuscation: reverse + base64
        reversed_token = token[::-1]
        encoded = base64.b64encode(reversed_token.encode()).decode()
        
        with open(_get_token_path(), 'w') as f:
            f.write(encoded)
        return True
    except Exception as e:
        print(f"Failed to save token: {e}")
        return False

def load_token():
    """Load and decode token from file."""
    path = _get_token_path()
    if not os.path.exists(path):
        return None
    try:
        with open(path, 'r') as f:
            encoded = f.read().strip()
        
        if not encoded:
            return None
            
        # Decode: base64 -> reverse
        reversed_token = base64.b64decode(encoded).decode()
        token = reversed_token[::-1]
        print(f"DEBUG: Token loaded from {path}")
        return token
    except Exception as e:
        print(f"Failed to load token: {e}")
        return None

def clear_token():
    """Delete the token file."""
    path = _get_token_path()
    if os.path.exists(path):
        try:
            os.remove(path)
        except Exception as e:
            print(f"Failed to clear token: {e}")
