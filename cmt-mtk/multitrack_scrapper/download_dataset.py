
import os
import requests
import shutil
import pandas as pd
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor
import zipfile
import time
import glob


def download_file_part(url, start, end, part_index, output_path, progress_bars):
    """
    Download a specific range of bytes (a part) from the file.
    Updates the progress bar for that part.
    """
    headers = {'Range': f'bytes={start}-{end}'}
    with requests.get(url, headers=headers, stream=True) as response:
        response.raise_for_status()
        part_path = f"{output_path}.part{part_index}"
        with open(part_path, "wb") as part_file:
            downloaded = 0
            total = end - start + 1
            last_time = time.time()
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    part_file.write(chunk)
                    downloaded += len(chunk)
                    # Update progress bar
                    current_time = time.time()
                    speed = len(chunk) / (current_time - last_time + 1e-5)  # Avoid division by zero
                    progress_bars[part_index].update(len(chunk))
                    progress_bars[part_index].desc = f"Part {part_index + 1}: {downloaded / (1024 ** 2):.2f}MB/{total / (1024 ** 2):.2f}MB @ {speed / 1024:.2f} KB/s"
                    last_time = current_time


def download_file_with_progress(url, output_path, num_parts=4):
    """
    Download a file using multiple parts with progress tracking for each part.
    """
    # Get file size
    response = requests.head(url, allow_redirects=True)
    total_size = int(response.headers.get('content-length', 0))
    if total_size == 0:
        raise Exception("Failed to fetch file size. URL might be invalid or server does not support ranged requests.")

    # Split file into parts
    part_size = total_size // num_parts
    ranges = [(i * part_size, (i + 1) * part_size - 1) for i in range(num_parts)]
    ranges[-1] = (ranges[-1][0], total_size - 1)  # Ensure the last part includes any leftover bytes

    # Create progress bars for each part
    progress_bars = [
        tqdm(total=(end - start + 1), position=i + 1, leave=False, desc=f"Part {i + 1}")
        for i, (start, end) in enumerate(ranges)
    ]

    # Download each part sequentially using threads
    with ThreadPoolExecutor(max_workers=1) as executor:
        futures = [
            executor.submit(download_file_part, url, start, end, idx, output_path, progress_bars)
            for idx, (start, end) in enumerate(ranges)
        ]
        for future in futures:
            future.result()  # Wait for each part to finish

    # Close progress bars
    for bar in progress_bars:
        bar.close()

    # Merge parts
    with open(output_path, "wb") as output_file:
        for idx in range(num_parts):
            part_path = f"{output_path}.part{idx}"
            with open(part_path, "rb") as part_file:
                shutil.copyfileobj(part_file, output_file)
            os.remove(part_path)  # Clean up part files


def extract_zip_file(zip_path, output_folder):
    """
    Extract a zip file into the specified output folder and delete the zip file.
    """
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(output_folder)
        os.remove(zip_path)
        print(f"Extracted and removed zip: {zip_path}")
    except Exception as e:
        print(f"Failed to extract {zip_path}: {e}")


