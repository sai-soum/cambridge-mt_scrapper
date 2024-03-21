Scraper for Downloading Mixes from Cambridge Multitrack forums
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
```


