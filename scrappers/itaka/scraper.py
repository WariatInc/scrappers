import time
import requests
import json

from bs4 import BeautifulSoup
from typing import List

from selenium.webdriver.common.action_chains import ActionChains
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


WEBSITE_URL: str = "https://www.itaka.pl/all-inclusive/"
NO_OF_SCRAPED_OFFERS: int = 25


class ItakaScraper:
    def __init__(self, website_url: str, no_of_scraped_offers: int) -> None:
        self.website_url: str = website_url
        self.no_of_scraped_offers: int = no_of_scraped_offers
        self.offer_urls: List[str] = self.get_itaka_urls()
        self.scraped_data: List[dict] = self.generate_data()
        self.save_json_as_file(filename="itaka_offers")

    def _initialize_driver(self) -> webdriver.Chrome:
        driver = webdriver.Chrome()
        driver.get(self.website_url)
        return driver

    def _accept_cookies(self, driver: webdriver.Chrome) -> None:
        time.sleep(5)
        accept_agreement_element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "/html/body/div[5]/div[2]/div[2]/div/div[3]/button[2]")))
        accept_agreement_element.click()
        time.sleep(5)
        accept_cookies_element = driver.find_element(By.XPATH, '//*[@id="cookie-info-container"]/div/p/button')
        accept_cookies_element.click()
        time.sleep(5)

    def _website_scroll(self, driver: webdriver.Chrome) -> None:
        generate_more_content_iterations = self.no_of_scraped_offers // 25
        for _ in range(generate_more_content_iterations - 1):
            generate_more_offers_button = driver.find_element(By.XPATH,
                                                              '//*[@id="search-results-container"]/div/div/section/div/div[1]/div[2]/div[1]')
            actions = ActionChains(driver)
            actions.move_to_element(generate_more_offers_button).perform()
            time.sleep(3)
            generate_more_offers_button.click()
            time.sleep(3)

    def _generate_url_list(self, driver: webdriver.Chrome) -> List[str]:
        html_page_source = driver.page_source
        html_content = BeautifulSoup(html_page_source, 'html.parser')
        offer_titles = html_content.find_all('h3', {'class': 'header_title'})
        offer_urls = [f"https://www.itaka.pl{title.find('a')['href']}" for title in offer_titles]
        # print(len(offer_urls))

        return offer_urls

    def _exit_driver(self, driver) -> None:
        time.sleep(3)
        driver.quit()

    def get_itaka_urls(self) -> List[str]:
        selenium_driver = self._initialize_driver()
        self._accept_cookies(selenium_driver)
        self._website_scroll(selenium_driver)
        offer_urls = self._generate_url_list(selenium_driver)
        self._exit_driver(selenium_driver)

        return offer_urls

    def generate_data(self) -> List[dict]:
        iterations = 0
        scraped_data = []
        for offer_url in self.offer_urls:
            html_page_source = requests.get(offer_url)
            html_content = BeautifulSoup(html_page_source.content, 'html.parser')

            product_name = html_content.find('span', {'class': 'productName-holder'}).text.strip()
            country = html_content .find('span', {'class': 'destination-title'}).text.strip().split('/',1)[0][:-1]
            region = html_content .find('span', {'class': 'destination-country-region'}).text.strip().split('/',1)[-1][1:]

            json_entry = {
                "operator": "Itaka",
                "hotel": product_name,
                "country": country,
                "city": region
            }

            scraped_data.append(json_entry)
            print(offer_url)
            print(f"--------- TRIP #{iterations+1}---------")
            iterations += 1

        return scraped_data

    def save_json_as_file(self, filename: str) -> None:
        with open(f"{filename}.json", "w") as outfile:
            json.dump(self.scraped_data, outfile)


scraper = ItakaScraper(WEBSITE_URL, NO_OF_SCRAPED_OFFERS)

