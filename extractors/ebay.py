import asyncio
from types import CoroutineType
from typing import Any, Callable, Coroutine, List
from bs4 import BeautifulSoup
from pathlib import Path
import csv
import re
import requests
import aiohttp
from typing import AsyncGenerator, get_type_hints

cache = dict()


class EbayDataExtractor:

    def __init__(self):
        self.cache = dict()
        self.soup = BeautifulSoup()
        self.path = Path()

        # Create the initial download folder
        # path = Path("downloads")

        (self.path / "downloads").mkdir(exist_ok=True)

    def trim(self, text: str):
        return re.sub(r"\s+", " ", text).strip()

    async def extract_stage(self, stream=None) -> AsyncGenerator[str, None]:
        total_pages = 10

        for i in range(total_pages):
            print(f"Extracting page {i}")
            yield {"current_page": i, "html": "", "status": 200}

    async def transform_stage(self, stream) -> AsyncGenerator:
        async for raw_data in stream:
            print(f"Transforming page {raw_data['current_page']}")
            yield raw_data

    async def load_stage(self, stream) -> CoroutineType:
        async for data in stream:
            print(f"Loading page {data['current_page']}")
            print(data)
            await asyncio.sleep(4)

        return ""

    async def pipeline_stream(self):
        result = None

        # Get the total pages available to download
        # soup = BeautifulSoup(
        #     await self._download_html_page(1, from_local=True), "html.parser"
        # )

        # pagination = soup.select_one(".pagination__items li:last-child")
        # if not pagination:
        #     raise Exception("No Paginatinon")

        # total_pages = int(pagination.text)

        async def pipeline(*funcs: Callable):
            result = None

            for func in funcs:
                is_coroutine = get_type_hints(func).get("return") is CoroutineType
                result = await func(result) if is_coroutine else func(result)

            return result

        # await pipeline(self.extract_stage, self.transform_stage, self.load_stage)
        extract_stream = self.extract_stage()
        trans_stream = self.transform_stage(extract_stream)
        
        await self.load_stage(trans_stream)

        # for page in range(1, 10):
        #     print(f"page: {page}")

        #     # Execute the ETL pipeline
        #     await pipeline(self.extract_stage, self.transform_stage, self.load_stage)

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

    async def _download_html_page(self, page: int, from_local: bool = False) -> str:
        print(f"Downloading html page {page}")

        async def download_page():
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

        def write_file(html: str):
            with open(f"downloads/ebay_products_page_{page}.html", "a") as writer:
                writer.write(html)
                writer.flush()
                return html

        if from_local:
            return await asyncio.to_thread(read_file)

        html = await download_page()
        return await asyncio.to_thread(lambda: write_file(html))
