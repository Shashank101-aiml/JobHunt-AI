import asyncio
from typing import Dict, Any

from app.utils.jd_parser import normalize_jd
from app.services.job_scrapers import scraper_registry, ScraperError, RestrictedJobSourceError

def scrape_job(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Scraper Agent Node in the LangGraph pipeline.
    Uses modular scrapers to fetch and parse target job posting without mock fallbacks.
    """
    raw_jd = state.get("raw_jd") or state.get("job_text")
    url = state.get("job_url", "")
    
    # If raw JD text was already provided (manual input), parse directly
    if raw_jd and len(raw_jd.strip()) > 30:
        try:
            structured = normalize_jd(raw_jd, source_url=url)
            return {
                "raw_jd": raw_jd,
                "structured_jd": structured.model_dump(),
                "status": "scraping_complete"
            }
        except Exception as e:
            return {
                "error": f"Failed to parse job description: {str(e)}",
                "status": "failed"
            }

    # Otherwise fetch from URL using scraper registry
    if not url or not url.strip():
        return {
            "error": "No job URL or job description text was provided.",
            "status": "failed"
        }

    try:
        # Run async scraper inside sync LangGraph node
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                scraped = pool.submit(asyncio.run, scraper_registry.scrape_job(url)).result()
        else:
            scraped = loop.run_until_complete(scraper_registry.scrape_job(url))

        raw_text = scraped.raw_description
        structured = normalize_jd(raw_text, source_url=url)

        return {
            "raw_jd": raw_text,
            "structured_jd": structured.model_dump(),
            "status": "scraping_complete"
        }
    except (ScraperError, RestrictedJobSourceError) as se:
        return {
            "error": str(se),
            "status": "failed"
        }
    except Exception as e:
        return {
            "error": f"Unexpected error scraping job: {str(e)}",
            "status": "failed"
        }
