from .base import BaseScraper
from .blackrock import BlackRockScraper
from .gs import GSScraper
from .jefferies import JefferiesScraper
from .jpm import JPMScraper
from .ms import MSScraper

SCRAPER_REGISTRY: dict[str, type[BaseScraper]] = {
    "gs_insights":        GSScraper,
    "jpm_insights":       JPMScraper,
    "ms_ideas":           MSScraper,
    "blackrock_bii":      BlackRockScraper,
    "jefferies_insights": JefferiesScraper,
}
