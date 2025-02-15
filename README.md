# Web Crawler for Discovering Product URLs on E-commerce Websites

## Introduction
A Python-based, asynchronous web crawler using **Playwright** to extract product URLs from e-commerce sites. It efficiently handles infinite scrolling, dynamic content, and varying URL structures.

## Code Overview
### Core Components
- **Initialization**: Reads domains from `data/start_urls.txt` and loads settings from `config.py`.
- **Queue Management**: `queue_manager.py` tracks and processes URLs.
- **Scraping Engine**: `scraper.py` loads pages, extracts product links, and filters them.
- **Concurrency Handling**: `main.py` runs multiple tasks asynchronously.
- **Logging & Error Handling**: `utils.py` logs activity and retries failed requests.

### Functionality
- **Asynchronous Execution**: Uses `asyncio` for parallel scraping.
- **Dynamic Content Handling**: Scrolls pages to load JavaScript-rendered elements.
- **URL Filtering**: Matches product links using predefined patterns (`/p/`, `/products/`, `/product/`, `/dp/`).
- **Performance Optimization**: Blocks unnecessary resources (images, ads) to improve speed.
- **Scalability**: Processes large websites efficiently without excessive memory usage.
- **Robustness**: Handles infinite scrolling, varying site structures, and implements retry mechanisms.

## Running the Crawler
```sh
# Install all the used python packages
python run.py
```

## Input
- A list of e-commerce website domains in .txt file:
```sh 
https://www.example1.com
https://www.example2.com 
https://www.example3.com
```

## Output
- Output stored in `output/results_<timestamp>.txt`.


## Project Structure
```markdown
├── src/
│   ├── __init__.py          # Package initializer
│   ├── config.py            # Configuration settings
│   ├── main.py              # Manages crawling workflow
│   ├── queue_manager.py     # Manages URL queue
│   ├── scraper.py           # Handles page interactions and scraping
│   ├── utils.py             # Utility functions (logging, file handling)
├── data/
│   ├── start_urls.txt       # List of seed URLs
├── output/
│   ├── results_<timestamp>.txt  # Output file containing product URLs
├── run.py                   # Entry point to execute the crawler
├── README.md                # Project documentation
