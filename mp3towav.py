from pydub import AudioSegment
import os
import glob

if __name__ == "__main__":
    # convert mp3 file to wav file

    audio_path = "/Users/svanka/Codes/cambridge-mt_scrapper/audio/6(rock_metal)_data"
    songs = os.listdir(audio_path)
    for song in songs:
        song_path = os.path.join(audio_path, song)
        if os.path.isdir(song_path):
            mp3_files = glob.glob(f"{song_path}/*.mp3")
            for mp3_file in mp3_files:
                sound = AudioSegment.from_mp3(mp3_file)
                wav_file = os.path.splitext(mp3_file)[0] + ".wav"
                sound.export(wav_file, format="wav")
                print(f"Converted {mp3_file} to {wav_file}")
        break
