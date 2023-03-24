import time
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException, NoSuchElementException
from offers import Offers


def scroll_all_offers(url):
    options = Options()
    options.add_argument("start-maximized")
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    driver.get(url)
    # Wait for the page to load completely
    wait = WebDriverWait(driver, 5)
    try:
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    except TimeoutException:
        print("Page not load")
    count = 0
    while count != 20:
        if count % 10 == 0:
            print("============ ", "Iteration", count, " ============")

        try:
            button: WebElement = driver.find_element(by=By.CLASS_NAME, value='szukaj-bloczki__load-more-button')
        except NoSuchElementException:
            print("-> Button not found")

        time.sleep(5)
        try:
            # Scroll to button
            driver.execute_script("arguments[0].scrollIntoView(true);", button)
            # Click the button
            driver.execute_script("arguments[0].click();", button)
            # print("-> button clicked")
        except StaleElementReferenceException:
            print("-> button not clicked")
            break

        time.sleep(5)
        count += 1

    return driver.page_source


url = "https://r.pl/turcja?dlugoscPobytu=7-9&dlugoscPobytu.od=&dlugoscPobytu.do=&typyWyjazdu=wypoczynek&cena=avg&cena.od=1&cena.do=3000&ocenaKlientow&odlegloscLotnisko=*-*&dlugoscPobytu.od.force=t&wybraneDokad=turcja&wybraneSkad=gdansk,GDN&typTransportu=dowolny&data&dorosli=1993-01-01&dorosli=1993-01-01&dzieci=nie&liczbaPokoi=1&dowolnaLiczbaPokoi=tak&sortowanie=cena-asc"

urls = {
    'bus': 'https://r.pl/szukaj?typTransportu=BUS&data&dorosli=1993-01-01&dorosli=1993-01-01&dzieci=2015-01-01&liczbaPokoi=1&dowolnaLiczbaPokoi=nie&dlugoscPobytu=*-*&dlugoscPobytu.od=&dlugoscPobytu.do=&cena=avg&cena.od=&cena.do=&ocenaKlientow&odlegloscLotnisko=*-*&sortowanie=cena-asc&dlugoscPobytu.od.force=t',
    'plane': 'https://r.pl/szukaj?typTransportu=AIR&data&dorosli=1993-01-01&dorosli=1993-01-01&dzieci=2015-01-01&liczbaPokoi=1&dowolnaLiczbaPokoi=nie&dlugoscPobytu=*-*&dlugoscPobytu.od=&dlugoscPobytu.do=&cena=avg&cena.od=&cena.do=&ocenaKlientow&odlegloscLotnisko=*-*&sortowanie=cena-asc&dlugoscPobytu.od.force=t',
    'plane2_3': 'https://r.pl/wczasy?typTransportu=AIR&data&dorosli=1993-01-01&dorosli=1993-01-01&dzieci=2015-01-01&liczbaPokoi=1&dowolnaLiczbaPokoi=nie&dlugoscPobytu=*-*&dlugoscPobytu.od=&dlugoscPobytu.do=&cena=avg&cena.od=&cena.do=&ocenaKlientow&odlegloscLotnisko=*-*&sortowanie=cena-asc&dlugoscPobytu.od.force=t&typyWyjazdu=wypoczynek',
    'self': 'https://r.pl/szukaj?typTransportu=SELF&data&dorosli=1993-01-01&dorosli=1993-01-01&dzieci=2015-01-01&liczbaPokoi=1&dowolnaLiczbaPokoi=nie&dlugoscPobytu=*-*&dlugoscPobytu.od=&dlugoscPobytu.do=&cena=avg&cena.od=&cena.do=&ocenaKlientow&odlegloscLotnisko=*-*&sortowanie=cena-asc&dlugoscPobytu.od.force=t'
}
selected_url = 'self'

# html = scroll_all_offers(url=urls[selected_url])
rainbow = Offers()
# rainbow.scrap_main_offer_page(html, name=selected_url)
# rainbow.num_offers = 2
# rainbow.titles = ['ABC', 'ABC']
# rainbow.countries = ['Poland', 'Poland']
# rainbow.cities = ['Gdansk', 'Gdansk']
# rainbow.stars = ['5', '5']
# rainbow.images = ['//image', '//image']
# rainbow.links = ['https://r.pl/bulgaria-sloneczny-brzeg-wczasy/saint-george?data=20230829',
#                  'https://r.pl/bulgaria-sloneczny-brzeg-wczasy/jeravi-beach?data=20230912']

# rainbow.init_scrap_data()
# rainbow.scrap_single_offers_subpages()
# rainbow.save_scrap_data_json(name=selected_url)
rainbow.repair_data(name=selected_url)
rainbow.save_images(name=selected_url)



