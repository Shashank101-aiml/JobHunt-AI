from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
from pydantic import BaseModel, Field

class ScraperError(Exception):
    """Base exception for scraping operations."""
    pass

class RestrictedJobSourceError(ScraperError):
    """Raised when a target website explicitly restricts automated access or enforces auth walls."""
    pass

class ScrapedJobData(BaseModel):
    title: str
    company: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    raw_description: str
    source: str
    source_url: str
    canonical_url: str
    publication_date: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

def normalize_url(url: str) -> str:
    """Strips tracking query parameters (utm_*, ref, etc.) to produce canonical URL for deduplication."""
    parsed = urlparse(url)
    clean_query = [
        (k, v) for k, v in parse_qsl(parsed.query)
        if not k.startswith("utm_") and k not in ["ref", "gh_src", "lever-source", "source", "fbclid"]
    ]
    canonical = parsed._replace(
        query=urlencode(clean_query),
        fragment=""
    )
    return urlunparse(canonical).rstrip("/")

class BaseJobScraper(ABC):
    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """Returns True if this scraper knows how to handle the given job posting URL."""
        pass

    @abstractmethod
    async def scrape(self, url: str) -> ScrapedJobData:
        """Fetches and parses the target job posting into standardized ScrapedJobData."""
        pass
