import time
import requests
import json
import random

from bs4 import BeautifulSoup
from typing import List, Tuple

from selenium.webdriver.common.action_chains import ActionChains
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

WEBSITE_URL: str = "https://www.itaka.pl/all-inclusive/"
NO_OF_SCRAPED_OFFERS: int = 500


class ItakaScraper:
    def __init__(self, website_url: str, no_of_scraped_offers: int) -> None:
        self.website_url: str = website_url
        self.no_of_scraped_offers: int = no_of_scraped_offers
        self.offer_urls: List[str] = self.get_itaka_urls()
        self.scraped_data: List[dict] = self.generate_data()

    def _initialize_driver(self) -> webdriver.Chrome:
        driver = webdriver.Chrome()
        driver.get(self.website_url)
        return driver

    def _accept_cookies(self, driver: webdriver.Chrome) -> None:
        time.sleep(5)
        accept_agreement_element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(
                (By.XPATH, "/html/body/div[5]/div[2]/div[2]/div/div[3]/button[2]")
            )
        )
        accept_agreement_element.click()
        time.sleep(5)
        accept_cookies_element = driver.find_element(
            By.XPATH, '//*[@id="cookie-info-container"]/div/p/button'
        )
        accept_cookies_element.click()
        time.sleep(5)

    def _website_scroll(self, driver: webdriver.Chrome) -> None:
        generate_more_content_iterations = self.no_of_scraped_offers // 25
        for _ in range(generate_more_content_iterations - 1):
            generate_more_offers_button = driver.find_element(
                By.XPATH,
                '//*[@id="search-results-container"]/div/div/section/div/div[1]/div[2]/div[1]',
            )
            actions = ActionChains(driver)
            actions.move_to_element(generate_more_offers_button).perform()
            time.sleep(3)
            generate_more_offers_button.click()
            time.sleep(3)

    def _generate_url_list(self, driver: webdriver.Chrome) -> List[str]:
        html_page_source = driver.page_source
        html_content = BeautifulSoup(html_page_source, "html.parser")
        offer_titles = html_content.find_all("h3", {"class": "header_title"})
        offer_urls = [
            f"https://www.itaka.pl{title.find('a')['href']}" for title in offer_titles
        ]

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

    def _get_hotel_name(self, html_content: BeautifulSoup) -> str:
        return html_content.find("span", {"class": "productName-holder"}).text.strip()

    def _get_country_name(self, html_content: BeautifulSoup) -> str:
        return (
            html_content.find("span", {"class": "destination-title"})
            .text.strip()
            .split("/", 1)[0][:-1]
        )

    def _get_city_name(self, html_content: BeautifulSoup) -> str:
        return (
            html_content.find("span", {"class": "destination-country-region"})
            .text.strip()
            .split("/", 1)[-1][1:]
        )

    def _get_description(self, html_content: BeautifulSoup) -> str:
        return (
            html_content.find("div", {"id": "product-tab-productdescription"})
            .text.strip()
            .split("POŁOŻENIE:")[0]
            .strip()
        )

    def _get_score(self, html_content: BeautifulSoup) -> int:
        try:
            rating = float(
                html_content.find("div", {"class": "event-opinion-flag"})
                .text.strip()
                .split("/", 1)[0]
            )
            final_rating = round(rating * (rating / 6))
        except AttributeError:
            print("AttributeError - generate random rating")
            final_rating = random.randint(3, 5)
        return final_rating

    def _get_img(self, html_content: BeautifulSoup) -> str:
        gallery_content = str(html_content.find("div", {"id": "gallery"}))

        string_starting_point = gallery_content.find("<meta content=")
        string_end_point = gallery_content.find(
            "'", string_starting_point + len("<meta content='")
        )

        link_start_position = string_starting_point + len("<meta content='")
        link_end_position = string_end_point
        return gallery_content[link_start_position:link_end_position].split('"', 1)[0]

    def _room_picker(self, html_content: BeautifulSoup) -> Tuple[bool, ...]:
        input_string = (
            html_content.find("div", {"id": "product-tab-productdescription"})
            .text.strip()
            .split("SPORT I ROZRYWKA:")[0]
            .strip()
            .split("POKÓJ:")[-1]
            .strip()
        )

        room_options = {
            "standardowy": False,
            "rodzinny": False,
            "apartament": False,
            "suite": False,
        }
        room_options = {option: option in input_string for option in room_options}
        return tuple(room_options.values())

    def generate_data(self) -> List[dict]:
        iterations = 0
        scraped_data = []
        for offer_url in self.offer_urls:
            html_page_source = requests.get(offer_url)
            html_content = BeautifulSoup(html_page_source.content, "html.parser")

            hotel_name = self._get_hotel_name(html_content)
            country_name = self._get_country_name(html_content)
            city_name = self._get_city_name(html_content)
            description = self._get_description(html_content)
            score = self._get_score(html_content)
            link = self._get_img(html_content)
            (is_standard, is_family, is_apartament, is_studio) = self._room_picker(
                html_content
            )

            json_entry = {
                "operator": "Itaka",
                "hotel": hotel_name,
                "country": country_name,
                "city": city_name,
                "description": description,
                "score": score,
                "img": link,
                "room": {
                    "is_standard": is_standard,
                    "is_family": is_family,
                    "is_apartment": is_apartament,
                    "is_studio": is_studio,
                },
            }

            scraped_data.append(json_entry)
            print(f"--------- TRIP #{iterations + 1}---------")
            iterations += 1

        return scraped_data

    def save_json_as_file(self, filename: str) -> None:
        with open(f"{filename}.json", "w") as outfile:
            json.dump(self.scraped_data, outfile)


def main(*comand_line_args: str) -> None:
    scrapper = ItakaScraper(WEBSITE_URL, NO_OF_SCRAPED_OFFERS)
    scrapper.save_json_as_file("itaka_offers")
       
if __name__ == "__main__":
    main()