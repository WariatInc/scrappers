from dataclasses import dataclass, asdict
from typing import Optional, Tuple
import asyncio
import hashlib
import urllib.request
import urllib.parse
from pathlib import Path
import os

from common import accept_cookies, query_accordion

from pyppeteer.page import Page
from pyppeteer.element_handle import ElementHandle

@dataclass
class Data:
    @dataclass
    class Room:
        is_apartament: Optional[bool] = None
        is_studio: Optional[bool] = None
        size: Optional[str] = None
    
    @dataclass
    class Transport:
        organised: Optional[bool] = None
        type: Optional[str] = None

    operator: Optional[str] = None
    hotel: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    description: Optional[str] = None
    score: Optional[int] = None
    kids: Optional[bool] = None
    url: Optional[str] = None
    image: Optional[str] = None
    image_local: Optional[str] = None

    room: Optional[Room] = None
    transport: Optional[Transport] = None


async def _get_rating(page: Page) -> int:
    rating_wrapper = await page.querySelector(".top-section__hotel-rating")
    assert rating_wrapper is not None
    return len(await rating_wrapper.querySelectorAll("li"))


async def _get_hotel_name(page: Page) -> str:
    header = await page.querySelector(".top-section__hotel-name")
    assert header is not None
    return await (await header.getProperty("textContent")).jsonValue()

async def _get_location(page: Page) -> Tuple[str, str]:
    locs = await page.querySelectorAll(".top-section__subheading > nav > .breadcrumbs__list > li > a > span")
    assert locs is not None
    text_contents = await asyncio.gather(
        *(
        prop.jsonValue()
        for prop in await asyncio.gather(
            *(
            loc.getProperty("textContent")
            for loc in locs
            )            
        ))
    )
    
    return (
        " / ".join((str(c) for c in text_contents[1:])),
        str(text_contents[0]),
    )

async def _get_description(page: Page) -> str:
    blocks = await page.querySelectorAll(".text-block > .text-block__content")
    assert blocks is not None
    return str(await (await blocks[0].getProperty("textContent")).jsonValue()).replace(
        "\xa0",
        " "
    )

async def _load_room(page: Page,
                     room: Data.Room):
    choices_objects = await page.querySelectorAll(".room-choice__name")
    assert choices_objects is not None
    choices = await asyncio.gather(*(
        prop.jsonValue()
        for prop in await asyncio.gather(*(
            obj.getProperty("textContent")
            for obj in choices_objects
        ))
    ))

    room.is_apartament = "Apartament" in choices
    room.is_studio = "Studio" in choices

async def _load_image(page: Page):
    image_elements = await page.querySelectorAll(".swiper-slide > div > span > img")
    assert image_elements is not None
    image_element = None
    for el in image_elements:
        image_url = str(await (await el.getProperty("src")).jsonValue())
        if urllib.parse.urlparse(image_url):
            image_element = el

    assert image_element is not None 
    image_url = str(await (await image_element.getProperty("src")).jsonValue())

    m = hashlib.sha256()
    m.update(image_url.encode("ASCII"))

    image_name = f"{m.hexdigest()}.jpg"
    image_path = Path("images/") / Path(image_name)
    urllib.request.urlretrieve(
        image_url,
        image_path.as_posix()
    )
    return image_url, image_name

async def load_offer(page: Page,
                     data: Data,
                     url: str) -> Optional[Data]:
    try:
        await page.goto(url, timeout=3 * 60_000)
    except TimeoutError:
        return None 
    await accept_cookies(page)
    data.operator = "Tui"
    data.score = await _get_rating(page) 
    data.hotel = await _get_hotel_name(page)
    data.city, data.country = await _get_location(page)
    data.url = url
    data.description = await _get_description(page)
    data.kids = len(await query_accordion(page, "Dla dzieci")) >= 1
    if data.room is None:
        data.room = Data.Room()
    await _load_room(page, data.room)
    data.image, data.image_local = await _load_image(page)

    return data
