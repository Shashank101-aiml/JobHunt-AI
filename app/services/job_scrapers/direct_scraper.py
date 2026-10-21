import re
from typing import Optional
from urllib.parse import urlparse
import httpx
from bs4 import BeautifulSoup

from app.config import settings
from app.services.job_scrapers.base import (
    BaseJobScraper,
    ScrapedJobData,
    ScraperError,
    RestrictedJobSourceError,
    normalize_url
)
from app.utils.jd_parser import extract_job_title, extract_company_name, extract_location_and_type

RESTRICTED_DOMAINS = [
    "linkedin.com",
    "indeed.com",
    "glassdoor.com",
    "myworkdayjobs.com",
    "workday.com",
    "ziprecruiter.com",
    "simplyhired.com"
]

class DirectUrlScraper(BaseJobScraper):
    """
    Scrapes permitted public job postings from company websites and public boards.
    Respects anti-bot restrictions and redirects users to manual input for restricted platforms.
    """
    
    def can_handle(self, url: str) -> bool:
        return True  # Fallback handler for any permitted HTTP/HTTPS URL

    async def scrape(self, url: str) -> ScrapedJobData:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Check for restricted domains that enforce logins, botwalls, or prohibit scraping
        for restricted in RESTRICTED_DOMAINS:
            if restricted in domain:
                raise RestrictedJobSourceError(
                    f"Automated access to '{restricted}' is restricted by the platform's terms or login barrier. "
                    f"Please copy the job description and use the 'Manual Job Input' feature instead."
                )

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        
        timeout = httpx.Timeout(settings.SCRAPER_TIMEOUT_SECONDS, connect=10.0)
        
        try:
            async with httpx.AsyncClient(headers=headers, timeout=timeout, follow_redirects=True) as client:
                resp = await client.get(url)
        except httpx.TimeoutException:
            raise ScraperError(f"Connection timed out after {settings.SCRAPER_TIMEOUT_SECONDS}s while reaching {url}")
        except httpx.RequestError as e:
            raise ScraperError(f"Network error while connecting to job URL: {str(e)}")

        if resp.status_code == 404:
            raise ScraperError(f"Job posting not found (HTTP 404) at {url}. The listing may have expired or been removed.")
        elif resp.status_code in (401, 403):
            raise ScraperError(
                f"Access denied (HTTP {resp.status_code}) by {domain}. "
                f"The website may require authentication or block automated requests. Please paste the job description manually."
            )
        elif resp.status_code != 200:
            raise ScraperError(f"Failed to retrieve job posting: HTTP status {resp.status_code}")

        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Strip navigation, scripts, ads, footers
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript", "svg", "iframe"]):
            tag.decompose()

        # Find best candidate content container
        content_element = (
            soup.find("main") or
            soup.find("article") or
            soup.find(class_=re.compile(r'(?:job[-_]?description|job[-_]?details|posting[-_]?content|description)', re.I)) or
            soup.find(id=re.compile(r'(?:job[-_]?description|job[-_]?details|content)', re.I)) or
            soup.find("body")
        )
        
        if not content_element:
            raise ScraperError("Could not locate readable job description content on page.")

        raw_text = content_element.get_text(separator="\n")
        # Clean up excessive blank lines
        cleaned_lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
        cleaned_text = "\n".join(cleaned_lines)
        
        if len(cleaned_text) < 50:
            raise ScraperError("Retrieved page content was too short or empty to be a valid job description.")

        canonical = normalize_url(url)
        title = extract_job_title(cleaned_text)
        company = extract_company_name(cleaned_text) or domain.replace("www.", "").split(".")[0].title()
        location, emp_type = extract_location_and_type(cleaned_text)

        return ScrapedJobData(
            title=title,
            company=company,
            location=location,
            employment_type=emp_type,
            raw_description=cleaned_text,
            source="direct_url",
            source_url=url,
            canonical_url=canonical,
            metadata={"domain": domain, "content_length": len(cleaned_text)}
        )
