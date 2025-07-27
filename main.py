import asyncio
from types import NoneType
from typing import Callable, get_type_hints

from src.ebay_data_extrat import EbayDataExtractor
from src.web_scraper import WebScraper


# Run stages in pipelibe mode
async def pipeline(*funcs: Callable):
    result = None

    for func in funcs:
        is_coroutine = get_type_hints(func).get("return") is NoneType
        result = await func(result) if is_coroutine else func(result)

    return result


async def main():
    ebay_extractor = EbayDataExtractor()

    await pipeline(
        ebay_extractor.extract_stage,
        ebay_extractor.transform_stage,
        ebay_extractor.load_stage,
    )


if __name__ == "__main__":
    asyncio.run(main())
