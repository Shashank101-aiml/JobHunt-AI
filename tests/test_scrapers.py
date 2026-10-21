import pytest
from app.services.job_scrapers.base import normalize_url, RestrictedJobSourceError
from app.services.job_scrapers.greenhouse_scraper import GreenhouseScraper
from app.services.job_scrapers.lever_scraper import LeverScraper
from app.services.job_scrapers.direct_scraper import DirectUrlScraper
from app.services.job_scrapers.registry import scraper_registry

def test_normalize_url():
    url_with_tracking = "https://boards.greenhouse.io/stripe/jobs/12345?utm_source=linkedin&utm_medium=job_board&ref=aggregator"
    clean = normalize_url(url_with_tracking)
    assert clean == "https://boards.greenhouse.io/stripe/jobs/12345"
    assert "utm_" not in clean

def test_greenhouse_handler_match():
    scraper = GreenhouseScraper()
    assert scraper.can_handle("https://boards.greenhouse.io/anthropic/jobs/123456") is True
    assert scraper.can_handle("https://job-boards.greenhouse.io/openai/jobs/789") is True
    assert scraper.can_handle("https://jobs.lever.co/company/abc") is False

def test_lever_handler_match():
    scraper = LeverScraper()
    assert scraper.can_handle("https://jobs.lever.co/databricks/12345-6789") is True
    assert scraper.can_handle("https://boards.greenhouse.io/anthropic/jobs/123") is False

@pytest.mark.asyncio
async def test_restricted_domain_raises_error():
    scraper = DirectUrlScraper()
    with pytest.raises(RestrictedJobSourceError) as exc_info:
        await scraper.scrape("https://www.linkedin.com/jobs/view/123456789")
    assert "restricted" in str(exc_info.value).lower()
    assert "manual" in str(exc_info.value).lower()
