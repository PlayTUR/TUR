from core.music_generator import MusicGenerator
import os

gen = MusicGenerator()
if not os.path.exists("mainmenu_music"):
    os.makedirs("mainmenu_music")

# Chill Menu Track (Ambiance) - 100 BPM
# Scale: C Major 7ish
scale = [261.63, 329.63, 392.00, 493.88, 523.25] 
gen.write_track("mainmenu_music/menu_theme.wav", 100, scale, duration=30)
print("Generated mainmenu_music/menu_theme.wav")
