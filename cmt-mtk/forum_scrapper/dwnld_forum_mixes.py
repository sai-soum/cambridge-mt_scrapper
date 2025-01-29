import os
import json
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import glob
import time

def create_directory(path):
    """Create a directory if it doesn't already exist."""
    if not os.path.exists(path):
        os.makedirs(path)

def download_audio_file(thread, song_path):
    """Download an audio file from a thread."""
    file_name = os.path.join(song_path, thread["Thread Author"] + ".mp3")
    
    if os.path.exists(file_name):
        print(f"Audio file '{file_name}' already exists.")
        return

    url = thread['Thread Link']
    try:
        page = requests.get(url).content
        page_soup = BeautifulSoup(page, 'html.parser')
        audio_element = page_soup.find("audio")

        if audio_element:
            audio_source = audio_element.find("source")["src"]
            audio_response = requests.get(audio_source, stream=True)
            total_size = int(audio_response.headers.get('content-length', 0))
            downloaded_size = 0

            with open(file_name, "wb") as f, tqdm(
                desc=f"Downloading {thread['Thread Author']} - {os.path.basename(song_path)}",
                total=total_size,
                unit="B",
                unit_scale=True
            ) as pbar:
                for chunk in audio_response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
                        downloaded_size += len(chunk)

            print(f"Audio file downloaded successfully as '{file_name}'.")
        else:
            print(f"No audio element found on the page: {url}")

    except Exception as e:
        print(f"Failed to download audio file for {thread['Thread Author']}: {e}")

def download_audio_for_song(song, value, dataset_path):
    """Download all audio files for a song."""
    song_path = os.path.join(dataset_path, song)
    create_directory(song_path)

    threads = value['threads']
    if len(threads) == len(glob.glob(song_path + "/*")):
        print(f"All audio files for '{song}' already downloaded.")
        return

    print(f"Downloading audio files for the song: {song}")
    with ThreadPoolExecutor(max_workers=4) as executor:
        executor.map(lambda t: download_audio_file(t, song_path), threads)

def main():
    # Load the JSON file containing information about the forum, threads, and posts
    json_path = input("Enter the path to the JSON file containing the scraped forum metadata: ") or "/home/soumya/cambridge-mt_scrapper/data/forum/5_data.json"
    # "/Users/svanka/Codes/Cambridge_Scraper/6(rock_metal)_data.json"
    with open(json_path) as f:
        data = json.load(f)

    dataset = os.path.basename(json_path).split(".")[0]
    audio_dir = input(f"Enter the directory to save audio files for the dataset '{dataset}': ") or "data/audio/forum"
    create_directory(audio_dir)

    dataset_path = os.path.join(audio_dir, dataset)
    create_directory(dataset_path)

    print(f"Processing {len(data)} songs in the dataset '{dataset}'...")

    for song, value in data.items():
        download_audio_for_song(song, value, dataset_path)

if __name__ == "__main__":
    main()
