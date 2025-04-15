import os
import json
import requests
from requests.adapters import HTTPAdapter, Retry
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import time
import glob

# Global variables to track download status
success_count = 0
fail_count = 0
# Setup a session with retry logic
session = requests.Session()
retries = Retry(
    total=5,  # Maximum retries
    backoff_factor=2,  # Exponential backoff (2s, 4s, 8s...)
    status_forcelist=[500, 502, 503, 504, 104],  # Retry on server errors & connection reset
)
session.mount("https://", HTTPAdapter(max_retries=retries))

# Add User-Agent to prevent server rejection
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def create_directory(path):
    """Create a directory if it doesn't already exist."""
    if not os.path.exists(path):
        os.makedirs(path)

def is_file_valid(file_path, expected_size):
    """Check if a downloaded file is complete."""
    return os.path.exists(file_path) and os.path.getsize(file_path) >= expected_size * 0.9  # Allow slight variation

# def download_audio_file(thread, song_path):
    """Download an audio file from a thread with retries and file validation."""
    file_name = os.path.join(song_path, thread["Thread Author"] + ".mp3")
    
    # Avoid re-downloading if file exists and is valid
    if os.path.exists(file_name) and os.path.getsize(file_name) > 1024:
        # print(f"Audio file '{file_name}' already exists and is valid.")
        return
    elif os.path.exists(file_name):  
        print(f"Corrupt or incomplete file found: {file_name}. Redownloading...")
        os.remove(file_name)  # Delete and redownload

    url = "https://discussion.cambridge-mt.com/" + thread['Thread Link']
    
    for attempt in range(5):  # Retry up to 5 times
        try:
            response = session.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            page_soup = BeautifulSoup(response.content, 'html.parser')
            audio_element = page_soup.find("audio")

            if audio_element:
                audio_source = audio_element.find("source")
                if audio_source and "src" in audio_source.attrs:
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

                    # Validate downloaded file
                    if is_file_valid(file_name, total_size):
                        print(f"Audio file downloaded successfully: '{file_name}'.")
                        success_count = success_count + 1
                        return
                    else:
                        print(f"File {file_name} is incomplete, retrying...")
                        os.remove(file_name)

            print(f"No audio element found on the page: {url}")
            return

        except requests.exceptions.RequestException as e:
            print(f"Error on attempt {attempt + 1} for {thread['Thread Author']}: {e}")
            # if error is 400, count and when count reaches 5, break
            fail_count = fail_count + 1
            if fail_count == 5:
                print("success_count: ", success_count)
                exit(0)
            time.sleep(2 ** attempt)  # Exponential backoff

    print(f"Failed to download audio after multiple attempts for {thread['Thread Author']}.")
import random

def download_audio_file(thread, song_path):
    """Download an audio file from a thread with retries and file validation."""
    file_name = os.path.join(song_path, thread["Thread Author"] + ".mp3")
    
    # Avoid re-downloading if file exists and is valid
    if os.path.exists(file_name) and os.path.getsize(file_name) > 1024:
        # print(f"Audio file '{file_name}' already exists and is valid.")
        return
    elif os.path.exists(file_name):  
        print(f"Corrupt or incomplete file found: {file_name}. Redownloading...")
        os.remove(file_name)  # Delete and redownload

    url = "https://discussion.cambridge-mt.com/" + thread['Thread Link']
    
    for attempt in range(5):  # Retry up to 5 times
        try:
            response = session.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            page_soup = BeautifulSoup(response.content, 'html.parser')
            audio_element = page_soup.find("audio")

            if audio_element:
                audio_source = audio_element.find("source")
                if audio_source and "src" in audio_source.attrs:
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

                    # Validate downloaded file
                    if is_file_valid(file_name, total_size):
                        print(f"Audio file {success_count + 1 } downloaded successfully: '{file_name}'.")
                        success_count = success_count + 1
                        return
                    else:
                        print(f"File {file_name} is incomplete, retrying...")
                        os.remove(file_name)

            print(f"No audio element found on the page: {url}")
            return

        except requests.exceptions.RequestException as e:
            print(f"Error on attempt {attempt + 1} for {thread['Thread Author']}: {e}")
            # if error is 400, count and when count reaches 5, break
            # if response.status_code == 400:
                # fail_count += 1
                # if fail_count == 5:
                #     print(f"Failed to download audio after multiple attempts for {thread['Thread Author']}.")
                #     # end the code
                #     print("successful downloads: ", success_count)
                #     break
            time.sleep(2 ** attempt + random.uniform(0.5, 1.5))  # Exponential backoff + small random delay

    print(f"Failed to download audio after multiple attempts for {thread['Thread Author']}.")

def download_audio_for_song(song, value, dataset_path):
    """Download all audio files for a song."""
    song_path = os.path.join(dataset_path, song)
    create_directory(song_path)

    threads = value['threads']
    if len(threads) == len(glob.glob(os.path.join(song_path, "*.mp3"))):
        print(f"All audio files for '{song}' already downloaded.")
        return

    print(f"Downloading audio files for the song: {song}")
    with ThreadPoolExecutor(max_workers=1) as executor:
        executor.map(lambda t: download_audio_file(t, song_path), threads)

def main():
    # Load the JSON file containing information about the forum, threads, and posts
    json_path = input("Enter the path to the JSON file containing the scraped forum metadata: ") or "/data4/soumya/MSF_forum/metadata/Discussion Zone - Alt Rock, Blues, Country Rock, Indie, Funk, Reggae.json"
    
    with open(json_path) as f:
        data = json.load(f)

    dataset = os.path.basename(json_path).split(".")[0]
    audio_dir = input(f"Enter the directory to save audio files for the dataset '{dataset}': ") or "/data4/soumya/MSF_forum/dataset"
    create_directory(audio_dir)

    dataset_path = os.path.join(audio_dir, dataset)
    create_directory(dataset_path)

    print(f"Processing {len(data)} songs in the dataset '{dataset}'...")

    for song, value in data.items():
        download_audio_for_song(song, value, dataset_path)

if __name__ == "__main__":
    main()
