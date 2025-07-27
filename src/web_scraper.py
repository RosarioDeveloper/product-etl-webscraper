import asyncio
from pathlib import Path
import random
from typing import Dict
import aiohttp


class BrowserHeaders:
    """
    Utility class to provide random browser headers for HTTP requests.
    """

    def __init__(self) -> None:
        """
        Initializes Chrome and Firefox header dictionaries.
        """
        self.chrome_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-EN,en;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
            "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
        }

        self.firefox_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.8,en-US;q=0.5,en;q=0.3",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
        }

    def random_headers(self):
        """
        Returns a random set of browser headers (Chrome or Firefox).
        """
        headers = [self.chrome_headers, self.firefox_headers]
        return random.choice(headers)


class WebScraper:
    """
    Asynchronous web scraper for fetching HTML pages with retry and random headers.
    """

    def __init__(self, delay=(1, 3)):
        """
        Initializes the WebScraper, sets up temp folder, retry count, and delay.
        """
        self.session = None
        self.temp_output = Path() / "temp"
        self.max_retry = 3
        self.delay = delay

        # create temp folder
        self.temp_output.mkdir(exist_ok=True)
        self.browser_headers = BrowserHeaders()

    async def __aenter__(self):
        """
        Asynchronous context manager entry: creates aiohttp session with custom headers.
        """
        connector = aiohttp.TCPConnector(
            limit=5,
            limit_per_host=30,
            ttl_dns_cache=300,
        )

        timeout = aiohttp.ClientTimeout(total=30, connect=10, sock_read=10)

        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=self.browser_headers.random_headers(),
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Asynchronous context manager exit: closes aiohttp session.
        """
        if self.session:
            await self.session.close()

    async def fetch_page(self, url: str, **kwargs):
        """
        Fetches a web page asynchronously with retries and random headers.
        Returns a dict with the HTML content.
        """

        if not self.session:
            raise RuntimeError("Erro")

        for attempt in range(0, self.max_retry):
            try:
                if attempt > 0:
                    print(f"Retrying: {attempt -1}")
                    delay = random.uniform(*self.delay)
                    await asyncio.sleep(delay)

                # raise  Exception('Error')

                async with self.session.get(
                    url, headers=self.browser_headers.random_headers()
                ) as response:
                    return {"html": await response.text()}

            except Exception as e:
                if not attempt == self.max_retry:
                    continue

        return {"error": "Max retries exceeded"}
