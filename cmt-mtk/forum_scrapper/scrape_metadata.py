#  The script will take the link to a miuxing forum specific to a genre and collect data 

import requests
from bs4 import BeautifulSoup
import json
import os
from tqdm import tqdm

def find_song_names_forumlink(soup):
        # Find all <strong> tags containing song names and usernames
    strong_tags = soup.find_all('strong')
    aaa_tags = soup.find_all('a')
    # print(aaa_tags)
    #if the aaa_tags['href'] is a url, then add to the list of urls
    url = []
    #create a dictionary to store the song names and the urls to the forums pertaining to the song
    song_dict = {}
    # Extract links to forums with song names and usernames
    for strong_tag in tqdm(strong_tags):
        a_tag = strong_tag.find('a')
        #print(a_tag)
        if a_tag:
            forum_link = "https://discussion.cambridge-mt.com/" + a_tag['href']
            song_name = a_tag.get_text()
            song_dict[song_name] = {}
            song_dict[song_name]['forum_link'] = forum_link
    # print(song_dict)
    print(len(song_dict), "songs found.")
    return song_dict

def find_thread_info(song_dict):
    for key, value in tqdm(song_dict.items()):
    # Extracting the number of pages
        song_forum_url = value['forum_link']
        
        song_forum_html = requests.get(song_forum_url).content
        song_forum_soup = BeautifulSoup(song_forum_html, 'html.parser')
        # Extracting the number of pages
        pages_element = song_forum_soup.find('span', class_='pages')
        if pages_element:
            pages_text = pages_element.get_text(strip=True)
            # Extracting the number of pages from the text
            pages_number = int(pages_text.split('(')[1].split(')')[0])
            # print("Number of pages:", pages_number)
        else:
            print("No page information found.")
        threads = []
        #parse through all the pages and add it to html
        for i in range(1, pages_number + 1):

            if i == 1:
                song_forum_url = value['forum_link']
            else:
                song_forum_url = value['forum_link'] + "&page=" + str(i)
            song_forum_html = requests.get(song_forum_url).content
            song_forum_soup = BeautifulSoup(song_forum_html, 'html.parser')
            mixes = song_forum_soup.find_all('tr', class_='inline_row')

            # Extracting data
        
            for row in mixes:
                try:
                    thread_link = row.find('span', class_='subject_new').a['href']
                except:
                    thread_link = "none"
                try:
                    #print(thread_link)
                    thread_title = row.find('span', class_='subject_new').text
                except:
                    thread_title = "none"
                    #print(thread_title)
                try:
                    thread_author_link = row.find('div', class_='author').a['href']
                except:
                    thread_author_link = "none"
                try:
                    thread_author = row.find('div', class_='author').a.text
                except:
                    thread_author = "none"
                try:
                    #print(thread_author)
                    thread_rating = row.find('ul', class_='star_rating').find('li').text.strip()
                except:
                    thread_rating = "none"

                #print(thread_rating)
                try:
                    thread_views = row.find_all('td', class_='trow1')[4].text.strip()
                except:
                    thread_views = row.find_all('td', class_='trow2')[4].text.strip()
                #print(thread_views)
                
                
                threads.append({
                    'Thread Link': thread_link,
                    'Thread Title': thread_title,
                    'Thread Author': thread_author,
                    'Thread Author Link': thread_author_link,
                    'Thread Rating': thread_rating,
                    'Thread Views': thread_views
                })
        # print("number of threads found:", len(threads))
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
    #insert the url of the mixing forum from Cambridge MT that you want to scrape
    #find the forum here: https://discussion.cambridge-mt.com/forumdisplay.php?fid=184 
    # this is the url specific for a genre
    url = input("Enter the URL of the Genre forum to scrape metadata, check here (https://discussion.cambridge-mt.com/forumdisplay.php?fid=184) ") or 'https://discussion.cambridge-mt.com/forumdisplay.php?fid=6'
    # url = "https://discussion.cambridge-mt.com/forumdisplay.php?fid=6"
    #get the html content of the page
    html = requests.get(url).content
    # print(html.decode("utf-8"))
    # Parse the HTML content
    soup = BeautifulSoup(html, 'html.parser')
    file_name = soup.title.string.strip() + ".json"
    save_dir = os.path.join('data/forum', file_name)
    # if os.path.exists(save_dir) is False:
    #     os.makedirs(os.path.dirname(save_dir), exist_ok=True)
    print("Scraping metadata from", file_name.replace(".json", ""))
    print("finding song names and forum links")
    song_dict = find_song_names_forumlink(soup)
    save_metadata(save_dir, song_dict)
    print("Finding thread information")
    #now we will extract the link to the threads within a song forum along with the number of views, ratings (between 0-5) and the author of the thread
    song_dict_with_threads_info = find_thread_info(song_dict)
    #write to a json file which will be later used to download audio files
    # create a json file to save the song_dict
    save_metadata(save_dir, song_dict_with_threads_info)
 