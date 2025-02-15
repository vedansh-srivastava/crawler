# Maximum number of scrolls for loading dynamic content
MAX_SCROLLS = 500

# Number of concurrent scraping tasks
CONCURRENCY = 1

# URL patterns to identify product pages
# https://www.flipkart.com : /p/
# https://www.amazon.in : /dp/
# https://burgerbaeclothing.com : /products/
# https://www.bonkerscorner.com/ : /products/
# https://www.lashkaraa.in/ : /products/
# https://www.snapdeal.com/ : /product/
# https://bluorng.com/ : /products/
# https://www.jaywalking.in/ : /products/
# https://www.ajio.com/ : /p/
# https://www.urbanmonkey.com/ : /products/
PRODUCT_PATTERNS = ["/p/", "/products/", "/product/", "/dp/"]

# Resource types to block to improve performance
BLOCKED_RESOURCES = ["image", "stylesheet", "media", "font", "script", "xhr", "fetch"]

# Keywords in URLs that should be blocked (ads & tracking)
BLOCKED_KEYWORDS = [
    "google-analytics", "facebook.com/tr", "doubleclick.net", "adservice",
    "tracking", "pixel", "cdn-cgi", "newrelic", "gtag", "adsystem",
    "amazon-adsystem", "bing.com", "akamaihd.net"
]

# User-Agent for mimicking a real browser
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
)

# Timeout (in ms) for loading pages
PAGE_LOAD_TIMEOUT = 30000

# Headless mode (set to False for debugging)
HEADLESS_MODE = True

# Output directory
OUTPUT_DIR = "output"

# Input file containing start URLs
INPUT_FILE = "data/start_urls.txt"

# Scroll wait time (ms) before checking for new content
SCROLL_WAIT_TIME = 2000

# Content load time (ms) before checking for new content
CONTENT_LOAD_TIME = 2000

# Page fetch time out (ms)
PAGE_FETCH_TIMEOUT = 120000

# Max retries while page fetch
MAX_RETRIES = 3

# Initial delay (in seconds)
RETRY_DELAY = 2