import os
import requests
import urllib.request as urllib2
import pickle
import time
import zipfile

from os.path import join, dirname, abspath, exists
from collections import defaultdict

from bs4 import BeautifulSoup as bs
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

from tqdm import tqdm


dirname = dirname(abspath(__file__))
LYRICS_DIR = join(dirname, '..', 'lyrics')
BASE_URL = "https://genius.com/"


def init_webdriver():
    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--incognito')
    options.add_argument('--headless')
    driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=options)
    
    return driver


def download_lyrics(urls, names):
    '''
    Web scraper for downloading lyrics from genius.com, given artist names and their respective URLs and stores them in pickle files
    Artist name and URLs must be in the same order
    returns 
    '''
    driver = init_webdriver()
    
    artists_dict = {}
    failed = defaultdict(lambda: [])
    for i, url in tqdm(enumerate(urls)):
        lyrics = {}
        driver.get(url)
        div_btn = driver.find_element_by_xpath("//*[text()[contains(.,'Show all albums by')]]")
        driver.execute_script("arguments[0].click();", div_btn)
        time.sleep(1)

        page_source = driver.page_source
        soup = bs(page_source, 'lxml')

        scrollable = soup.find("scrollable-data")
        albums = soup.find_all('mini-album-card')
        for a in albums:
            links = a.find('a')
            href = links['href']
            title = links['title']

            page = requests.get(href).text
            soup = bs(page, 'lxml')
            tracks = soup.find_all("a", class_="u-display_block")
            album = {}
            album[href] = []
            for track in tqdm(tracks):
                track_href = track['href']
                title = track.find('h3').text.split('\n')[1].strip()
                
                # Handle network traffic inconsistencies within the page (e.g. if page loads too slow)
                reload = True
                count = 0
                while reload:
                    if count == 20:
                        break 
                    page = requests.get(track_href).text
                    soup = bs(page, 'lxml')
                    lyric_div = soup.find_all("div", class_="lyrics")
                    reload = len(lyric_div) < 1
                    count += 1

                if count == 20:
                    album[href].append(track_href)
                    failed[names[i]].append(album)
                    continue

                text = lyric_div[0].text.split('\n')
                lyrics[title] = text
        artists_dict[names[i]] = lyrics
        
        if not exists(LYRICS_DIR):
            os.makedirs(LYRICS_DIR)
        
    for n in names:
        with open(join(LYRICS_DIR, n + ".pkl"), "wb") as file:
            pickle.dump(artists_dict[n], file)
            file.close()

    return artists_dict, failed
    
    
if __name__ == '__main__':
    urls = [
        "https://genius.com/artists/Eminem",
        "https://genius.com/artists/J-cole",
        "https://genius.com/artists/Kanye-west",
        "https://genius.com/artists/2pac",
        "https://genius.com/artists/The-notorious-big",
        "https://genius.com/artists/Logic",
        "https://genius.com/artists/Nas",
        "https://genius.com/artists/Joyner-lucas",
        "https://genius.com/artists/Juice-wrld",
        "https://genius.com/artists/Lil-pump",
        "https://genius.com/artists/Nicki-minaj",
        "https://genius.com/artists/Cardi-b",
        "https://genius.com/artists/Mac-miller"
    ]

    rappers = ["Eminem", "J. Cole", "Kanye West", "2Pac", 
               "Notorious B.I.G.", "Logic", "Nas", "Joyner Lucas", 
               "Juice WRLD", "Lil Pump", 
               "Nicki Minaj", "Cardi B", "Mac Miller"]
    
    download_lyrics(urls, rappers)