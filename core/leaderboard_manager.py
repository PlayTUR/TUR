import random
import json
import os

class LeaderboardManager:
    def __init__(self, game):
        self.game = game
        self.mock_players = [
            "NeonRider", "GlitchK1ng", "BassDrop", "CyberSamurai", 
            "RhythmG0d", "PixelValkyrie", "WaveSurfer", "NullPointer",
            "Synthetik", "VortexDrifter", "CodeBreaker", "BitCrusher"
        ]
        self.global_rankings = []
        self._generate_mock_data()
        
    def _generate_mock_data(self):
        # Create a list of players with random high stats
        self.global_rankings = []
        
        for name in self.mock_players:
            # Deterministic random based on name for persistence feel
            seed = sum(ord(c) for c in name)
            random.seed(seed)
            
            total_score = random.randint(500000, 5000000)
            level = int(total_score / 50000) + random.randint(1, 10)
            accuracy = 85.0 + (random.random() * 14.9)
            
            self.global_rankings.append({
                "name": name,
                "score": total_score,
                "level": level,
                "accuracy": round(accuracy, 2)
            })
            
        # Add Local User (if they have stats)
        local_name = self.game.settings.get("name")
        local_xp = self.game.settings.get("xp") or 0
        # Estimate score from XP (mock)
        local_score = local_xp * 100 
        
        # Check if local user is already represented or needs adding
        if local_name not in self.mock_players:
            self.global_rankings.append({
                "name": local_name,
                "score": local_score,
                "level": self.game.settings.get("level") or 1,
                "accuracy": 0.0 # Placeholder
            })
            
        # Sort by Score
        self.global_rankings.sort(key=lambda x: x["score"], reverse=True)
        
    def get_rankings(self):
        # Refresh local user stats before returning
        self._update_local_user_stats()
        # Re-sort
        self.global_rankings.sort(key=lambda x: x["score"], reverse=True)
        return self.global_rankings
        
    def _update_local_user_stats(self):
        local_name = self.game.settings.get("name")
        # Find local user entry
        for p in self.global_rankings:
            if p["name"] == local_name:
                # Update with current real stats
                p["level"] = self.game.settings.get("level") or 1
                xp = self.game.settings.get("xp") or 0
                p["score"] = xp * 150 # Mock formula: 1 XP = 150 Score?
                # In reality we'd sum actual high scores from ScoreManager
                p["accuracy"] = 99.9 # Mock
                return
        
        # If not found (name changed?), add new
        self.global_rankings.append({
             "name": local_name,
             "score": (self.game.settings.get("xp") or 0) * 150,
             "level": self.game.settings.get("level") or 1,
             "accuracy": 98.5
        })
        
    def get_user_rank(self):
        self._update_local_user_stats()
        self.global_rankings.sort(key=lambda x: x["score"], reverse=True)
        local_name = self.game.settings.get("name")
        for i, p in enumerate(self.global_rankings):
            if p["name"] == local_name:
                return i + 1
        return 999
