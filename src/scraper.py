import json
from urllib.parse import urljoin, urlparse
from playwright.async_api import Page
from src.config import (
    PRODUCT_PATTERNS, BLOCKED_RESOURCES, BLOCKED_KEYWORDS, SCROLL_WAIT_TIME,
    CONTENT_LOAD_TIME, MAX_SCROLLS, PAGE_FETCH_TIMEOUT, MAX_RETRIES, RETRY_DELAY
)
from src.utils import log
from furl import furl
import asyncio


class Scraper:
    def __init__(self, output_file):
        self.output_file = output_file
        self.lock = asyncio.Lock()
        self.visited_urls = set()
        self.domain_product_count = {}

    def should_abort_req(self, request):
        """Determines whether a request should be blocked (e.g., images, tracking scripts)."""
        return request.resource_type in BLOCKED_RESOURCES or any(
            keyword in request.url for keyword in BLOCKED_KEYWORDS
        )

    async def scroll_page(self, page: Page):
        """Scrolls down the page to load dynamic content."""
        log(f"📜 Scrolling down to load all content...")
        last_height = await page.evaluate("document.body.scrollHeight")

        for scroll in range(MAX_SCROLLS):
            await page.wait_for_timeout(CONTENT_LOAD_TIME)
            await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
            await page.wait_for_timeout(SCROLL_WAIT_TIME)
            new_height = await page.evaluate("document.body.scrollHeight")

            if new_height == last_height:
                log(f"✅ No more content to load after {scroll + 1} scrolls.")
                break
            last_height = new_height

    async def fetch_dynamic_content(self, url: str, page: Page):
        """Fetches and processes a single URL by loading the page dynamically."""
        log(f"🎭 Fetching dynamic content for: {url}")

        try:
            await page.route(
                "**/*", lambda route, request: route.abort() if self.should_abort_req(request) else route.continue_()
            )

            await page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Upgrade-Insecure-Requests": "1",
            })

            delay = RETRY_DELAY
            response = None  # Initialize response to avoid UnboundLocalError

            for attempt in range(MAX_RETRIES):
                try:
                    log(f"🌐 Attempt {attempt + 1}: Navigating to {url}")
                    response = await page.goto(url, wait_until="domcontentloaded", timeout=PAGE_FETCH_TIMEOUT)

                    if response and response.status == 200:
                        log(f"✅ Successfully loaded {url}")
                        break  # Exit retry loop if successful
                    else:
                        log(f"⚠️ Attempt {attempt + 1} failed with HTTP status: {response.status if response else 'N/A'}")
                except Exception as e:
                    log(f"❌ Error on attempt {attempt + 1}: {repr(e)}")

                if attempt < MAX_RETRIES - 1:
                    log(f"🔄 Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                    delay *= 2  # Exponential backoff

            if not response or response.status != 200:
                log(f"❌ Failed to load {url} after {MAX_RETRIES} attempts.")
                return [], False

            await self.scroll_page(page)  # Scroll to load more content

            links = await page.eval_on_selector_all("a[href]", "elements => elements.map(el => el.href)")
            log(f"🔗 Extracted {len(links)} links from {url}")

            domain = urlparse(url).netloc.replace('www.', '')
            product_links = set()
            new_urls = set()

            async with self.lock:
                for link in links:
                    link = urljoin(url, link)
                    # Remove fragment identifiers after `#`
                    f = furl(link)
                    f.fragment = ''
                    link = f.url
                    link_domain = urlparse(link).netloc.replace('www.', '')
                    if domain != link_domain or link in self.visited_urls:
                        continue
                    self.visited_urls.add(link)
                    if any(pattern in link for pattern in PRODUCT_PATTERNS):
                        product_links.add(link)
                        log(f"🛒 Found product URL: {link}")
                    new_urls.add(link)
                self.domain_product_count[domain] = self.domain_product_count.get(domain, 0) + len(product_links)
                log(f"✅ Total products for domain {domain} ----> {self.domain_product_count[domain]}")

                if product_links:
                    with open(self.output_file, 'a', encoding='utf-8') as f:
                        result = {
                            'domain': domain,
                            'parent_link': url,
                            'count': len(product_links),
                            'product_links': list(product_links)
                        }
                        f.write(json.dumps(result, ensure_ascii=False) + "\n")
                    log(f"✅ Saved {len(product_links)} product links from {url}")

        ## [not applied] Optimization with minor error (can matter largely for domains like ajio.com): 
        ## We are ignoring child links from URLs with 0 product links to avoid unwanted crawling.
            # if not product_links:
            #     return list() for new urls identified.
            return list(new_urls), True

        except Exception as e:
            log(f"❌ Error processing {url}: {repr(e)}")
            return [], False
