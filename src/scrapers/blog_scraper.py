"""Blog scraper for ML blogs and news sites."""

import feedparser
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from datetime import datetime, timedelta
import structlog

from ..config import settings
from .base import BaseScraper

logger = structlog.get_logger()


class BlogScraper(BaseScraper):
    """Scraper for ML blogs and news sites."""
    
    def __init__(self):
        super().__init__("blogs")
    
    async def scrape(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Scrape recent posts from ML blogs."""
        all_posts = []
        
        for blog_url in settings.ml_blogs:
            try:
                posts = await self._get_blog_posts(blog_url, limit)
                all_posts.extend(posts)
                self.logger.info(f"Scraped {len(posts)} posts from {blog_url}")
            except Exception as e:
                self.logger.error(f"Error scraping {blog_url}: {str(e)}")
                continue
        
        # Sort by publication date and return recent posts
        all_posts.sort(key=lambda x: x.get("published_at", datetime.min), reverse=True)
        return all_posts[:limit]
    
    async def _get_blog_posts(self, blog_url: str, limit: int) -> List[Dict[str, Any]]:
        """Get recent posts from a specific blog."""
        try:
            # Parse RSS feed
            feed = feedparser.parse(blog_url)
            
            if not feed.entries:
                self.logger.warning(f"No entries found for {blog_url}")
                return []
            
            posts = []
            cutoff_date = datetime.now() - timedelta(days=7)  # Last week
            
            for entry in feed.entries[:limit]:
                # Parse publication date
                published_at = datetime.now()
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published_at = datetime(*entry.published_parsed[:6])
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    published_at = datetime(*entry.updated_parsed[:6])
                
                # Skip old posts
                if published_at < cutoff_date:
                    continue
                
                # Extract content
                content = self._extract_content(entry)
                
                post = self._standardize_content({
                    "id": entry.link,
                    "title": entry.title,
                    "content": content,
                    "author": self._extract_author(entry),
                    "published_at": published_at,
                    "url": entry.link,
                    "tags": self._extract_tags(entry)
                })
                
                posts.append(post)
            
            return posts
            
        except Exception as e:
            self.logger.error(f"Error fetching posts for {blog_url}: {str(e)}")
            return []
    
    def _extract_content(self, entry) -> str:
        """Extract content from feed entry."""
        content = ""
        
        # Try different content fields
        if hasattr(entry, 'content') and entry.content:
            content = entry.content[0].value
        elif hasattr(entry, 'summary') and entry.summary:
            content = entry.summary
        elif hasattr(entry, 'description') and entry.description:
            content = entry.description
        
        # Clean HTML
        if content:
            soup = BeautifulSoup(content, 'html.parser')
            content = soup.get_text().strip()
        
        return content
    
    def _extract_author(self, entry) -> str:
        """Extract author from feed entry."""
        if hasattr(entry, 'author') and entry.author:
            return entry.author
        elif hasattr(entry, 'authors') and entry.authors:
            return ", ".join([author.name for author in entry.authors])
        elif hasattr(entry, 'dc_creator') and entry.dc_creator:
            return entry.dc_creator
        
        return "Unknown"
    
    def _extract_tags(self, entry) -> List[str]:
        """Extract tags from feed entry."""
        tags = []
        
        # Extract from tags/categories
        if hasattr(entry, 'tags') and entry.tags:
            tags.extend([tag.term for tag in entry.tags])
        
        # Add content-based tags
        content = (entry.title + " " + self._extract_content(entry)).lower()
        
        ml_keywords = {
            "machine learning": "machine_learning",
            "deep learning": "deep_learning",
            "neural network": "neural_networks",
            "computer vision": "computer_vision",
            "natural language processing": "nlp",
            "reinforcement learning": "reinforcement_learning",
            "transformer": "transformer",
            "llm": "llm",
            "pytorch": "pytorch",
            "tensorflow": "tensorflow",
            "ai": "ai",
            "artificial intelligence": "ai"
        }
        
        for keyword, tag in ml_keywords.items():
            if keyword in content:
                tags.append(tag)
        
        return list(set(tags)) 