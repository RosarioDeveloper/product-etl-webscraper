import os
from bs4 import BeautifulSoup
from pathlib import Path
import csv
from typing import AsyncGenerator
from psycopg import AsyncConnection

from src.web_scraper import WebScraper


class EbayDataExtractor:

    def __init__(self):
        self.cache = dict()
        self.soup = BeautifulSoup()
        self.output_path = Path() / "output"

        # Create the initial folders
        (Path() / "downloads").mkdir(exist_ok=True)
        self.output_path.mkdir(exist_ok=True)

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

        async with WebScraper() as scraper:
            output_file = self.output_path / "extrated_data.txt"

            with open(output_file, "w+") as file:
                print("Extrating Data")
                for i in range(1, 3):
                    result = await scraper.fetch_page(
                        f"https://www.ebay.com/sch/i.html?_nkw=iphone&_sacat=0&_from=R40&_pgn={i}"
                    )

                    if "error" in result:
                        continue

                    html = result.get("html")
                    async for product in extract_product(str(html)):
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

    async def load_stage(self, stream: AsyncGenerator[Path]) -> None:
        DB_HOST = os.getenv("DB_HOST")
        DB_NAME = os.getenv("DB_NAME")
        DB_USER = os.getenv("DB_USER")
        DB_PASS = os.getenv("DB_PASSWORD")
        DB_PORT = os.getenv("DB_PORT")

        async with await AsyncConnection.connect(
            f"dbname={DB_NAME} user={DB_USER} password={DB_PASS} host={DB_HOST} port={DB_PORT}"
        ) as conn:
            async with conn.cursor() as query:
                try:

                    # Drop table if exist
                    await query.execute(
                        """ create table if not exists products (
                        id    serial primary key,
                        name  varchar(255),
                        price float
                        ) """
                    )

                    dir = await stream.asend(None)
                    print("Loading Data\n")

                    # Load data to database
                    with open(dir, "r", newline="") as file:
                        reader = csv.DictReader(file)

                        async with query.copy(
                            "COPY products (name, price) FROM STDIN"
                        ) as copy:
                            for row in reader:
                                await copy.write_row([row["name"], row["price"]])

                    print("✅ Data extraction successufully ")
                    print("✅ See results on output folder")
                except Exception as e:
                    print("❌ Could not possible extracting data. Try again late")
