

import os
import numpy as np
import pyloudnorm as pyln
import glob
import librosa
from scipy.stats import skew
import pickle
from tqdm import tqdm
# Extract features from audio files
# Dynamics
# RMS gives an idea of the loudness of the signal
# Zero crossing rate indicates the number of times the signal crosses zero
def dynamics(x,fs):
    print(x.shape)
    rms = librosa.feature.rms(y=x)
    dynamic_range = np.max(rms) - np.min(rms)
    zcr = librosa.feature.zero_crossing_rate(x)
    crest_factor = np.max(rms) / np.mean(rms)
    
    meter = pyln.Meter(fs) # create BS.1770-4 meter
    loudness = meter.integrated_loudness(x.T)
    dynamics = {
        "rms": rms,
        "crest_factor": crest_factor,
        "dynamic_range": dynamic_range,
        "zcr": zcr,
        "loudness": loudness

    }
    # rms_mean = np.mean(rms)
    # rms_sd = np.std(rms)
    return dynamics

# Spectral features
#Spectral Centroid indicates where the "center of mass" of the spectrum is located
# Spectral skewness indicates the asymmetry of the spectrum
# Negative Skewness (< 0): More energy in the high frequencies (e.g., bright, trebly sounds).
# Zero Skewness (≈ 0): Symmetrical distribution of spectral energy (e.g., white noise).
# Positive Skewness (> 0): More energy in the low frequencies (e.g., bass-heavy sounds).
# spectral flux indicates rate of change of the spectrum; corresponds to perceptual roughness of sound
# High spectral flux → Indicates rapid changes in the spectrum (e.g., drum hits, percussive sounds).
# Low spectral flux → Indicates a stable, smooth sound (e.g., sustained notes, ambient pads).
# Speech & vocals → Typically moderate spectral flux with periodic peaks at syllable transitions.
def spectral_features(x, fs):
    print(x.shape)
    spectral_cetroid = librosa.feature.spectral_centroid(y=x, sr=fs)
    spectral_tilt = librosa.feature.spectral_rolloff(y=x, sr=fs, roll_percent=0.85)
    spectral_bandwidth = librosa.feature.spectral_bandwidth(y=x, sr=fs)
    spectral_flatness = librosa.feature.spectral_flatness(y=x)
    spectral_flux = librosa.onset.onset_strength(y=x, sr=fs)
    mfcc = librosa.feature.mfcc(y=x, sr=fs)
    spectral_features = {
        "spectral_cetroid": spectral_cetroid,
        "spectral_tilt": spectral_tilt,
        "spectral_bandwidth": spectral_bandwidth,
        "spectral_flatness": spectral_flatness,
        "spectral_flux": spectral_flux,
        "mfcc": mfcc
    }
    # sc_mean = np.mean(sc)
    # sc_sd = np.std(sc)
    return spectral_features

def rms(x):
    return np.sqrt(np.mean(x**2))

# Spatial features
# Stereo width indicates the width of the stereo image
# Stereo imbalance indicates the imbalance between left and right channels
# mid sideration ratio indicates the balance between mid and side channels

def spatial_features(x,fs):
    print(x.shape)
    if x.shape[1] == 1:
        x = np.concatenate([x, x], axis=1)
    # compute sum and difference of channels
    sum_ = x[:,0] + x[:,1]
    diff = x[:,0] - x[:,1]
    # compute power of sum and difference
    sum_power = (rms(sum_))**2
    diff_power = (rms(diff))**2
    # add small value to avoid division by zero
    stereo_width = diff_power / (sum_power + 1e-8)
    left_power = (rms(x[:,0]))**2
    right_power = (rms(x[:,1]))**2
    stereo_imbalance = (right_power-left_power)/ (right_power+left_power + 1e-8)
    mid = (x[:,0] + x[:,1]) / 2
    side = (x[:,0] - x[:,1]) / 2
    mid_power = (rms(mid))**2
    side_power = (rms(side))**2
    midside_ratio = mid_power / (side_power + 1e-8)
    spatial_features = {
        "stereo_width": stereo_width,
        "stereo_imbalance": stereo_imbalance,
        "midside_ratio": midside_ratio
    }
    return spatial_features
# Tonal Centroid (or Harmonic Centroid): Reflects the overall harmonic balance of the mix,
#  indicating if the mix is more bass-heavy or treble-heavy.
# Harmonic-to-Noise Ratio (HNR): Indicates the amount of harmonic versus non-harmonic content in a signal,
#  useful for detecting how much distortion or noise is introduced in the mix.
def tonal_features(x, fs):
    print(x.shape)
    harmonic, _ = librosa.effects.hpss(x)  # Harmonic-to-Noise Ratio calculation
    noise = x - harmonic
    hnr = np.mean(np.abs(harmonic) / (np.abs(noise) + 1e-6))  # Harmonic-to-noise ratio
    tonal_centroid = librosa.feature.tonnetz(y=x)  # Tonal centroid using Tonnetz
    tonal_features = {
        "hnr": hnr,
        "tonal_centroid": tonal_centroid
    }
    return tonal_features

