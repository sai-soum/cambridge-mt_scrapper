import os
import json
import requests
import sys
from requests.adapters import HTTPAdapter, Retry
from bs4 import BeautifulSoup
from tqdm import tqdm
import time
import random

# Global counters
fail_count = 0

# Configure retry logic
session = requests.Session()
retries = Retry(total=5, backoff_factor=2, status_forcelist=[500, 502, 503, 504, 104])
session.mount("https://", HTTPAdapter(max_retries=retries))

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def create_directory(path):
    """Create a directory if it doesn't already exist."""
    os.makedirs(path, exist_ok=True)

def download_audio_file(thread, song_path):
    """Download an audio file from a thread."""
    global fail_count

    file_name = os.path.join(song_path, f"{thread['Thread Author']}.mp3")
    
    if os.path.exists(file_name) and os.path.getsize(file_name) > 1024:
        return True  # File already exists

    url = "https://discussion.cambridge-mt.com/" + thread['Thread Link']

    for attempt in range(5):
        try:
            response = session.get(url, headers=HEADERS, timeout=10)
            if response.status_code == 400:
                fail_count += 1
                if fail_count >= 5:
                    print("Too many 400 errors. Exiting...")
                    sys.exit(1)  # Exit so Bash script can restart
                return False

            response.raise_for_status()
            page_soup = BeautifulSoup(response.content, 'html.parser')
            audio_element = page_soup.find("audio")

            if not audio_element:
                print(f"No audio found for {thread['Thread Author']}.")
                # remove the entry
                
                return False

            audio_source = audio_element.find("source")
            if not audio_source or "src" not in audio_source.attrs:
                print(f"No audio source found for {thread['Thread Author']}.")
                return False

            audio_url = audio_source["src"]
            audio_response = session.get(audio_url, stream=True, headers=HEADERS, timeout=10)
            audio_response.raise_for_status()

            total_size = int(audio_response.headers.get('content-length', 0))

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

            return True

        except requests.exceptions.RequestException as e:
            print(f"Error downloading {thread['Thread Author']}: {e}")
            time.sleep(2 ** attempt + random.uniform(0.5, 1.5))

    return False

def download_audio_for_song(song, value, dataset_path):
    """Download all audio files for a song."""
    song_path = os.path.join(dataset_path, song)
    create_directory(song_path)

    valid_threads = [thread for thread in value['threads'] if download_audio_file(thread, song_path)]
    return valid_threads

def clean_json(json_path, dataset_path):
    """Remove songs that didn't have valid audio from JSON."""
    with open(json_path, "r") as f:
        data = json.load(f)

    updated_data = {song: {"threads": download_audio_for_song(song, value, dataset_path)} for song, value in data.items() if value['threads']}

    # Save cleaned JSON
    cleaned_json_path = json_path.replace(".json", "_cleaned.json")
    with open(cleaned_json_path, "w") as f:
        json.dump(updated_data, f, indent=4)

    print(f"Cleaned JSON saved at: {cleaned_json_path}")

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 download_script.py <json_path> <audio_directory>")
        sys.exit(1)

    json_path = sys.argv[1]
    audio_dir = sys.argv[2]

    dataset_name = os.path.basename(json_path).split(".")[0]
    dataset_path = os.path.join(audio_dir, dataset_name)
    create_directory(dataset_path)

    print(f"Processing dataset: {dataset_name}")
    clean_json(json_path, dataset_path)

if __name__ == "__main__":
    main()
