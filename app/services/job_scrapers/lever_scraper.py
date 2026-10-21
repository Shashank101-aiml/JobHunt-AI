import re
from typing import Optional
import httpx
from bs4 import BeautifulSoup

from app.services.job_scrapers.base import (
    BaseJobScraper,
    ScrapedJobData,
    ScraperError,
    normalize_url
)
from app.utils.jd_parser import extract_location_and_type

class LeverScraper(BaseJobScraper):
    """
    Scraper for Lever job board postings (jobs.lever.co/{company}/{id}).
    Lever sites render clean semantic HTML with structured metadata tags.
    """

    LEVER_PATTERN = re.compile(r'https?:\/\/jobs\.lever\.co\/([a-zA-Z0-9_-]+)\/([a-zA-Z0-9-]+)')

    def can_handle(self, url: str) -> bool:
        return bool(self.LEVER_PATTERN.search(url))

    async def scrape(self, url: str) -> ScrapedJobData:
        match = self.LEVER_PATTERN.search(url)
        if not match:
            raise ScraperError(f"Invalid Lever URL format: {url}")
            
        company_slug = match.group(1)
        job_id = match.group(2)
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml"
        }
        
        try:
            async with httpx.AsyncClient(headers=headers, timeout=12.0, follow_redirects=True) as client:
                resp = await client.get(url)
        except Exception as e:
            raise ScraperError(f"Failed to fetch Lever posting: {str(e)}")

        if resp.status_code == 404:
            raise ScraperError(f"Lever job '{job_id}' at company '{company_slug}' was not found or has been closed.")
        elif resp.status_code != 200:
            raise ScraperError(f"Lever page returned HTTP status {resp.status_code}")

        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Lever semantic classes
        title_el = soup.find(class_=re.compile(r'posting-headline')) or soup.find("h2")
        title = title_el.get_text().strip() if title_el else "Software Engineer"
        
        categories_el = soup.find(class_="posting-categories")
        location = None
        commitment = None
        if categories_el:
            loc_tag = categories_el.find(class_="location")
            if loc_tag:
                location = loc_tag.get_text().strip()
            workplace_tag = categories_el.find(class_="workplaceTypes")
            if workplace_tag:
                location = f"{location} ({workplace_tag.get_text().strip()})" if location else workplace_tag.get_text().strip()
            comm_tag = categories_el.find(class_="commitment")
            if comm_tag:
                commitment = comm_tag.get_text().strip()
                
        # Main content
        content_el = soup.find(class_="content") or soup.find("body")
        for tag in content_el(["script", "style", "nav", "footer"]):
            tag.decompose()
            
        description_text = content_el.get_text(separator="\n").strip()
        loc_extracted, emp_type = extract_location_and_type(description_text)

        return ScrapedJobData(
            title=title,
            company=company_slug.replace("-", " ").title(),
            location=location or loc_extracted,
            employment_type=commitment or emp_type or "Full-Time",
            raw_description=description_text,
            source="lever_scraper",
            source_url=url,
            canonical_url=normalize_url(url),
            metadata={"company_slug": company_slug, "job_id": job_id}
        )