def convert_to_wav(song_path):
    if os.path.exists(song_path.replace(".mp3", ".wav")):
        os.remove(song_path.replace(".mp3", ".wav"))
    # convert to wav at 44.1kHz and 16 bit; preserve the stereo channels; dont replace the mp3 file
    os.system(f'ffmpeg -i {song_path} -acodec pcm_s16le -ar 44100 {song_path.replace(".mp3", ".wav")}')

    # 
        
# as of now this code is adapted for mini mixing secrets excerpt dataset stored in soumya
#  home folder on server 2
# under Mixing_secret_test_set/dataset
def collect_path_rough_mix_full(dataset_path):       
    all_songs = glob.glob(dataset_path + '/*')
    rough_excerptmix = {}
    for song in all_songs:
        rough_excerptmix[os.path.basename(song)] = {}
        rough_excerptmix[os.path.basename(song)]['rough_mix'] = os.path.join(song, "aligned", "rough_mix.wav")
        rough_excerptmix[os.path.basename(song)]['excerpt'] = os.path.join(song, "excerpt_mix_previews/excerpt_mix_preview.mp3")
        if (rough_excerptmix[os.path.basename(song)]['excerpt'].endswith('.wav')):
            print(rough_excerptmix[os.path.basename(song)]['excerpt'] )
    # print(rough_excerptmix)
    return rough_excerptmix
# this is adapted to the full dataset from mixing secrets (only for songs with excerpt_mixes available)
# def select_section_max_activity(x, fs, section_duration=30):
#     window = int(fs * section_duration)
#     hop = int(fs *2)
#     rms = librosa.feature.rms(y=x, frame_length=window, hop_length=hop)
#     # avg across channels
#     rms = np.mean(rms, axis=0)
#     print(rms.shape)
#     print(rms)
#     # find the section where rms is closest to avg rms
#     avg_rms = np.mean(rms)
#     print("avg rms", avg_rms)
#     # find the index where rms is closest to avg rms
#     target_index = [i for i, val in enumerate(rms) if np.argmin(np.abs(val-avg_rms))][0]
#     print("target index", target_index)
#     start_time = target_index*fs
#     end_time = start_time+ window
#     print("start time", start_time, "end time", end_time)

#     return x[:,start_time:end_time]


def extract_features(audio_path, sr=44100):
    # convert to wav
    # if audio_path.endswith('.mp3'):
    #     convert_to_wav(audio_path)
    # # # read audio file
    # audio_path = audio_path.replace(".mp3", ".wav")
    x, fs = librosa.load(audio_path, sr=sr, mono=False)
    print(x.shape, fs)
    # check if the sample rate is 44.1kHz
    if fs != 44100:
        print('Sample rate is not 44.1kHz')
        # resample to 44.1kHz
        x = librosa.resample(x, fs, 44100)
    # loudness normalise
    meter = pyln.Meter(sr)
    loudness = meter.integrated_loudness(x.T)
    x = pyln.normalize.loudness(x.T, loudness, -15.0)
    # print(x.T)
    x = x.T




    # # trim to 30 seconds
    # x = x[:, :sr*30]
    # if mono, convert to stereo
    if x.ndim == 1:
        x = np.vstack([x, x])
    # extract features
    audio_feature={}
    print("dynamic features")
    audio_feature['dynamics'] = dynamics(x, fs)
    print("spectral features")
    audio_feature['spectral'] = spectral_features(x, fs)
    print("spatial features")
    audio_feature['spatial'] = spatial_features(x, fs)
    print("tonal features")
    audio_feature['tonal'] = tonal_features(x, fs)

    return audio_feature

def main():
    # we will generate features only for mixes with excerpts available and no rough mix for now. 
    dataset_path = "/data3/share/soumya/Mixing_Secrets_Full/"
    all_excerpt_mixes = glob.glob(os.path.join(dataset_path,"*", "full_mix_previews", "*.mp3"))
    print(len(all_excerpt_mixes))
    pickle_name = input("Press Enter the pickle file name for storing feature data : ")

    # rough_excerptmix = collect_path_rough_mix(dataset_path)
    for path in tqdm(all_excerpt_mixes):
        song_path = os.path.dirname(path).replace("full_mix_previews", "aligned")
        # print(song_path)

        # check if the feature file already exists
        # if(os.path.exists(os.path.join(dataset_path , song ,'aligned/features.pkl'))):
        #     print("features already extracted for ", song)
        #     continue
        print("Extracting features for ", path)
        features = {}
        features["full_mix"] = extract_features(path)
        # save features
        with open(os.path.join(song_path,f'{pickle_name}_loudnorm.pkl'), 'wb') as f:
            pickle.dump(features, f)
        print("Features saved for ", path)


if __name__ == '__main__':
    main()

