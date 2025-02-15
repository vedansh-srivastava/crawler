import asyncio
from src.utils import log

class QueueManager:
    """Manages a queue of URLs to be processed."""

    def __init__(self):
        self.queue = asyncio.Queue()
        self.lock = asyncio.Lock()  # Ensures thread safety

    async def add_urls(self, urls):
        """Adds multiple URLs to the queue."""
        async with self.lock:
            for url in urls:
                await self.queue.put(url)
                log(f"📤 Added {url} to queue.")

    async def get(self):
        """Retrieves the next URL from the queue."""
        url = await self.queue.get()
        log(f"⏳ Retrieving {url} from queue.")
        return url

    def is_empty(self):
        """Returns True if the queue is empty."""
        return self.queue.empty()

    def size(self):
        """Returns the current size of the queue."""
        return self.queue.qsize()
