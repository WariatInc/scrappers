from typing import List
from pyppeteer.page import Page


async def accept_cookies(page: Page):
    button_wrapper = await page.querySelector(".cookies-bar__buttons-wrapper")
    if button_wrapper is None:
        return
    button = await button_wrapper.querySelector("button")
    assert button is not None
    await button.click()


async def query_accordion(page: Page, query: str) -> List[str]:
    with open("query_accordions.js", "r") as f:
        return await page.evaluate(
            f.read(),
            query
        )
