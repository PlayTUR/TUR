"""
Account Manager for TUR
Placeholder for future online account system.
Currently supports local accounts only (stored in settings).
"""

import os
import json
import hashlib


class AccountManager:
    """
    Account system placeholder.
    
    Current features (local):
    - Local username stored in settings
    - Local stats tracking
    
    Future features (online):
    - Login/register with backend
    - Cloud sync for scores
    - Friend lists
    - Leaderboards
    """
    
    def __init__(self, settings_manager):
        self.settings = settings_manager
        self.logged_in = False
        self.online_account = None
        
        # API endpoint placeholder (for future)
        self.API_URL = None  # "https://tur-api.example.com"
    
    @property
    def username(self):
        """Get current username (local or online)"""
        if self.online_account:
            return self.online_account.get("username", "ANON")
        return self.settings.get("name") or "ANON"
    
    def set_local_name(self, name):
        """Set local username (always available)"""
        self.settings.set("name", name)
    
    def is_online(self):
        """Check if using online account"""
        return self.logged_in and self.online_account is not None
    
    # ===== PLACEHOLDER METHODS FOR FUTURE =====
    
    def login(self, username, password):
        """
        Login to online account (placeholder).
        Returns: {'success': bool, 'message': str, 'token': str}
        """
        # TODO: Implement when backend is ready
        # req = urllib.request.Request(f"{self.API_URL}/login", ...)
        return {
            "success": False,
            "message": "Online accounts not yet available. Using local account."
        }
    
    def register(self, username, password, email=None):
        """
        Register online account (placeholder).
        Returns: {'success': bool, 'message': str}
        """
        # TODO: Implement when backend is ready
        return {
            "success": False,
            "message": "Online registration not yet available."
        }
    
    def sync_scores(self):
        """Sync local scores with cloud (placeholder)"""
        if not self.is_online():
            return False
        # TODO: Upload scores.json to cloud
        return False
    
    def get_leaderboard(self, song_name=None):
        """Get leaderboard (placeholder)"""
        # TODO: Fetch from API
        return []
    
    def logout(self):
        """Logout from online account"""
        self.logged_in = False
        self.online_account = None
