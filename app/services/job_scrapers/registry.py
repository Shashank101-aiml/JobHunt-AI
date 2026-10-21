from typing import List
from app.services.job_scrapers.base import BaseJobScraper, ScrapedJobData, ScraperError
from app.services.job_scrapers.greenhouse_scraper import GreenhouseScraper
from app.services.job_scrapers.lever_scraper import LeverScraper
from app.services.job_scrapers.direct_scraper import DirectUrlScraper

class ScraperRegistry:
    def __init__(self):
        self._scrapers: List[BaseJobScraper] = [
            GreenhouseScraper(),
            LeverScraper(),
            DirectUrlScraper(),  # Fallback for standard web pages
        ]

    def register(self, scraper: BaseJobScraper, prepend: bool = True):
        if prepend:
            self._scrapers.insert(0, scraper)
        else:
            self._scrapers.append(scraper)

    async def scrape_job(self, url: str) -> ScrapedJobData:
        if not url or not url.strip():
            raise ScraperError("Job posting URL cannot be empty.")
            
        clean_url = url.strip()
        for scraper in self._scrapers:
            if scraper.can_handle(clean_url):
                return await scraper.scrape(clean_url)
                
        raise ScraperError(f"No suitable scraper adapter found for URL: {clean_url}")

scraper_registry = ScraperRegistry()
