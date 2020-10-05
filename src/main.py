import requests
from bs4 import BeautifulSoup
import time

url="https://www.dofus.com/fr/mmorpg/encyclopedie/monstres?monster_type[0]=archimonster&size=96&ipage="
n_pages=1
for i in range(1,n_pages+1):
        print('Scraping page',i,'/',n_pages)
        page = requests.get(url + str(i))
        soup = BeautifulSoup(page.content, 'html.parser')
        results = soup.find("table").find("tbody").find_all("tr")
        for elem in results:
            nameFr = elem.find("a").getText()
            img = elem.find("img")
            print(nameFr, img, img["src"])
        print('Scraped ! Waiting 1s ...')
        time.sleep(1)

