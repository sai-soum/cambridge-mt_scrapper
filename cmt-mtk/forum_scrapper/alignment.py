import os
import soundfile as sf
import librosa
import numpy as np
import pickle
import pandas as pd
from glob import glob
from tqdm import tqdm
import audalign as ad

# Helper function for joining paths
opj = os.path.join

class AudioProcessor:
    def __init__(self, mix_path, multitrack_path):
        self.mix_path = mix_path
        self.multitrack_path = multitrack_path
        self.aligned_folder = mix_path.replace("dataset", "alignment").replace(".mp3", "")
        os.makedirs(self.aligned_folder, exist_ok=True)
    
    def get_rough_sum(self):
        """
        Create a rough mix from multitrack audio files.
        """
        check_rough_exists_path = opj(os.path.dirname(self.multitrack_path),"aligned/full_rough_mix.wav")
        if os.path.exists(check_rough_exists_path):
            return check_rough_exists_path
        if os.path.exists(opj(self.multitrack_path, ".DS_Store")):
            os.remove(opj(self.multitrack_path, ".DS_Store"))
        
        dry_tracks = sorted(glob(opj(self.multitrack_path, "*", "*.wav")))
        print(f"Found {len(dry_tracks)} tracks in {self.multitrack_path}")
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
            
            filename = f"rough_mix.wav"
            rough_mix_path = opj(self.aligned_folder, filename)
            sf.write(rough_mix_path, rough_sum, 44100)
            return rough_mix_path
        else:
            print(f"No tracks found in {self.multitrack_path}")
            return None

    def align_song(self):
        """Aligns mix with rough mix."""
        try:
            rough_mix_path = self.get_rough_sum()
            if rough_mix_path is None:
                return

            alignment_metadata_path = opj(self.aligned_folder, "alignment.pickle")
            
            recognizer = ad.CorrelationSpectrogramRecognizer()
            fine_recognizer = ad.CorrelationRecognizer()
            fine_recognizer.config.sample_rate = 44100
            fine_recognizer.config.max_lags = 0.05

            results = ad.align_files(self.mix_path, rough_mix_path, recognizer=recognizer)
            results = ad.fine_align(results=results, recognizer=fine_recognizer)

            pickle.dump(results, open(alignment_metadata_path, "wb"))
        except Exception as e:
            print(f"Error aligning {self.mix_path}: {e}")
    
    def align_and_save(self):
        """Save the aligned mix and rough mix as a composite file."""
        alignment_metadata_path = opj(self.aligned_folder, "alignment.pickle")
        if not os.path.exists(alignment_metadata_path):
            print(f"Alignment metadata not found for {self.mix_path}. Skipping.")
            return
        
        try:
            align_data = pickle.load(open(alignment_metadata_path, "rb"))
            offset = align_data[self.mix_path] - align_data["rough_mix.wav"]
            
            mix_preview, _ = sf.read(self.mix_path, always_2d=True)
            rough_mix, _ = sf.read(opj(self.aligned_folder, "rough_mix.wav"), always_2d=True)
            
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
            composite_path = opj(self.aligned_folder, "comp.wav")
            sf.write(composite_path, composite, 44100)
        except Exception as e:
            print(f"Error saving aligned mix for {self.mix_path}: {e}")

if __name__ == "__main__":
    path_list = pd.read_csv("/home/soumya/cambridge-mt_scrapper/cmt-mtk/forum_scrapper/forum_mix_mt_pair.csv")
    song_paths = zip(path_list["mix_path"], path_list["multitrack_path"])

    for mix_path, multitrack_path in tqdm(song_paths, desc="Processing songs"):
        processor = AudioProcessor(mix_path, multitrack_path)
        processor.align_song()
        processor.align_and_save()

