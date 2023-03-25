import asyncio
from pyppeteer.element_handle import ElementHandle
from pyppeteer.page import Page
from pyppeteer.browser import Browser
from tqdm import tqdm

from common import accept_cookies

async def _get_all_offers_elements(page: Page):
    results = await page.querySelectorAll(".results-container")
    assert len(results) == 1
    return await results[0].querySelectorAll(".offer-tile-wrapper")

async def _get_offer_link(offer: ElementHandle) -> str:
    offer_a = await offer.querySelector("a")
    assert offer_a is not None, "Oferta nie ma linku"
    href = await offer_a.getProperty("href")

    return str(await href.jsonValue())

async def get_all_offers(browser: Browser,
                         url: str,
                         iterations: int = 1):
    page = await browser.newPage()
    await page.goto(url)
    await accept_cookies(page)
    await asyncio.sleep(10)

    offers_links = []
    loop = tqdm(range(iterations))

    for _ in loop:
        offers = await _get_all_offers_elements(page)
        assert len(offers) > 0
        offers_links += [await _get_offer_link(offer) for offer in offers]
        await page.evaluate("""window.scrollTo({
          top: document.body.clientHeight - 2500,
          left: 100,
          behavior: "smooth",
        })""") 
        await asyncio.sleep(1)
        more_button = None
        for b in [b for b in await page.querySelectorAll(".button__content")
                  if await (await b.getProperty("textContent")).jsonValue() == "Pokaż więcej"]:
            more_button = b
        if more_button is None:
            break

        await more_button.click()
        await asyncio.sleep(3)
        loop.set_description(f"Found {len(set(offers_links))} distinct offers")

    await page.close()
    return set(offers_links)