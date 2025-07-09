import asyncio
from typing import List
from bs4 import BeautifulSoup
from pathlib import Path
import csv
import re
import requests
import aiohttp

cache = dict()


class EbayDataExtractor:

    def __init__(self):
        self.cache = dict()
        self.soup = BeautifulSoup()

    async def load_html(self, filename: str):
        def read_file():
            with open(f"downloads/{filename}.html", "r") as file:
                return file.read()

        try:
            return await asyncio.to_thread(read_file)
        except Exception:
            pass

    async def get_html(self, page: int, from_local: bool = False):
        print(f"Downloading html page {page}")

        async def __get_html():
            response = await asyncio.to_thread(
                lambda: requests.get(
                    f"https://www.ebay.com/sch/i.html?_nkw=iphone&_sacat=0&_from=R40&_pgn={page}"
                )
            )

            if not response.ok:
                raise Exception("404", "Page not founded")

            return response.text

        def read_file():
            with open(f"downloads/ebay_products_page_{page}.html", "r") as reader:
                return reader.read()

        def download(html: str):
            with open(f"downloads/ebay_products_page_{page}.html") as writer:
                writer.write(html)
                writer.flush()
                return html

        if from_local:
            return await asyncio.to_thread(read_file)

        html = await self.__get_html()
        return await asyncio.to_thread(lambda: download())

    async def extract(self):
        filename = "ebay_products_page"
        html = await self.get_html(page=1)

        soup = BeautifulSoup(html, "html.parser")
        pagination = soup.select_one(".pagination__items li:last-child")

        if not pagination:
            raise Exception("No Paginatinon")

        total_pages = int(pagination.text)
        if total_pages <= 1:
            return

        # total_pages = 2
        for page in range(1, total_pages):
            page_html = await self.get_html(page + 1)

            if not page_html:
                continue

            print(page + 1)

        total_pages = 0

    # async load

    def trim(self, text: str):
        return re.sub(r"\s+", " ", text).strip()

    async def extract_data(self):
        # response = requests.get(
        #     "https://www.ebay.com/sch/i.html?_nkw=iphone&_sacat=0&_from=R40&_pgn=1"
        # )

        # if response.status_code != 200:
        #     print("I cannot make the scraper")
        #     return

        path = Path("output/ebay_extracted_data.csv")
        path.parent.mkdir(parents=True, exist_ok=True)

        html = await asyncio.to_thread(self.load_file, "iphone_sale _ eBay.html")
        soup = BeautifulSoup(html, "html.parser")
        products = soup.select("ul.srp-results > li")

        # Extract the data
        with open(path.resolve(), "a+", newline="", encoding="utf-8") as file:
            buffer: List[dict] = []
            writer = csv.DictWriter(
                file,
                fieldnames=[
                    "name",
                    "price",
                    "second_price",
                    "old_price",
                    "store",
                    "store_address",
                ],
            )

            # Create the columns if not exist
            if path.stat().st_size <= 0:
                writer.writeheader()

            for i, product in enumerate(products):
                name = product.find("div", "s-item__title")
                price = product.select_one(".s-item__price")

                if not name or not price:
                    continue

                # Check if the product already exist on the output
                name = self.trim(name.text)
                if name in cache:
                    continue

                cache[name] = cache.get(name, 0) + 1
                buffer.append({"name": name, "price": self.trim(price.text)})

                # Generate the output
                if len(buffer) >= 30:
                    writer.writerows(buffer)
                    file.flush()
                    buffer.clear()

        # print(f"{i} - {name.text[0:10]} - {price.text}")
