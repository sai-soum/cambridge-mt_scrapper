import os
import re
import yaml
import soundfile as sf
import librosa
import numpy as np
import pickle
import shutil
from glob import glob
from tqdm import tqdm
import audalign as ad

def opj(*args):
    return os.path.join(*args)

def add_space_between_cases(text):
    return re.sub(r'([a-z])([A-Z])', r'\1 \2', text)

def categorize_tracks(multitrack_dir):
    correspondance = {
        'kick': [], 'snare': [], 'aux_perc': [], 'percussion': [], 'drum': [], 'bass': [], 'synth': [], 'keys': [], 
        'room': [], 'organ': [], 'brass': [], 'woodwind': [], 'vocal': [], 'string': [], 'fx': [], 'guitar': [], 'other': []
    }
    track_names = glob(opj(multitrack_dir, "*.wav"))
    names = [os.path.basename(name) for name in track_names]
    
    for name in names:
        process_name = re.sub(r'\d+', '', name.replace(".wav", "").replace("_", " ").replace("-", " "))
        process_name = add_space_between_cases(process_name).lower()
        
        categories = {
            "kick": ["kick"],
            "snare": ["snare"],
            "aux_perc": ["hihat", "tom", "cymbal", "ride", "crash", "splash", "hi", "hat", "ride"],
            "percussion": ["perc", "shaker", "kalimba", "clap", "snap", "djembe", "cowbell", "conga", "glockenspiel", "timpani", "congo", "beat", "overhead", "beatbox", "tambourine", "triangle", "maraca", "bongo", "cabasa", "guiro", "woodblock", "clave", "castanet", "agogo", "whistle", "bell", "chime", "gong", "tambourine"],
            "drum": ["drum"],
            "bass": ["bass"],
            "synth": ["synth"],
            "keys": ["piano", "keys", "clavinet", "rhodes", "accordion"],
            "room": ["room"],
            "organ": ["organ"],
            "brass": ["brass", "trumpet", "trombone", "horn", "bagpipe", "tuba", "euphonium"],
            "woodwind": ["woodwind", "flute", "clarinet", "oboe", "saxophone", "sax", "bassoon", "alto", "soprano"],
            "vocal": ["vocal", "choir", "vox", "backing"],
            "string": ["string", "violin", "cello", "viola"],
            "fx": ["fx"],
            "guitar": ["guitar", "gtr", "ukulele", "ukelele", "banjo", "fiddle", "mandolin"]
        }
        
        found = False
        for category, keywords in categories.items():
            if any(keyword in process_name for keyword in keywords):
                correspondance[category].append(name)
                found = True
                break
        
        if not found:
            correspondance['other'].append(name)
    
    return {k: v for k, v in correspondance.items() if v}
def get_first_subdir(parent_dir):
    """Returns the first subdirectory inside a given directory, or None if empty."""
    if os.path.exists(parent_dir) and os.path.isdir(parent_dir):
        subdirs = [d for d in os.listdir(parent_dir) if os.path.isdir(opj(parent_dir, d))]
        if subdirs:
            return opj(parent_dir, subdirs[0])
    return None

def save_correspondance(dataset_dir):
    song_dirs = glob(opj(dataset_dir, "*"))
    
    for song_dir in song_dirs:
        song_name = os.path.basename(song_dir)
        excerpt_multitrack_dir = get_first_subdir(opj(song_dir, "excerpt_multitrack"))
        full_multitrack_dir = get_first_subdir(opj(song_dir, "full_multitrack"))
        
        correspondance_excerpt = categorize_tracks(excerpt_multitrack_dir) if excerpt_multitrack_dir else {}
        correspondance_full = categorize_tracks(full_multitrack_dir) if full_multitrack_dir else {}
        
        aligned_dir = opj(song_dir, "aligned")
        os.makedirs(aligned_dir, exist_ok=True)
        
        with open(opj(aligned_dir, "correspondance_excerpt.yaml"), "w") as f:
            yaml.dump(correspondance_excerpt, f)
        
        with open(opj(aligned_dir, "correspondance_full.yaml"), "w") as f:
            yaml.dump(correspondance_full, f)

if __name__ == "__main__":
    dataset_folder = "/data3/share/soumya/Mixing_Secrets_Full"
    save_correspondance(dataset_folder)
