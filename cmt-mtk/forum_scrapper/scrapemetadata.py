
#  This is the one to use


import requests
from bs4 import BeautifulSoup
import json
import os
import time
import random
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Configure headers to mimic a real browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.google.com/'
}

# Use a session for persistent connection
session = requests.Session()
session.headers.update(HEADERS)

# Optional: Proxy support (set to True if needed)
USE_PROXY = False
PROXIES = {
    "http": "http://your_proxy_here",
    "https": "https://your_proxy_here",
}

def fetch_url(url, use_selenium=False):
    """Fetch the HTML content of a URL with retries and optional Selenium fallback."""
    max_retries = 3
    delay = random.uniform(2, 5)  # Randomized delay to prevent detection
    
    for attempt in range(max_retries):
        try:
            time.sleep(delay)  # Add delay before making a request

            if use_selenium:
                print(f"Fetching {url} using Selenium...")
                return fetch_with_selenium(url)

            print(f"Fetching {url} (attempt {attempt + 1}/{max_retries})...")
            response = session.get(url, proxies=PROXIES if USE_PROXY else None, timeout=10)
            response.raise_for_status()
            return response.content  # Return raw HTML
        
        except requests.exceptions.RequestException as e:
            print(f"Request failed ({attempt + 1}/{max_retries}): {e}")
            time.sleep(5)  # Wait before retrying
            
    print(f"Failed to fetch {url} after {max_retries} attempts.")
    return None

def fetch_with_selenium(url):
    """Use Selenium to fetch the page source."""
    options = Options()
    options.headless = True  # Run in headless mode
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url)
    time.sleep(5)  # Wait for page to load
    html = driver.page_source
    driver.quit()
    return html

def find_song_names_forumlink(soup):
    """Extract song names and forum links from the page."""
    strong_tags = soup.find_all('strong')
    song_dict = {}

    for strong_tag in tqdm(strong_tags):
        a_tag = strong_tag.find('a')
        if a_tag:
            forum_link = "https://discussion.cambridge-mt.com/" + a_tag['href']
            song_name = a_tag.get_text()
            song_dict[song_name] = {'forum_link': forum_link}
    
    print(f"{len(song_dict)} songs found.")
    return song_dict

def find_thread_info(song_dict):
    """Extract thread details (title, author, rating, views) from each song's forum page."""
    for key, value in tqdm(song_dict.items()):
        song_forum_url = value['forum_link']
        song_forum_html = fetch_url(song_forum_url, use_selenium=False)  # Try normal request first
        
        if not song_forum_html:  # If request fails, use Selenium
            song_forum_html = fetch_url(song_forum_url, use_selenium=True)
            if not song_forum_html:
                print(f"Skipping {song_forum_url} due to persistent failure.")
                continue

        song_forum_soup = BeautifulSoup(song_forum_html, 'html.parser')
        pages_element = song_forum_soup.find('span', class_='pages')
        pages_number = int(pages_element.get_text(strip=True).split('(')[1].split(')')[0]) if pages_element else 1
        
        threads = []
        for i in range(1, pages_number + 1):
            page_url = song_forum_url if i == 1 else f"{song_forum_url}&page={i}"
            song_forum_html = fetch_url(page_url, use_selenium=False)
            
            if not song_forum_html:
                continue  # Skip page if request fails

            song_forum_soup = BeautifulSoup(song_forum_html, 'html.parser')
            mixes = song_forum_soup.find_all('tr', class_='inline_row')

            for row in mixes:
                
              
                try:
                    thread_link = row.find('span', class_='subject_new').a['href']
                except:
                    thread_link = "none"
                try:
                    thread_title = row.find('span', class_='subject_new').text
                except:
                    thread_title = "none"
                try:
                    thread_author = row.find('span', class_='author smalltext').a.text
                    # print(thread_author)
                except:
                    thread_author = "none"
                try:
                    thread_time = row.find('span', class_='thread_start_datetime smalltext').text.strip()
                    
                except:
                    thread_time = "none"
                try:
                    thread_rating = row.find('ul', class_='star_rating').find('li').text.strip()
                except:
                    thread_rating = "none"
                try:
                    thread_views = row.find_all('td', class_='trow1')[4].text.strip()
                except:
                    thread_views = "none"

                threads.append({
                    'Thread Link': thread_link,
                    'Thread Title': thread_title,
                    'Thread Author': thread_author,
                    'Thread Time': thread_time,
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
    # url = input("Enter the URL of the Genre forum to scrape metadata: ") or 'https://discussion.cambridge-mt.com/forumdisplay.php?fid=6'
    # list of the url with i from 2 to 7

    urls = [
            'https://discussion.cambridge-mt.com/forumdisplay.php?fid=3',
            'https://discussion.cambridge-mt.com/forumdisplay.php?fid=4',
            'https://discussion.cambridge-mt.com/forumdisplay.php?fid=5',
            'https://discussion.cambridge-mt.com/forumdisplay.php?fid=6',
            'https://discussion.cambridge-mt.com/forumdisplay.php?fid=7']
    for url in urls:
        print("Fetching forum page...")
        forum_html = fetch_url(url, use_selenium=False)

        if not forum_html:
            forum_html = fetch_url(url, use_selenium=True)  # Try Selenium if normal request fails
            if not forum_html:
                print("Failed to fetch the forum page. Exiting.")
                exit()

        soup = BeautifulSoup(forum_html, 'html.parser')
        file_name = soup.title.string.strip() + ".json"
        save_dir = os.path.join('/data4/soumya/MSF_forum/metadata', file_name)

        print("Scraping metadata from", file_name.replace(".json", ""))
        song_dict = find_song_names_forumlink(soup)
        save_metadata(save_dir, song_dict)

        print("Finding thread information...")
        song_dict_with_threads_info = find_thread_info(song_dict)
        save_metadata(save_dir, song_dict_with_threads_info)
