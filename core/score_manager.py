import json
import os

class ScoreManager:
    def __init__(self, file="scores.json"):
        self.file = file
        self.scores = {}
        self.load()

    def load(self):
        if os.path.exists(self.file):
            try:
                with open(self.file, 'r') as f:
                    self.scores = json.load(f)
            except:
                self.scores = {}
        else:
            self.scores = {}

    def save(self):
        with open(self.file, 'w') as f:
            json.dump(self.scores, f, indent=4)

    def get_score(self, song_name, difficulty):
        # Key: "SongName|Difficulty"
        key = f"{song_name}|{difficulty}"
        return self.scores.get(key, None)

    def submit_score(self, song_name, difficulty, score, rank, combo):
        key = f"{song_name}|{difficulty}"
        prev = self.scores.get(key)
        
        is_pb = False
        if not prev or score > prev['score']:
            self.scores[key] = {
                'score': score,
                'rank': rank,
                'combo': combo
            }
            is_pb = True
            self.save()
            
        return is_pb
