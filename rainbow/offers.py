from bs4 import BeautifulSoup
import re
import os
import urllib.request
from urllib.parse import quote
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

import json

options = Options()
# options.add_argument('--headless')
options.add_argument("start-maximized")
options.add_argument('--disable-gpu')


class Offers:
    def __init__(self):
        self.scrapped_data = []
        self.links = []
        # self.links = ['https://r.pl/turcja-riwiera-wczasy/dizalya-palm-garden', 'https://r.pl/turcja-riwiera-wczasy/melissa', 'https://r.pl/turcja-riwiera-wczasy/bonapart-sealine-hotel', 'https://r.pl/turcja-riwiera-wczasy/kleopatra-micador', 'https://r.pl/turcja-riwiera-wczasy/bonn-beach-hotel', 'https://r.pl/turcja-riwiera-wczasy/olimpos-beach-hotel', 'https://r.pl/turcja-riwiera-wczasy/anitas-beach', 'https://r.pl/turcja-egejska-wczasy/kriss-hotel', 'https://r.pl/turcja-riwiera-wczasy/club-dizalya', 'https://r.pl/turcja-riwiera-wczasy/grand-uysal-beach-spa', 'https://r.pl/turcja-riwiera-wczasy/kolibri-hotel', 'https://r.pl/turcja-riwiera-wczasy/sultan-of-dreams', 'https://r.pl/turcja-riwiera-wczasy/oba-star', 'https://r.pl/turcja-riwiera-wczasy/annabella-park-hotel', 'https://r.pl/turcja-riwiera-wczasy/gardenia-hotel', 'https://r.pl/turcja-riwiera-wczasy/grand-kolibri-prestige-and-spa', 'https://r.pl/turcja-riwiera-wczasy/club-turtas-beach', 'https://r.pl/turcja-egejska-wczasy/arora-hotel',  'https://r.pl/turcja-riwiera-wczasy/side-lowe-hotel', 'https://r.pl/turcja-riwiera-wczasy/lonicera-city-kleopatra', 'https://r.pl/turcja-riwiera-wczasy/sultan-of-side', 'https://r.pl/turcja-riwiera-wczasy/side-bay', 'https://r.pl/turcja-riwiera-wczasy/ambassador-plaza-hotel', 'https://r.pl/turcja-riwiera-wczasy/gardenia-beach-hotel', 'https://r.pl/turcja-riwiera-wczasy/ring-beach-hotel', 'https://r.pl/turcja-riwiera-wczasy/sultan-sipahi-resort', 'https://r.pl/turcja-riwiera-wczasy/aydinbey-gold-dreams', 'https://r.pl/turcja-riwiera-wczasy/andriake-beach-club-hotel', 'https://r.pl/turcja-riwiera-wczasy/ramira-city-hotel', 'https://r.pl/turcja-egejska-wczasy/mandarin-resort', 'https://r.pl/turcja-riwiera-wczasy/lonicera-world', 'https://r.pl/turcja-egejska-wczasy/sami-beach', 'https://r.pl/turcja-riwiera-wczasy/xperia-grand-bali-hotel', 'https://r.pl/turcja-egejska-wczasy/club-shark-hotel', 'https://r.pl/turcja-egejska-wczasy/summer-garden-suites-and-beach-hotel']
        self.titles = None
        self.countries = None
        self.cities = None
        self.stars = None
        self.num_offers = None
        self.images = None

    def scrap_main_offer_page(self, page_source, name):
        with open(f'html/rainbow_html_{name}.html', 'w', encoding='utf-8') as f:
            f.write(page_source)

        regex = r'•\s*(\w+)\s*:\s*(.+)'
        soup = BeautifulSoup(page_source, 'html.parser')
        self.num_offers = len(soup.find_all('div', class_='r-card__body r-bloczek__body'))
        self.titles = list(map(lambda span: span.text, soup.find_all('span', class_='r-bloczek-naglowek__tytul')))
        self.links = list(
            map(lambda a: a["href"].split('&')[0], soup.find_all('a', class_='n-bloczek szukaj-bloczki__element')))
        locations = list(map(lambda span: span.text, soup.find_all('span',
                                                                   class_='r-typography r-typography--secondary r-typography--normal r-typography--black r-typography__caption r-typography--one-line-ellipsis r-bloczek-lokalizacja')))
        self.countries = [re.search(regex, loc).group(1) if re.search(regex, loc) else None for loc in locations]
        self.cities = [re.search(regex, loc).group(2) if re.search(regex, loc) else None for loc in locations]
        self.stars = list(
            map(lambda div: div['data-rating'], soup.find_all('div', class_='r-gwiazdki r-gwiazdki--medium')))
        self.images = [img['src'] for img in soup.find_all('img', {'alt': 'zdjęcie oferty'})]

        print("Num of offers:", self.num_offers)

    def init_scrap_data(self):
        for lst in [self.links, self.titles, self.cities, self.stars, self.countries]:
            while len(lst) < self.num_offers:
                lst.append(None)

        for i in range(self.num_offers):
            main_page_info = {
                'operator': "Rainbow",
                'hotel': self.titles[i],
                'link': self.links[i],
                'country': self.countries[i],
                'city': self.cities[i],
                'score': self.stars[i],
                'image': self.images[i]
            }
            self.scrapped_data.append(main_page_info)

    def scrap_single_offers_subpages(self):

        for i in range(self.num_offers):
            if i % 20 == 0:
                print("----- ", "Subpage ", i, " of ", self.num_offers, " -----")
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

            driver.get(self.links[i])
            driver.implicitly_wait(2)

            button = driver.find_element(By.XPATH, "//a[@class='cmpboxbtn cmpboxbtnyes cmptxt_btn_yes']")
            button.click()

            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')

            sub_pages_info = {
                'room_types': [div.text for div in soup.find_all("div", class_="pokoj__title")],
                # 'images': [img["src"] for img in soup.find_all("img", class_="slide-image")]
            }

            try:
                informacje_ogolne_tab = soup.find("div", class_="informacje-ogolne tab")
                sub_page_description = {'description': informacje_ogolne_tab.find("p",
                                                                                  class_="paragraph").text}
            except AttributeError as e:
                # print("Description not found")
                element = driver.find_element(By.XPATH, "//a[@role='tab']/h2[text()='Hotel']")
                element.click()

                page_source = driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
                try:
                    paragraph = soup.find('div', {'class': 'paragraph'}).p
                    if paragraph is not None:
                        text = paragraph.get_text(strip=True)
                    else:
                        text = "Not found"
                except AttributeError as e:
                    text = "Not found"

                sub_page_description = {'description': text}

            # Update dicts
            self.scrapped_data[i].update(sub_pages_info)
            self.scrapped_data[i].update(sub_page_description)
            driver.quit()

    def save_scrap_data_json(self, name):
        with open(f'json/rainbow_scrapped_data_{name}.json', 'w') as f:
            json.dump(self.scrapped_data, f)

    def repair_data(self, name):
        file = open(f'json/rainbow_scrapped_data_{name}.json')
        offers = json.load(file)

        offers = [d for d in offers if 'image' in d and 'gif' not in d['image']]
        offers = [d for d in offers if 'description' in d and 'Not found' not in d['image']]

        for offer in offers:
            offer['image_path'] = offer.pop('image')

            offer.update({
                'room': {
                    'is_standard': True,
                    'is_family': any(
                        map(lambda x: "family" in x.lower() or "junior" in x.lower() or "rodzinny" in x.lower(),
                            offer['room_types'])),
                    'is_apartment': any(
                        map(lambda
                                x: "deluxe" in x.lower() or "premium" in x.lower() or "apartment" in x.lower() or "apartament" in x.lower(),
                            offer['room_types'])),
                    'is_studio': any(
                        map(lambda x: "superior" in x.lower() or "economy" in x.lower() or "studio" in x.lower(),
                            offer['room_types']))
                }
            })

            offer.pop('link')
            offer.pop('room_types')

        self.scrapped_data = offers.copy()

        with open(f'json_corrected/rainbow_scrapped_data_{name}.json', 'w') as f:
            json.dump(offers, f)

    @staticmethod
    def modify_img_name(name, index):
        name = re.sub(r'\s+', '_', name.strip())
        # remove all other characters except alphanumeric and underscores
        name = re.sub(r'[^\w_]', '', name.lower())
        # append .jpg extension
        return index + "_" + name + '.jpg'

    def save_images(self, name):
        os.makedirs(f'images/rainbow_scrapped_data_{name}', exist_ok=True)

        for i, offer in enumerate(self.scrapped_data):
            # full_path = os.path.join("images", FINAL_OFFER_NAME, modify_img_name(offer['hotel']))
            full_path = os.path.join("images", f"rainbow_scrapped_data_{name}",
                                     self.modify_img_name(offer['hotel'], str(i)))
            try:
                image_url = "http:" + quote(offer['image_path'], safe='/:')
                response = urllib.request.urlopen(image_url)
                image_data = response.read()
                with open(full_path, 'wb') as f:
                    f.write(image_data)
            except Exception as e:
                print("Error downloading image:", e)
                print(offer['image_path'])
            # check if the download was successful
            response = urllib.request.urlopen(image_url)

            if response.getcode() == 200:
                pass
            else:
                print(f"{offer['hotel']} Image download failed.")

            offer.update({'image_path': full_path})

        with open(f'json_corrected/rainbow_scrapped_data_{name}.json', 'w') as f:
            json.dump(self.scrapped_data, f)
