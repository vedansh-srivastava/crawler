import asyncio
import os
import sys
import datetime
from playwright.async_api import async_playwright
from urllib.parse import urlparse

from src.config import (
    INPUT_FILE, OUTPUT_DIR, HEADLESS_MODE, URL_TASK_TIMEOUT,
    MAXIMUM_CONCURRENCY_LIMIT, AUTO_SCALE, DOMAIN_CONCURRENCY_LIMIT,
    DOMAIN_SCRAPING_TIMEOUT
)
from src.scraper import Scraper
from src.queue_manager import QueueManager
from src.utils import load_start_urls, log
from src.load_scaler import LoadScaler


async def process_url(url, queue, scraper, browser):
    """Processes a URL and extracts new links."""
    log(f"🔄 Starting processing for: {url}")
    page = await browser.new_page()
    new_urls, success = [], False
    
    try:
        new_urls, success = await scraper.fetch_dynamic_content(url, page)
        log(f"✅ Successfully fetched content for: {url}")
        await queue.add_urls(new_urls)
    except asyncio.TimeoutError:
        log(f"⏳ Task timed out for URL: {url}", error=True)
    except Exception as e:
        log(f"❌ Error processing {url}: {e}", error=True)
    finally:
        log(f"🔒 Closing page for: {url}")
        await page.close()
    
    return new_urls, success


async def process_tasks(queue, browser, scraper, load_scaler):
    """Processes tasks from the queue with retries within the same domain."""
    tasks = set()
    failed_urls = set()

    while not queue.is_empty() or tasks:
        while len(tasks) < load_scaler.get_concurrency() and not queue.is_empty():
            url = await queue.get()
            log(f"⏳ Processing URL: {url}")
            task = asyncio.create_task(
                asyncio.wait_for(process_url(url, queue, scraper, browser), timeout=URL_TASK_TIMEOUT)
            )
            tasks.add(task)

        done, tasks = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        
        for task in done:
            try:
                new_urls, success = task.result()
                load_scaler.adjust_concurrency(success)
                if new_urls:
                    await queue.add_urls(new_urls)
                if not success:
                    failed_urls.add(url)
            except asyncio.TimeoutError:
                log(f"⏳ Timeout occurred while processing URL: {url}", error=True)
                load_scaler.adjust_concurrency(False)
                failed_urls.add(url)  # Retry later if needed
            except Exception as e:
                log(f"⚠️ Error processing URL: {e}", error=True)
                load_scaler.adjust_concurrency(False)
                failed_urls.add(url)

    return failed_urls


async def process_domain(url, browser, domain_semaphore):
    """Handles crawling for a single domain with concurrency control."""
    domain = urlparse(url).netloc
    domain_filename = domain.replace(".", "_")
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(OUTPUT_DIR, f"{domain_filename}_{timestamp}.txt")

    log(f"🔍 Processing domain: {domain}")
    log(f"📂 Output file for {url} -> {output_file}")

    queue = QueueManager()
    await queue.add_urls([url])
    log(f"📝 Added {url} to queue.")

    scraper = Scraper(output_file)
    load_scaler = LoadScaler(auto_scale=AUTO_SCALE, max_limit=MAXIMUM_CONCURRENCY_LIMIT)
    log(f"🔧 Initial concurrency set to: {load_scaler.get_concurrency()}")

    async with domain_semaphore:
        failed_links = await process_tasks(queue, browser, scraper, load_scaler)
        
        if failed_links:
            log(f"🔄 Retrying {len(failed_links)} failed URLs for domain - {domain}.")
            await queue.add_urls(failed_links)
            await process_tasks(queue, browser, scraper, load_scaler)  # Best effort retry

    log(f"✅ Completed crawling for domain: {domain}")


async def main():
    """Main function to initialize and start the crawler."""
    log("🚀 Starting crawler...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    start_urls = load_start_urls(INPUT_FILE)
    if not start_urls:
        log("❌ No start URLs found. Exiting...", error=True)
        sys.exit(1)

    log(f"📝 Found {len(start_urls)} start URLs. Initializing scrapers per domain...")

    async with async_playwright() as p:
        log("🌐 Launching browser...")
        browser = await p.chromium.launch(headless=HEADLESS_MODE)
        domain_concurrency_semaphore = asyncio.Semaphore(DOMAIN_CONCURRENCY_LIMIT)
        
        domain_tasks = [
            asyncio.create_task(
                asyncio.wait_for(process_domain(url, browser, domain_concurrency_semaphore), timeout=DOMAIN_SCRAPING_TIMEOUT * 3600)
            )
            for url in start_urls
        ]

        log("🚀 All domain scraping tasks started. Waiting for completion...")
        results = await asyncio.gather(*domain_tasks, return_exceptions=True)

        for result, url in zip(results, start_urls):
            if isinstance(result, asyncio.TimeoutError):
                log(f"⏳ Timeout occurred for domain: {url}", error=True)
            elif isinstance(result, Exception):
                log(f"❌ Unhandled error for domain {url}: {result}", error=True)

        log("🎉 Crawling completed. Closing browser.")
        await browser.close()

    log("✅ All tasks finished. Exiting...")


if __name__ == "__main__":
    log("🟢 Starting main execution.")
    asyncio.run(main())