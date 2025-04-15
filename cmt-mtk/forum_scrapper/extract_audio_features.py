import os
import glob
import pickle
import numpy as np
import tqdm
import concurrent.futures
import librosa
import pyloudnorm as pyln
from scipy.stats import skew
import time
import cProfile

def dynamics(x, fs):
    rms = librosa.feature.rms(y=x)
    dynamic_range = np.max(rms) - np.min(rms)
    zcr = librosa.feature.zero_crossing_rate(x)
    crest_factor = np.max(rms) / np.mean(rms)
    
    meter = pyln.Meter(fs)
    loudness = meter.integrated_loudness(x.T)
    return {
        "rms": rms,
        "crest_factor": crest_factor,
        "dynamic_range": dynamic_range,
        "zcr": zcr,
        "loudness": loudness
    }


def spectral_features(x, fs):
    spectral_cetroid = librosa.feature.spectral_centroid(y=x, sr=fs)
    spectral_tilt = librosa.feature.spectral_rolloff(y=x, sr=fs, roll_percent=0.85)
    spectral_bandwidth = librosa.feature.spectral_bandwidth(y=x, sr=fs)
    spectral_flatness = librosa.feature.spectral_flatness(y=x)
    spectral_flux = librosa.onset.onset_strength(y=x, sr=fs)
    mfcc = librosa.feature.mfcc(y=x, sr=fs)
    return {
        "spectral_cetroid": spectral_cetroid,
        "spectral_tilt": spectral_tilt,
        "spectral_bandwidth": spectral_bandwidth,
        "spectral_flatness": spectral_flatness,
        "spectral_flux": spectral_flux,
        "mfcc": mfcc
    }


def spatial_features(x, fs):
    if x.shape[1] == 1:
        x = np.concatenate([x, x], axis=1)
    sum_ = x[:, 0] + x[:, 1]
    diff = x[:, 0] - x[:, 1]
    sum_power = (np.sqrt(np.mean(sum_ ** 2))) ** 2
    diff_power = (np.sqrt(np.mean(diff ** 2))) ** 2
    stereo_width = diff_power / (sum_power + 1e-8)
    left_power = (np.sqrt(np.mean(x[:, 0] ** 2))) ** 2
    right_power = (np.sqrt(np.mean(x[:, 1] ** 2))) ** 2
    stereo_imbalance = (right_power - left_power) / (right_power + left_power + 1e-8)
    mid = (x[:, 0] + x[:, 1]) / 2
    side = (x[:, 0] - x[:, 1]) / 2
    mid_power = (np.sqrt(np.mean(mid ** 2))) ** 2
    side_power = (np.sqrt(np.mean(side ** 2))) ** 2
    midside_ratio = mid_power / (side_power + 1e-8)
    return {
        "stereo_width": stereo_width,
        "stereo_imbalance": stereo_imbalance,
        "midside_ratio": midside_ratio
    }


def tonal_features(x, fs):
    harmonic, _ = librosa.effects.hpss(x)
    noise = x - harmonic
    hnr = np.mean(np.abs(harmonic) / (np.abs(noise) + 1e-6))
    tonal_centroid = librosa.feature.tonnetz(y=x)
    return {
        "hnr": hnr,
        "tonal_centroid": tonal_centroid
    }


def extract_features(audio_path, sr=44100):
    # start_time = time.time()
    try: 
        x, fs = librosa.load(audio_path, sr=sr, mono=False)
        if fs != 44100:
            x = librosa.resample(x, fs, 44100)
        meter = pyln.Meter(sr)
        loudness = meter.integrated_loudness(x.T)
        x = pyln.normalize.loudness(x.T, loudness, -15.0)
        x = x.T
        if x.ndim == 1:
            x = np.vstack([x, x])

        audio_feature = {}
        print(f"Extracting features for {audio_path}")
        # print("Dynamics")
        audio_feature['dynamics'] = dynamics(x, fs)
        # print("Spectral")
        audio_feature['spectral'] = spectral_features(x, fs)
        # print("Spatial")
        audio_feature['spatial'] = spatial_features(x, fs)
        # print("Tonal")
        audio_feature['tonal'] = tonal_features(x, fs)

        # end_time = time.time()
        # print(f"Feature extraction for {audio_path} took {end_time - start_time:.2f} seconds.")
        return audio_feature
    except Exception as e:
        print(f"Error processing {audio_path}: {e}")
        return None


def save_features(audio_path, audio_feature, forum_dataset_path, af_save_path):
    pkl_path = audio_path.replace(forum_dataset_path, af_save_path).replace(".mp3", "_loudnorm.pkl")
    os.makedirs(os.path.dirname(pkl_path), exist_ok=True)
    with open(pkl_path, "wb") as f:
        pickle.dump(audio_feature, f)


def process_audio(audio, forum_dataset_path, af_save_path):
    # check if the audio has already been processed
    pkl_path = audio.replace(forum_dataset_path, af_save_path).replace(".mp3", "_loudnorm.pkl")
    if os.path.exists(pkl_path):
        return
    
    audio_feature = extract_features(audio)
    if audio_feature is not None:
        save_features(audio, audio_feature, forum_dataset_path, af_save_path)


def main():
    forum_dataset_path = os.path.join("/data4/soumya/MSF_forum", "dataset")
    af_save_path = os.path.join(os.path.dirname(forum_dataset_path), "audio_features")

    # all_audio = glob.glob(os.path.join(forum_dataset_path, "*", "*", "*.mp3"))
    # print(f"Found {len(all_audio)} audio files.")
    # all_audio = all_audio[:5]
    audio_path ="/data4/soumya/MSF_forum/dataset/Discussion Zone - Hip-hop, R&B, Soul" 
    all_audio = glob.glob(os.path.join(audio_path, "*/*.mp3"))
    print(f"Found {len(all_audio)} audio files.")
    # Track progress using tqdm and process audio in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        list(tqdm.tqdm(executor.map(process_audio, all_audio, [forum_dataset_path]*len(all_audio), [af_save_path]*len(all_audio)), total=len(all_audio)))


if __name__ == "__main__":
    # Uncomment for profiling
    # profiler = cProfile.Profile()
    # profiler.enable()
    
    main()
    
    # Uncomment for profiling
    # profiler.disable()
    # profiler.print_stats()
