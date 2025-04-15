
# a web scrapper to collect metadat into a csv file genre, extract the song names, genre, link for full multitrack, excerpt multitrack,
#  mix previews for multitrack and excerpt, unmastered mix(if available) artist name, genre, sub genre,
#  number of tracks in excert and full multitrack, and the number of bars
#  in the excerpt and full multitrack, links to mixing and mastering forum, podcast link.

import requests
from bs4 import BeautifulSoup
import pandas as pd

# URL of the website to scrape
URL = "https://cambridge-mt.com/ms/mtk/"

try:
    # Send a GET request to the webpage
    response = requests.get(URL)
    response.raise_for_status()  # Raise an error for bad status codes
    soup = BeautifulSoup(response.content, "html.parser")

    # Initialize a list to store the scraped data
    data = []

    # Find all artist containers
    artists = soup.find_all("div", class_="c-mtk__artist")

    for artist in artists:
        # Extract genre and artist name
        genre = artist.find_previous("h3").text.strip() if artist.find_previous("h3") else "Unknown Genre"
        artist_name = artist.find("h4", class_="m-container__title-bar-item").text.strip() if artist.find("h4", class_="m-container__title-bar-item") else "Unknown Artist"
        genre_span = artist.find("span", class_="m-container__title-bar-item")
        specific_genre = genre_span.text.strip() if genre_span else "Unknown Genre"
        # print(f"Processing {artist_name} from {genre} ({specific_genre})")
        # Extract tracks
        tracks = artist.find_all("li", class_="m-mtk-track")

        for track in tracks:
            track_name = track.find("span", class_="m-mtk-track__name").text.strip() if track.find("span", class_="m-mtk-track__name") else "Unknown Track"

            # Initialize variables for preview links and metadata
            full_mix_preview = None
            excerpt_mix_preview = None
            unmastered_wav = None
            full_multitrack_link = None
            excerpt_multitrack_link = None
            num_tracks_excerpt = None
            num_tracks_full = None
            forum_link = None
            podcast_link = None

            # Find download links and previews

            downloads = track.find_all("li", class_="m-mtk-download")

            for i,download in enumerate(downloads):
                # print(f"Processing download link {i}", download)
                try:
                    content_type = download.find("div", class_="m-mtk-download__type").text.strip()
                    # print("content_type", content_type)
                    if "Full" in content_type:
                        full_multitrack_link = download.find("a").get("href")
                        num_tracks_full = download.find("span", class_="m-mtk-download__count").text.strip().replace(" Tracks:","")
                    elif "Edited" in content_type:
                        excerpt_multitrack_link = download.find("a").get("href")
                        num_tracks_excerpt = download.find("span", class_="m-mtk-download__count").text.strip().replace(" Tracks:","")
                
                except:
                    try:
                        preview_section = download.find("div", class_="m-mtk-download__content")
                        # print("Preview Section Found", preview_section)
                        for preview in preview_section:
                            if "Excerpt" in preview.text.strip():
                                excerpt_preview = preview.find("a", string = "MP3")
                                if excerpt_preview:
                                    excerpt_mix_preview = excerpt_preview['href']
                            elif "Full" in preview.text.strip():
                                full_preview = preview.find("a", string = "MP3")
                                if full_preview:
                                    full_mix_preview = full_preview['href']
                            elif "Unmastered" in preview.text.strip():
                                unmastered_mix = preview.find("a", string = "WAV")
                                if unmastered_mix:
                                    unmastered_wav = unmastered_mix['href']
                    except:
                        print("Error in processing song previews link")
                        continue


                # Extract forum link
                forum = track.find("p", class_="m-mtk-track__forum-link")
                if forum:
                    forum_link = forum.find("a")
                    if forum_link:
                        forum_link = forum_link.get("href")

                # Extract podcast link if available
                podcast_section = artist.find("p", class_="m-container__header")
                if podcast_section:
                    podcast_link_tag = podcast_section.find("a", string=lambda text: text and "Podcast" in text)
                    if podcast_link_tag:
                        podcast_link = podcast_link_tag.get("href")

            # Append data for the track
            data.append({
                "Genre": genre,
                "Specific Genre": specific_genre,
                "Artist": artist_name,
                "Track Name": track_name,
                "Full Multitrack Link": full_multitrack_link,
                "Excerpt Multitrack Link": excerpt_multitrack_link,
                "Number of Tracks (Excerpt)": num_tracks_excerpt,
                "Number of Tracks (Full)": num_tracks_full,
                "Full Mix Preview": full_mix_preview,
                "Excerpt Mix Preview": excerpt_mix_preview,
                "Unmastered WAV": unmastered_wav,
                "Forum Link": forum_link,
                "Podcast Link": podcast_link
            })
         

    # Convert the data into a DataFrame and save to CSV
    df = pd.DataFrame(data)
    df.to_csv("data/multitrack_website/metadata_with_fine_genre.csv", index=False)

    print("Data scraped and saved to metadata.csv")

except requests.exceptions.RequestException as e:
    print(f"Error occurred during the HTTP request: {e}")
except Exception as e:
    print(f"An error occurred: {e}")
