from pydub import AudioSegment
from pydub.playback import play
from pathlib import Path
import os

bip_sound = AudioSegment.from_file("bip.wav")  
boop_sound = AudioSegment.from_file("boop.wav")  
duration = 300

input_folder = Path('text2speech/')
output_folder = Path('audio/')

def add_bruitages(phrase_file, index):
    phrase = AudioSegment.from_file(f"{input_folder}/{phrase_file}")
    silence = AudioSegment.silent(duration=duration)

    phrase_with_bruitages = bip_sound + silence + phrase + boop_sound

    output_filename = f"{output_folder}/{phrase_file}"
    phrase_with_bruitages.export(output_filename, format="wav", parameters=["-ar", "44100"])
    print(f"Saved: {output_filename}")

for i, fichier in enumerate(os.listdir(input_folder)):
    if fichier.endswith(".wav"):  
        add_bruitages(fichier, i)
