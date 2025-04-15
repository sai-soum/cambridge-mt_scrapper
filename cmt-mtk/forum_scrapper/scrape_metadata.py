import requests
from bs4 import BeautifulSoup
import json
import os
import time
from tqdm import tqdm
from tenacity import retry, wait_exponential, stop_after_attempt

# Define a user-agent to mimic a real browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Retry failed requests with exponential backoff
@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(5))
def fetch_url(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

def find_song_names_forumlink(soup):
    """Find all songs and their respective forum links."""
    strong_tags = soup.find_all('strong')
    song_dict = {}

    for strong_tag in tqdm(strong_tags, desc="Extracting song names and links"):
        a_tag = strong_tag.find('a')
        if a_tag:
            forum_link = "https://discussion.cambridge-mt.com/" + a_tag['href']
            song_name = a_tag.get_text()
            song_dict[song_name] = {'forum_link': forum_link}

    print(f"{len(song_dict)} songs found.")
    return song_dict

def find_thread_info(song_dict):
    """Find threads, authors, ratings, and views for each song."""
    for key, value in tqdm(song_dict.items(), desc="Scraping thread data"):
        song_forum_url = value['forum_link']
        time.sleep(1)  # Slow down requests

        song_forum_html = fetch_url(song_forum_url)
        if not song_forum_html:
            print(f"Skipping {key} due to request failure.")
            continue

        song_forum_soup = BeautifulSoup(song_forum_html, 'html.parser')
        pages_element = song_forum_soup.find('span', class_='pages')
        
        pages_number = 1
        if pages_element:
            try:
                pages_text = pages_element.get_text(strip=True)
                pages_number = int(pages_text.split('(')[1].split(')')[0])
            except ValueError:
                print(f"Could not parse pages for {key}, defaulting to 1.")

        threads = []

        for i in range(1, pages_number + 1):
            page_url = value['forum_link'] if i == 1 else f"{value['forum_link']}&page={i}"
            time.sleep(1)  # Slow down requests

            page_html = fetch_url(page_url)
            if not page_html:
                print(f"Skipping page {i} for {key} due to request failure.")
                continue

            page_soup = BeautifulSoup(page_html, 'html.parser')
            mixes = page_soup.find_all('tr', class_='inline_row')
            print(mixes)

            for row in mixes:
                try:
                    thread_link = row.find('span', class_='subject_new').a['href']
                except AttributeError:
                    thread_link = "none"
                
                try:
                    thread_title = row.find('span', class_='subject_new').text.strip()
                except AttributeError:
                    thread_title = "none"

                try:
                    thread_author_link = row.find('div', class_='author').a['href']
                except AttributeError:
                    thread_author_link = "none"
                
                try:
                    thread_author = row.find('div', class_='author').a.text.strip()
                except AttributeError:
                    thread_author = "none"

                try:
                    thread_rating = row.find('ul', class_='star_rating').find('li').text.strip()
                except AttributeError:
                    thread_rating = "none"

                try:
                    thread_views = row.find_all('td', class_='trow1')[4].text.strip()
                except (AttributeError, IndexError):
                    try:
                        thread_views = row.find_all('td', class_='trow2')[4].text.strip()
                    except (AttributeError, IndexError):
                        thread_views = "none"

                threads.append({
                    'Thread Link': thread_link,
                    'Thread Title': thread_title,
                    'Thread Author': thread_author,
                    'Thread Author Link': thread_author_link,
                    'Thread Rating': thread_rating,
                    'Thread Views': thread_views
                })

        song_dict[key]['threads'] = threads
    return song_dict

def save_metadata(file_name, data):
    """Save the metadata to a JSON file."""
    try:
        with open(file_name, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"Metadata saved to {file_name}.")
    except Exception as e:
        print(f"Error saving metadata to {file_name}: {e}")

if __name__ == "__main__":
    url = input("Enter the URL of the Genre forum to scrape metadata: ") or 'https://discussion.cambridge-mt.com/forumdisplay.php?fid=6'

    print("Fetching forum page...")
    html = fetch_url(url)
    if not html:
        print("Failed to fetch the forum page. Exiting.")
        exit(1)

    soup = BeautifulSoup(html, 'html.parser')
    file_name = soup.title.string.strip() + ".json"
    save_dir = os.path.join('/data4/soumya/MSF_forum/metadata', file_name)

    print(f"Scraping metadata from {file_name.replace('.json', '')}...")
    song_dict = find_song_names_forumlink(soup)
    save_metadata(save_dir, song_dict)

    print("Finding thread information...")
    song_dict_with_threads_info = find_thread_info(song_dict)
    save_metadata(save_dir, song_dict_with_threads_info)
