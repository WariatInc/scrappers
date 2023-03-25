import asyncio
import dataclasses
import json
from copy import deepcopy
from typing import Optional

from pyppeteer import launch
from pyppeteer.browser import Browser
from pyppeteer.page import Page
import tqdm.asyncio

import offers_list as offers
import offer

CHROMIUM = "/usr/bin/chromium-browser"  # This is a device specific path

ITERATIONS = 50
QUERIES = [
    (
        "https://www.tui.pl/all-inclusive?pm_source=MENU&pm_name=All_Inclusive&q=%3Aprice%3AbyPlane%3AT%3AdF%3A6%3AdT%3A14%3ActAdult%3A2%3ActChild%3A0%3Aroom%3A2%3Aboard%3AGT06-AI%3AminHotelCategory%3AdefaultHotelCategory%3AtripAdvisorRating%3AdefaultTripAdvisorRating%3Abeach_distance%3AdefaultBeachDistance%3AtripType%3AWS&fullPrice=false",
        offer.Data(
            room=offer.Data.Room(
                size="small"
            ),
            transport=offer.Data.Transport(
                organised=True,
                type="plane"
            )
        )
    ),
    (
        "https://www.tui.pl/all-inclusive?pm_source=MENU&pm_name=All_Inclusive&q=%3Aprice%3AbyPlane%3AT%3AdF%3A6%3AdT%3A14%3ActAdult%3A5%3ActChild%3A0%3Aroom%3A5%3Aboard%3AGT06-AI%3AminHotelCategory%3AdefaultHotelCategory%3AtripAdvisorRating%3AdefaultTripAdvisorRating%3Abeach_distance%3AdefaultBeachDistance%3AtripType%3AWS&fullPrice=false",
        offer.Data(
            room=offer.Data.Room(
                size="medium"
            ),
            transport=offer.Data.Transport(
                organised=True,
                type="plane"
            )
        )
    ),
    (
        "https://www.tui.pl/all-inclusive?pm_source=MENU&pm_name=All_Inclusive&q=%3Aprice%3AbyPlane%3AT%3AdF%3A6%3AdT%3A14%3ActAdult%3A7%3ActChild%3A0%3Aroom%3A7%3Aboard%3AGT06-AI%3AminHotelCategory%3AdefaultHotelCategory%3AtripAdvisorRating%3AdefaultTripAdvisorRating%3Abeach_distance%3AdefaultBeachDistance%3AtripType%3AWS&fullPrice=false",
        offer.Data(
            room=offer.Data.Room(
                size="large"
            ),
            transport=offer.Data.Transport(
                organised=True,
                type="plane"
            )
        )
    ),
    (
        "https://www.tui.pl/wypoczynek/wyniki-wyszukiwania-nocleg?pm_source=MENU&pm_name=Wakacje_samochodem_FM&q=%3Aprice%3AbyPlane%3AF%3AdF%3A6%3AdT%3A8%3ActAdult%3A2%3ActChild%3A0%3AminHotelCategory%3AdefaultHotelCategory%3AtripAdvisorRating%3AdefaultTripAdvisorRating%3Abeach_distance%3AdefaultBeachDistance%3AtripType%3ADW&fullPrice=false",
        offer.Data(
            room=offer.Data.Room(
                size="small"
            ),
            transport=offer.Data.Transport(
                organised=False,
                type=""
            )
        )
    ),
    (
        "https://www.tui.pl/wypoczynek/wyniki-wyszukiwania-nocleg?pm_source=MENU&pm_name=Wakacje_samochodem_FM&q=%3Aprice%3AbyPlane%3AF%3AdF%3A6%3AdT%3A8%3ActAdult%3A4%3ActChild%3A0%3Aroom%3A4%3AminHotelCategory%3AdefaultHotelCategory%3AtripAdvisorRating%3AdefaultTripAdvisorRating%3Abeach_distance%3AdefaultBeachDistance%3AtripType%3ADW&fullPrice=false",
        offer.Data(
            room=offer.Data.Room(
                size="medium"
            ),
            transport=offer.Data.Transport(
                organised=False,
                type=""
            )
        )
    ),
    (
        "https://www.tui.pl/wypoczynek/wyniki-wyszukiwania-nocleg?pm_source=MENU&pm_name=Wakacje_samochodem_FM&q=%3Aprice%3AbyPlane%3AF%3AdF%3A6%3AdT%3A8%3ActAdult%3A7%3ActChild%3A0%3Aroom%3A7%3AminHotelCategory%3AdefaultHotelCategory%3AtripAdvisorRating%3AdefaultTripAdvisorRating%3Abeach_distance%3AdefaultBeachDistance%3AtripType%3ADW&fullPrice=false",
        offer.Data(
            room=offer.Data.Room(
                size="large"
            ),
            transport=offer.Data.Transport(
                organised=False,
                type=""
            )
        )
    ),
]

tabs_sem = asyncio.Semaphore(15)


async def scrape_offer(browser: Browser, data: offer.Data, url: str) -> Optional[offer.Data]:
    async with tabs_sem:
        page = await browser.newPage()
        try:
            s_data = await offer.load_offer(
                page,
                deepcopy(data),
                url
            )
        except Exception:
            s_data = None
        await page.close()
    return s_data


async def main():
    browser = await launch(headless=True,
                           autoclose=False,
                           executablePath=CHROMIUM)

    scraped_offers = []
    for search_url, data in QUERIES:
        all_offers = await offers.get_all_offers(browser, search_url, iterations=ITERATIONS)
        for res in tqdm.asyncio.tqdm_asyncio.as_completed(
                [
                scrape_offer(browser, data, o)
                for o in all_offers
                ],
                desc="Scraping each offer"):
            if (scr := await res) is not None:
                scraped_offers.append(scr)

    with open("tui.json", "w") as f:
        json.dump([
            dataclasses.asdict(o)
            for o in scraped_offers
        ], f)


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
