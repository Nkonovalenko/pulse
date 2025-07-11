"""ArXiv scraper for ML research papers."""

import feedparser
import requests
from typing import List, Dict, Any
from datetime import datetime, timedelta
import structlog

from ..config import settings
from .base import BaseScraper

logger = structlog.get_logger()


class ArxivScraper(BaseScraper):
    """Scraper for ArXiv ML research papers."""
    
    def __init__(self):
        super().__init__("arxiv")
        self.base_url = "http://export.arxiv.org/api/query"
    
    async def scrape(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Scrape recent ML papers from ArXiv."""
        all_papers = []
        
        for category in settings.arxiv_categories:
            try:
                papers = await self._get_papers_by_category(category, limit)
                all_papers.extend(papers)
                self.logger.info(f"Scraped {len(papers)} papers from {category}")
            except Exception as e:
                self.logger.error(f"Error scraping {category}: {str(e)}")
                continue
        
        # Sort by submission date and return recent papers
        all_papers.sort(key=lambda x: x.get("published_at", datetime.min), reverse=True)
        return all_papers[:limit]
    
    async def _get_papers_by_category(self, category: str, limit: int) -> List[Dict[str, Any]]:
        """Get recent papers from a specific ArXiv category."""
        try:
            # Get papers from the last 3 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=3)
            
            # Build query
            date_query = f"submittedDate:[{start_date.strftime('%Y%m%d')}* TO {end_date.strftime('%Y%m%d')}*]"
            query = f"cat:{category} AND {date_query}"
            
            params = {
                "search_query": query,
                "start": 0,
                "max_results": min(limit, 100),
                "sortBy": "submittedDate",
                "sortOrder": "descending"
            }
            
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            # Parse the Atom feed
            feed = feedparser.parse(response.text)
            
            papers = []
            for entry in feed.entries:
                paper = self._standardize_content({
                    "id": entry.id,
                    "title": entry.title,
                    "content": entry.summary,
                    "author": ", ".join([author.name for author in entry.authors]),
                    "published_at": datetime.strptime(entry.published, "%Y-%m-%dT%H:%M:%SZ"),
                    "url": entry.link,
                    "tags": [tag.term for tag in entry.tags] + [category]
                })
                
                # Add ArXiv-specific metadata
                paper["arxiv_id"] = entry.id.split("/")[-1]
                paper["category"] = category
                
                papers.append(paper)
            
            return papers
            
        except Exception as e:
            self.logger.error(f"Error fetching papers for {category}: {str(e)}")
            return [] 