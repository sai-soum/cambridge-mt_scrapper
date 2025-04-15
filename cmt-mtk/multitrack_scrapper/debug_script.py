import os
import shutil
import zipfile
import yaml
import numpy as np
import pandas as pd
import requests
import time
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor
from glob import glob
from os.path import join as opj

# Constants
DATASET_DIR = "/data4/soumya/Mixing_Secrets_Full"
METADATA_PATH = "/home/soumya/cambridge-mt_scrapper/data/multitrack_website/metadata_with_fine_genre.csv"
MAX_WORKERS = 4  # Number of parallel downloads

# Load metadata and convert to dictionary for fast lookup
METADATA = pd.read_csv(METADATA_PATH)
metadata_dict = {
    row["Track Name"]: (row["Excerpt Multitrack Link"], row["Full Multitrack Link"])
    for _, row in METADATA.iterrows()
}


def post_process_download(directory):
    """Unzip files and clean up unnecessary subdirectories."""
    for zip_file in glob(opj(directory, "*.zip")):
        # check if file is not zip  file
        if not zipfile.is_zipfile(zip_file):
            print(f"{zip_file} is not a valid zip file. Skipping...")
            continue
        with zipfile.ZipFile(zip_file, "r") as zip_ref:
            zip_ref.extractall(directory)
        os.remove(zip_file)  # Remove the zip file after extraction

    # Move all audio files to the main directory
    subdirs = [d for d in glob(opj(directory, "*")) if os.path.isdir(d) and "__MACOSX" not in d]

    if len(subdirs) > 1:
        main_dir = subdirs[0]
        for subdir in subdirs[1:]:
            for file in glob(opj(subdir, "*.wav")):
                shutil.move(file, main_dir)
            shutil.rmtree(subdir)  # Remove empty directories


def download_file_with_progress(url, output_path, max_retries=5, retry_delay=5):
    """Download a file with progress bar and retry mechanism."""
    temp_path = output_path + ".part"
    
    # Get file size
    try:
        response = requests.head(url, allow_redirects=True)
        total_size = int(response.headers.get("content-length", 0))
    except Exception as e:
        print(f"Error getting file size: {e}")
        return False

    # Check if partially downloaded file exists
    downloaded_size = os.path.getsize(temp_path) if os.path.exists(temp_path) else 0
    headers = {"Range": f"bytes={downloaded_size}-"} if downloaded_size > 0 else {}

    for attempt in range(max_retries):
        try:
            with requests.get(url, headers=headers, stream=True) as r:
                r.raise_for_status()
                with open(temp_path, "ab") as f, tqdm(
                    total=total_size, initial=downloaded_size, unit="B", unit_scale=True, desc="Downloading"
                ) as pbar:
                    for chunk in r.iter_content(chunk_size=1024 * 1024):
                        f.write(chunk)
                        pbar.update(len(chunk))
            os.rename(temp_path, output_path)  # Rename to final file
            return True
        except requests.exceptions.RequestException as e:
            print(f"Download error: {e}. Retrying in {retry_delay}s...")
            time.sleep(retry_delay)

    print(f"Failed to download {url} after {max_retries} attempts.")
    return False


def process_song(song_path):
    """Check if excerpts/full multitracks exist, and download if missing."""
    song_name = os.path.basename(song_path)
    excerpt_path = opj(song_path, "excerpt_multitrack")
    full_path = opj(song_path, "full_multitrack")

    # Ensure directories exist
    os.makedirs(excerpt_path, exist_ok=True)
    os.makedirs(full_path, exist_ok=True)

    excerpt_subdirs = glob(opj(excerpt_path, "*/"))
    full_subdirs = glob(opj(full_path, "*/"))

    failed_downloads = {"excerpt": None, "full": None}

    excerpt_link, full_link = metadata_dict.get(song_name, (None, None))
    print(f"Processing {song_name}...")
    print(f"Excerpt: {excerpt_link}")
    print(f"Full: {full_link}")

    if not excerpt_subdirs and isinstance(excerpt_link, str):
        if download_file_with_progress(excerpt_link, opj(excerpt_path, "excerpt_multitrack.zip")):
            print(excerpt_path)
            post_process_download(excerpt_path)
        else:
            failed_downloads["excerpt"] = song_name

    if not full_subdirs and isinstance(full_link, str):
        if download_file_with_progress(full_link, opj(full_path, "full_multitrack.zip")):
            print(full_path)
            post_process_download(full_path)
        else:
            failed_downloads["full"] = song_name

    return failed_downloads


def main():
    song_dirs = glob(opj(DATASET_DIR, "*"))
    print(f"Found {len(song_dirs)} songs")

    failed_downloads = {"excerpt": [], "full": []}

    # Use ThreadPoolExecutor for parallel downloads
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = list(tqdm(executor.map(process_song, song_dirs), total=len(song_dirs), desc="Processing Songs"))

    # Collect failed downloads
    for result in results:
        if result["excerpt"]:
            failed_downloads["excerpt"].append(result["excerpt"])
        if result["full"]:
            failed_downloads["full"].append(result["full"])

    # Save failed directories
    with open("data/failed_dir.yaml", "w") as f:
        yaml.dump(failed_downloads, f)

    print("Failed directories saved in data/failed_dir.yaml")


if __name__ == "__main__":
    main()
