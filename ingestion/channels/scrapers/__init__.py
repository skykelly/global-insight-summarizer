from .base import BaseScraper
from .gs import GSScraper
from .jpm import JPMScraper
from .ms import MSScraper

SCRAPER_REGISTRY: dict[str, type[BaseScraper]] = {
    "gs_insights":  GSScraper,
    "jpm_insights": JPMScraper,
    "ms_ideas":     MSScraper,
}
