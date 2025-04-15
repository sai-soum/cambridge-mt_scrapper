import os
import soundfile as sf
import librosa
import numpy as np
import pickle
from glob import glob
from tqdm import tqdm
import audalign as ad

# Helper function for joining paths
opj = os.path.join

class AudioProcessor:
    def __init__(self, song_path):
        self.song_path = song_path
        self.aligned_folder = opj(song_path, "aligned")
        os.makedirs(self.aligned_folder, exist_ok=True)

    def get_rough_sum(self, multitrack_folder):
        """
        Create a rough mix from multitrack audio files.
        """
        # remove an MACOS file
        if os.path.exists(opj(multitrack_folder, ".DS_Store")):
            os.remove(opj(multitrack_folder, ".DS_Store"))
        
        dry_tracks = sorted(glob(opj(multitrack_folder, "*","*.wav")))
        print(f"Found {len(dry_tracks)} tracks in {multitrack_folder}")
        drys = []
        
        for dry_track in dry_tracks:
            wav, sr = sf.read(dry_track, always_2d=True)
            if sr != 44100:
                wav = librosa.resample(wav.T, orig_sr=sr, target_sr=44100).T
            drys.append(wav)
        
        if drys:
            max_len = max(len(x) for x in drys)
            drys = [np.pad(x, ((0, max_len - len(x)), (0, 0))) for x in drys]
            rough_sum = sum(drys)
            # go to the parent folder and save the rough mix
            temp_name = os.path.basename(multitrack_folder).replace("_multitrack", "")
            filename = f"{temp_name}_rough_mix.wav"
            # print(f"Saving rough mix to {filename}")
            rough_mix_path = opj(self.aligned_folder, filename)
            sf.write(rough_mix_path, rough_sum, 44100)
            # print(f"Rough mix saved to {rough_mix_path}")
            return rough_mix_path
        else:
            print(f"No tracks found in {multitrack_folder}")
            return None

    def align_song(self, mix_type):
        """Aligns mix previews with rough mix."""
        try:
            mix_preview_path = opj(self.song_path, f"{mix_type}_mix_previews", f"{mix_type}_mix_preview.mp3")
            rough_mix_path = opj(self.aligned_folder, f"{mix_type}_rough_mix.wav")
            alignment_metadata_path = opj(self.aligned_folder, f"{mix_type}_alignment.pickle")
            
            if os.path.exists(rough_mix_path):
                recognizer = ad.CorrelationSpectrogramRecognizer()
                fine_recognizer = ad.CorrelationRecognizer()
                fine_recognizer.config.sample_rate = 44100
                fine_recognizer.config.max_lags = 0.05
    
                results = ad.align_files(mix_preview_path, rough_mix_path, recognizer=recognizer)
                results = ad.fine_align(results=results, recognizer=fine_recognizer)
    
                pickle.dump(results, open(alignment_metadata_path, "wb"))
        except Exception as e:
            print(f"Error aligning {mix_type} for {self.song_path}: {e}")
    
    def align_and_save(self, mix_type):
        """Save the aligned mix and rough mix as a composite file."""
        alignment_metadata_path = opj(self.aligned_folder, f"{mix_type}_alignment.pickle")
        if not os.path.exists(alignment_metadata_path):
            print(f"Alignment metadata not found for {mix_type} in {self.song_path}. Skipping.")
            return
        
        try:
            align_data = pickle.load(open(alignment_metadata_path, "rb"))
            offset = align_data[f"{mix_type}_mix_preview.mp3"] - align_data[f"{mix_type}_rough_mix.wav"]
            
            mix_preview, _ = sf.read(opj(self.song_path, f"{mix_type}_mix_previews", f"{mix_type}_mix_preview.mp3"), always_2d=True)
            rough_mix, _ = sf.read(opj(self.aligned_folder, f"{mix_type}_rough_mix.wav"), always_2d=True)
            
            mix_preview = np.mean(mix_preview, axis=-1)
            rough_mix = np.mean(rough_mix, axis=-1)
            
            offset_sample = int(round(offset * 44100))
            rough_mix = rough_mix[offset_sample:] if offset_sample > 0 else np.pad(rough_mix, (-offset_sample, 0))
            
            min_length = min(len(mix_preview), len(rough_mix))
            mix_preview = mix_preview[:min_length]
            rough_mix = rough_mix[:min_length]
            
            def rms(x):
                return np.sqrt(np.mean(np.square(x)))
            rough_mix = rough_mix / rms(rough_mix) * rms(mix_preview)
            
            composite = np.stack([mix_preview, rough_mix], axis=-1)
            composite_path = opj(self.aligned_folder, f"{mix_type}_comp.wav")
            sf.write(composite_path, composite, 44100)
        except Exception as e:
            print(f"Error saving aligned mix for {mix_type} in {self.song_path}: {e}")

if __name__ == "__main__":
    dataset_folder = "/data3/share/soumya/Mixing_Secrets_Full"
    song_paths = sorted(glob(opj(dataset_folder, "*")))
    
    for song_path in tqdm(song_paths, desc="Processing songs"):
        processor = AudioProcessor(song_path)
        print(f"Processing {song_path}")
        
        excerpt_rough_mix = processor.get_rough_sum(opj(song_path, "excerpt_multitrack"))
        full_rough_mix = processor.get_rough_sum(opj(song_path, "full_multitrack"))
        print(f"Processing {song_path}")
        print(f"Excerpt rough mix: {excerpt_rough_mix}")
        print(f"Full rough mix: {full_rough_mix}")
        if excerpt_rough_mix:
            processor.align_song("excerpt")
            processor.align_and_save("excerpt")
        else:
            print(f"No excerpt rough mix found for {song_path}")
        if full_rough_mix:
            processor.align_song("full")
            processor.align_and_save("full")
        else:
            print(f"No full rough mix found for {song_path}")

