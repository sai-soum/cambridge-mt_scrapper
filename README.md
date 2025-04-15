<!-- Scraper for Downloading Mixes from Cambridge Multitrack forums
\\
Cambridge Multitrack Forums: https://discussion.cambridge-mt.com/forumdisplay.php?fid=184 

## Installation
Create a conda environment with the following command:
```
conda create --name cambridge_scraper python=3.7
```
Activate the environment:
```
conda activate cambridge_scraper
```
Install the required packages:
```
pip install -r requirements.txt
```

## Usage
To download the links to song forums and the links to posts in the song forums, run 
```
scripts/scraper.ipynb
```
To download audio files afterwards
```
scripts/download_audio.ipynb
``` -->

# Cambridge Music Technology 'Mixing Secrets' Free Multitrack Dataset Scrapper
This repository provides a comprehensive solution for downloading metadata and audio files from the [Cambridge Multitrack Mixing Secrets](https://www.cambridge-mt.com/) website.  

Curated and hosted by Mike Senior, the site offers an invaluable resource for audio enthusiasts, featuring multitracks and corresponding mixes generously contributed by artists and producers. For more details, visit the website and explore its extensive collection.

This repository is structured the following way:
- ```Cambridge-mt_scrapper```
    - ```cmt-mtk```: contains all the scripts for downloading metadata and audio files. This is split into seperate folders to download requirements from the website and the forum
        - ```forum_scrapper``` : Contains scripts for scrapping metadata from the forums. The approach follows genre-wise scrapping and the data is stored in./data/forum/ . Further, you can use provided scripts for downloading all the different mixes created by participants in the forum.
        - ```multitrack_scrapper```: This folder contains scripts pertaining to the main website. The scripts allow to scrape metadata and download audio files and multitrack.
        - ```data_analysis```: This folder contains Jupyter notebooks with some basic data analysis about the data available in the forum and the website.
        - ```post_processing```: This folder contains scripts for alligning mixes to multitracks, naming the multitrack instrument groups, extracting audio features.
    - ```data```: Contains scrapped textual and metadata from the websites. Many of these are used for downloading audio and multitracks as well. 

To start, create a virtual environment using either ```conda``` or ```pip```.

```
cd cambridge-mt_scrapper
python3 -m venv env
source env/bin/activate
pip install -r requirments.txt
```
## 'Mixing Secrets' Free Multitrack Download Library
### Metadata Scrapping
To collect metadata from the multitrack website about song names, artists name, genre, links to full and excerpt previews and corresponding multitrack, and more, run 
``` python cmt-mtk/multitrack_scrapper/scrape_metadata.py```
- Currently ```data/multitrack_website``` contains all the downloaded metadata for forum.
### Audio Download
Next, download audio using
``` python cmt-mtk/multitrack_scrapper/download_dataset.py ```

## 'Mixing Secrets' Free Multitrack Download Library: Mixing Forum
### Forum Metadata Scrapping
We first generate a .json file with song_names and links to the forum. This is done genre-by-genre. You will need to provide URL for a specific genre mixing forum. Find the link [here](https://discussion.cambridge-mt.com/forumdisplay.php?fid=184).
Run:
``` python cmt-mtk/forum_scrapper/scrape_metadata.py ```
- Currently ```data/forum/metadata``` contains all the downloaded metadata for forum.
### Audio Download 
Once you have scrapped the metadata, we will use the .json file to find links to download. 
Run:
``` python cmt-mtk/forum_scrapper/dwnld_forum_mixes.py ```

You can find all the scrapped metadata saved in the ```data/```.

*Some of the code was corrected and optimised with the help of ChatGPT
*A part of the multitrack audio downloader was inspired by https://github.com/mimbres/Cambridge-MT-Downloader 

This repository was updated by Soumya during her internship at SonyAI, Tokyo in Jan 2025 from Sony email-based Github account. 