def handle_track_download(row, dl_dir, full, preview, excerpt, excerpt_preview, num_parts=4):
    """
    Handle downloading for a single track, including full multitracks and previews.
    """
    track_name = row["Track Name"]
    track_folder = os.path.join(dl_dir, track_name)
    os.makedirs(track_folder, exist_ok=True)
    if len(glob.glob(track_folder + '/*')) == 4:
        print(f"Track {track_name} already downloaded.")
        return

    # Subfolder paths
    subfolders = {
        "Full Multitrack": os.path.join(track_folder, "full_multitrack"),
        "Mix Previews": os.path.join(track_folder, "mix_previews"),
        "Excerpt Multitrack": os.path.join(track_folder, "excerpt_multitrack"),
        "Excerpt Mix Previews": os.path.join(track_folder, "excerpt_mix_previews"),
    }
    for folder in subfolders.values():
        os.makedirs(folder, exist_ok=True)

    # Download full multitrack
    if full.lower() == "y" and pd.notna(row["Full Multitrack Link"]):
        full_multitrack_path = os.path.join(subfolders["Full Multitrack"], "full_multitrack.zip")
        print(f"Downloading Full Multitrack: {track_name}")
        try:
            download_file_with_progress(row["Full Multitrack Link"], full_multitrack_path, num_parts=num_parts)
            extract_zip_file(full_multitrack_path, subfolders["Full Multitrack"])
        except Exception as e:
            print(f"Failed to download Full Multitrack for {track_name}: {e}")

    # Download mix previews
    if preview.lower() == "y" and pd.notna(row["Full Mix Preview"]):
        mix_preview_path = os.path.join(subfolders["Mix Previews"], "mix_preview.mp3")
        print(f"Downloading Mix Preview: {track_name}")
        try:
            download_file_with_progress(row["Full Mix Preview"], mix_preview_path, num_parts=num_parts)
        except Exception as e:
            print(f"Failed to download Mix Preview for {track_name}: {e}")

    # Download excerpt multitrack
    if excerpt.lower() == "y" and pd.notna(row["Excerpt Multitrack Link"]):
        excerpt_multitrack_path = os.path.join(subfolders["Excerpt Multitrack"], "excerpt_multitrack.zip")
        print(f"Downloading Excerpt Multitrack: {track_name}")
        try:
            download_file_with_progress(row["Excerpt Multitrack Link"], excerpt_multitrack_path, num_parts=num_parts)
            extract_zip_file(excerpt_multitrack_path, subfolders["Excerpt Multitrack"])
        except Exception as e:
            print(f"Failed to download Excerpt Multitrack for {track_name}: {e}")

    # Download excerpt mix previews
    if excerpt_preview.lower() == "y" and pd.notna(row["Excerpt Mix Preview"]):
        excerpt_mix_preview_path = os.path.join(subfolders["Excerpt Mix Previews"], "excerpt_mix_preview.mp3")
        print(f"Downloading Excerpt Mix Preview: {track_name}")
        try:
            download_file_with_progress(row["Excerpt Mix Preview"], excerpt_mix_preview_path, num_parts=num_parts)
        except Exception as e:
            print(f"Failed to download Excerpt Mix Preview for {track_name}: {e}")


if __name__ == "__main__":
    import subprocess

    # Prompt the user for settings
    DL_DIR = input("Enter the download directory (default is './data/multitrack_website/'): ") or './data/multitrack_website/'
    FULL_MULTITRACK = input("Download full multitracks? (y/n) (default is y): ") or 'y'
    MIX_PREVIEWS = input("Download mix previews? (y/n) (default is y): ") or 'y'
    EXCERPT_MULTITRACK = input("Download excerpt multitracks, if exists? (y/n) (default is n): ") or 'n'
    EXCERPT_MIX_PREVIEWS = input("Download excerpt mix previews, if exists? (y/n) (default is n): ") or 'n'
    UPDATE_METADATA = input("Update metadata.csv? (y/n) (default is n): ") or 'n'

    # Check and update metadata
    if os.path.exists('data/multitrack_website/metadata.csv') and UPDATE_METADATA.lower() == 'n':
        metadata_csv = pd.read_csv('data/multitrack_website/metadata.csv')
    else:
        subprocess.call("python cmt-mtk/multitrack_scrapper/scrape_metadata.py", shell=True)
        metadata_csv = pd.read_csv('data/multitrack_website/metadata.csv')

    print(f"Downloading {len(metadata_csv)} multitracks from Cambridge Multitrack website...")

    # Sequential download
    for _, row in tqdm(metadata_csv.iterrows(), total=len(metadata_csv), desc="Tracks"):
        handle_track_download(row, DL_DIR, FULL_MULTITRACK, MIX_PREVIEWS, EXCERPT_MULTITRACK, EXCERPT_MIX_PREVIEWS)

    print("\nDownload completed.")
