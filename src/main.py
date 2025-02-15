import asyncio
import os
import sys
import datetime
from playwright.async_api import async_playwright
from src.config import INPUT_FILE, OUTPUT_DIR, CONCURRENCY, HEADLESS_MODE
from src.scraper import Scraper
from src.queue_manager import QueueManager
from src.utils import load_start_urls, log

async def process_url(url, queue, scraper, page):
    log(f"🔄 Starting processing for: {url}")
    try:
        new_urls, processed_url = await scraper.fetch_dynamic_content(url, page)
        log(f"✅ Successfully fetched content for: {processed_url}")
        await queue.add_urls(new_urls)
        return processed_url
    except Exception as e:
        log(f"❌ Error processing {url}: {e}", error=True)
    finally:
        log(f"🔒 Closing page for: {url}")
        await page.close()

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

    async with async_playwright() as p:
        log("🌐 Launching browser...")
        browser = await p.chromium.launch(headless=HEADLESS_MODE)
        scraper = Scraper(output_file)
        tasks = set()

        while not queue.is_empty() or tasks:
            # Start new tasks if concurrency limit is not reached
            while len(tasks) < CONCURRENCY and not queue.is_empty():
                current_url = await queue.get()
                log(f"⏳ Processing URL: {current_url}")

                page = await browser.new_page()  # Create a page for this task
                task = asyncio.create_task(process_url(current_url, queue, scraper, page))
                tasks.add(task)

            # Wait for at least one task to complete
            done, tasks = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

            for task in done:
                try:
                    task.result()
                    log("✅ Task completed successfully.")
                except Exception as e:
                    log(f"❌ Task failed with error: {e}", error=True)

        log("🎉 Crawling completed. Closing browser.")
        await browser.close()

if __name__ == "__main__":
    log("🟢 Starting main execution.")
    asyncio.run(main())
