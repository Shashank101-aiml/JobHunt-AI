import re
from typing import Optional
from urllib.parse import urlparse
import httpx
from bs4 import BeautifulSoup

from app.services.job_scrapers.base import (
    BaseJobScraper,
    ScrapedJobData,
    ScraperError,
    normalize_url
)
from app.utils.jd_parser import extract_location_and_type

class GreenhouseScraper(BaseJobScraper):
    """
    Official public integration for Greenhouse job boards.
    Uses Greenhouse's documented public read API for reliable, structured data.
    """

    GREENHOUSE_PATTERN = re.compile(
        r'https?:\/\/(?:boards|job-boards)\.greenhouse\.io\/(?:embed\/job_app\?for=([a-zA-Z0-9_-]+)&token=(\d+)|([a-zA-Z0-9_-]+)\/jobs\/(\d+))'
    )

    def can_handle(self, url: str) -> bool:
        return bool(self.GREENHOUSE_PATTERN.search(url))

    async def scrape(self, url: str) -> ScrapedJobData:
        match = self.GREENHOUSE_PATTERN.search(url)
        if not match:
            raise ScraperError(f"Invalid Greenhouse URL format: {url}")
            
        board_token = match.group(1) or match.group(3)
        job_id = match.group(2) or match.group(4)
        
        api_url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs/{job_id}"
        
        headers = {"Accept": "application/json"}
        try:
            async with httpx.AsyncClient(headers=headers, timeout=12.0) as client:
                resp = await client.get(api_url)
        except Exception as e:
            raise ScraperError(f"Failed to reach Greenhouse API: {str(e)}")

        if resp.status_code == 404:
            raise ScraperError(f"Greenhouse job {job_id} on board '{board_token}' was not found or has been closed.")
        elif resp.status_code != 200:
            raise ScraperError(f"Greenhouse API returned HTTP status {resp.status_code}")

        data = resp.json()
        title = data.get("title", "Software Engineer")
        company = board_token.replace("-", " ").title()
        
        location_obj = data.get("location", {})
        location_name = location_obj.get("name") if isinstance(location_obj, dict) else str(location_obj)
        
        html_content = data.get("content", "")
        # Greenhouse content is HTML-encoded
        soup = BeautifulSoup(html_content, "html.parser")
        description_text = soup.get_text(separator="\n").strip()
        
        loc_extracted, emp_type = extract_location_and_type(description_text)
        final_location = location_name or loc_extracted

        return ScrapedJobData(
            title=title,
            company=company,
            location=final_location,
            employment_type=emp_type or "Full-Time",
            raw_description=description_text,
            source="greenhouse_api",
            source_url=url,
            canonical_url=normalize_url(url),
            publication_date=data.get("updated_at"),
            metadata={
                "board": board_token,
                "job_id": job_id,
                "departments": data.get("departments", []),
                "offices": data.get("offices", [])
            }
        )
