import asyncio
from typing import List
from bs4 import BeautifulSoup
from pathlib import Path
import csv
import re
import requests


class EbayDataExtractor:

    def __init__(self):
        pass

    async def init(self):
        # response = requests.get(
        #     "https://www.ebay.com/sch/i.html?_nkw=iphone&_sacat=0&_from=R40&_trksid=p4432023.m570.l1313"
        # )

        # if response.status_code != 200:
        #     print("I cannot make the scraper")
        #     return

        def load_file(filename: str):
            with open(filename, "r") as file:
                return file.read()

        path = Path("output/ebay_extracted_data.csv")
        path.parent.mkdir(parents=True, exist_ok=True)

        html = await asyncio.to_thread(load_file, "iphone_sale _ eBay.html")
        soup = BeautifulSoup(html, "html.parser")
        products = soup.select("ul.srp-results > li")

        # Extract the data
        with open(path.resolve(), "a", newline="", encoding="utf-8") as file:
            buffer: List[dict] = []
            writer = csv.DictWriter(file, fieldnames=["name", "price"])

            # Create the columns if not exist
            if path.stat().st_size <= 0:
                writer.writeheader()

            for i, product in enumerate(products):
                name = product.find("div", "s-item__title")
                price = product.select_one(".s-item__price")

                if not name or not price:
                    continue
                
                name = re.sub(r'\s+', ' ', name.text)
                buffer.append({"name": name.strip(), "price": price.text})

                # Generate the output
                if len(buffer) >= 30:
                    writer.writerows(buffer)
                    file.flush()
                    buffer.clear()

        # print(f"{i} - {name.text[0:10]} - {price.text}")
