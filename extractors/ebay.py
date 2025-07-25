import asyncio
from dataclasses import dataclass
from types import CoroutineType, NoneType
from typing import Any, Callable, Coroutine, List, Literal, Optional
from bs4 import BeautifulSoup
from pathlib import Path
import csv
import requests
import aiohttp
from typing import AsyncGenerator, get_type_hints


cache = dict()


@dataclass
class StreamResult:
    status: Optional[int] = 200
    output_file: Optional[str] = None


class EbayDataExtractor:

    def __init__(self):
        self.cache = dict()
        self.soup = BeautifulSoup()
        self.output_path = Path() / "output"

        # Create the initial download folder
        # path = Path("downloads")

        # Create the initial folders
        (Path() / "downloads").mkdir(exist_ok=True)
        self.output_path.mkdir(exist_ok=True)

    async def pipeline_stream(self):
        # Run stages in pipelibe mode
        async def pipeline(*funcs: Callable):
            result = None
            for func in funcs:
                is_coroutine = get_type_hints(func).get("return") is NoneType
                result = await func(result) if is_coroutine else func(result)

            return result

        await pipeline(self.extract_stage, self.transform_stage, self.load_stage)

    async def extract_stage(self, stream=None) -> AsyncGenerator[Path | None]:

        def clear_text(text: str):
            import regex

            return regex.sub(r"[$\s]+", " ", text).strip()

        async def extract_product(raw_data: str):
            html = BeautifulSoup(raw_data, "html.parser")
            products = html.select("ul.srp-results > li")

            for item in products:
                name_tag = item.select_one(".s-card__title")
                price_tag = item.select_one(".s-card__price")

                if not name_tag or not price_tag:
                    # print("Product not found")
                    yield None
                    continue

                yield clear_text(f"{name_tag.text}:{price_tag.text}")

        # Get the total pages available to scraper
        page_html = await self.download_html_page(1, from_local=True)
        soup = BeautifulSoup(page_html, "html.parser")

        pagination = soup.select_one(".pagination__items li:last-child")
        if not pagination:
            yield None
            return

        total_pages = int(pagination.text)

        # Start Extraction
        output_file = self.output_path / "extrated_data.txt"
        with open(output_file, "w+") as file:
            print(f"Extracting Data Page ")

            for i in range(1, 3):
                html = (
                    page_html
                    if i == 1
                    else await self.download_html_page(i, from_local=True)
                )

                async for product in extract_product(html):
                    if product:
                        file.write(f"{product}\n")

            yield output_file

    async def transform_stage(self, stream: AsyncGenerator[Path]):
        import regex

        result = await stream.asend(None)
        transformed_data_dir = self.output_path / "tranformed_data.csv"

        with (
            open(str(result), "r") as file,
            open(transformed_data_dir, "w", newline="") as transformed_file,
        ):
            print(f"Tranforming Data Page ")
            output = csv.DictWriter(transformed_file, fieldnames=["name", "price"])

            # Create the csv columns
            output.writeheader()

            for line in file:
                name, price = line.split(":")[:2]
                output.writerow(
                    {"name": name, "price": regex.sub(r"[^\d.]+", "", price)}
                )

        yield transformed_data_dir

    async def load_stage(self, stream: AsyncGenerator[StreamResult]) -> None:
        async for data in stream:
            print(f"Loading Data")

    async def read_file(self, dir: str):
        with open(dir, "r") as reader:
            return reader.read()

    async def write_file(self, dir: str, content: str):
        with open(dir, "a") as writer:
            writer.write(content)
            writer.flush()

    async def download_html_page(
        self,
        page: int,
        url: str = "",
        from_local: bool = False,
    ) -> str:
        # Download html page
        async def download_page(url: str):
            # headers = {
            #     "Cache-Control": "no-cache",
            #     "Pragma": "no-cache",
            #     "Expires": "0",
            #     "User-Agent": "Mozilla/5.0",
            # }

            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    return await response.text()

        # Controll concurrency
        html = ""
        async with asyncio.Semaphore(10):
            try:
                filename = f"downloads/ebay_products_page_{page}.html"
                if from_local:
                    return await self.read_file(filename)

                html = await download_page(
                    f"https://www.ebay.com/sch/i.html?_nkw=iphone&_sacat=0&_from=R40&_pgn={page}"
                )

                await self.write_file(filename, content=html)

            except Exception as e:
                html = ""

            return html

    async def extract_product(self, html: BeautifulSoup):
        products = html.select("ul.srp-results > li")

        name = html.find("div", class_="s-item__title")
        price = html.select_one(".s-item__price")

        # async for i, product in enumerate(products):
        #     pass

        # return {"name": name, "price": price}
