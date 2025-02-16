import asyncio
import os
import sys
import datetime
from playwright.async_api import async_playwright
from src.config import INPUT_FILE, OUTPUT_DIR, HEADLESS_MODE, URL_TASK_TIMEOUT, MAXIMUM_CONCURRENCY_LIMIT, AUTO_SCALE
from src.scraper import Scraper
from src.queue_manager import QueueManager
from src.utils import load_start_urls, log
from src.load_scaler import LoadScaler

async def process_url(url, queue, scraper, page):
    """Processes a URL and extracts new links."""
    log(f"🔄 Starting processing for: {url}")
    new_urls = []
    sucess = False
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
    """Process tasks from the queue with given concurrency settings."""
    tasks = set()
    failed_urls = set()
    while not queue.is_empty() or tasks:
        while len(tasks) < load_scaler.get_concurrency() and not queue.is_empty():
            url = await queue.get()
            log(f"⏳ Processing URL: {url}")
            page = await browser.new_page()
            task = asyncio.create_task(
                asyncio.wait_for(process_url(url, queue, scraper, page), timeout=URL_TASK_TIMEOUT)
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
            except Exception as e:
                log(f"⚠️ Error processing URL: {e}", error=True)
                failed_urls.add(url)
            log(f"{len(failed_urls)} failed URLs queued for retry post initial scraping.")
    return failed_urls


async def main():
    """Main function to initialize and start the crawler."""
    log("🚀 Starting crawler...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(OUTPUT_DIR, f"results_{timestamp}.txt")
    log(f"📂 Output file set to: {output_file}")
    start_urls = load_start_urls(INPUT_FILE)
    if not start_urls:
        log("❌ No start URLs found. Exiting...", error=True)
        sys.exit(1)
    queue = QueueManager()
    await queue.add_urls(start_urls)
    log(f"📝 Added {len(start_urls)} start URLs to the queue.")

    # Initialize LoadScaler for adaptive concurrency
    load_scaler = LoadScaler(auto_scale=AUTO_SCALE, max_limit=MAXIMUM_CONCURRENCY_LIMIT)
    async with async_playwright() as p:
        log("🌐 Launching browser...")
        browser = await p.chromium.launch(headless=HEADLESS_MODE)
        scraper = Scraper(output_file)
        
        log(f"🔧 Initial concurrency set to: {load_scaler.get_concurrency()}")
        
        # Process main tasks
        failed_urls = await process_tasks(queue, browser, scraper, load_scaler)

        # Retry failed URLs once
        if failed_urls:
            log(f"🔄 Retrying {len(failed_urls)} failed URLs...")
            await queue.add_urls(failed_urls)
            await process_tasks(queue, browser, scraper, load_scaler)

        log("🎉 Crawling completed. Closing browser.")
        await browser.close()
if __name__ == "__main__":
    log("🟢 Starting main execution.")
    asyncio.run(main())
