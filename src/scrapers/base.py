"""Base scraper class for all content scrapers."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime
import structlog

logger = structlog.get_logger()


class BaseScraper(ABC):
    """Abstract base class for all content scrapers."""
    
    def __init__(self, source_name: str):
        self.source_name = source_name
        self.logger = logger.bind(scraper=source_name)
    
    @abstractmethod
    async def scrape(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Scrape content from the source.
        
        Args:
            limit: Maximum number of items to scrape
            
        Returns:
            List of content items with standardized fields:
            - id: Unique identifier
            - title: Title of the content
            - content: Main content text
            - author: Author information
            - published_at: Publication timestamp
            - url: Source URL
            - source: Source name
            - tags: List of relevant tags
        """
        pass
    
    def _standardize_content(self, raw_content: Dict[str, Any]) -> Dict[str, Any]:
        """Standardize content format across all scrapers."""
        return {
            "id": raw_content.get("id", ""),
            "title": raw_content.get("title", ""),
            "content": raw_content.get("content", ""),
            "author": raw_content.get("author", ""),
            "published_at": raw_content.get("published_at", datetime.now()),
            "url": raw_content.get("url", ""),
            "source": self.source_name,
            "tags": raw_content.get("tags", [])
        } 