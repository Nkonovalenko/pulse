"""Twitter scraper for ML accounts."""

import tweepy
from typing import List, Dict, Any
from datetime import datetime, timedelta
import structlog

from ..config import settings
from .base import BaseScraper

logger = structlog.get_logger()


class TwitterScraper(BaseScraper):
    """Scraper for Twitter content from ML accounts."""
    
    def __init__(self):
        super().__init__("twitter")
        self.client = None
        if settings.twitter_bearer_token:
            self.client = tweepy.Client(bearer_token=settings.twitter_bearer_token)
    
    async def scrape(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Scrape tweets from configured ML accounts."""
        if not self.client:
            self.logger.warning("Twitter client not configured, skipping Twitter scraping")
            return []
        
        all_tweets = []
        
        # Get recent tweets from each account
        for account in settings.twitter_accounts:
            try:
                tweets = await self._get_user_tweets(account, limit)
                all_tweets.extend(tweets)
                self.logger.info(f"Scraped {len(tweets)} tweets from @{account}")
            except Exception as e:
                self.logger.error(f"Error scraping @{account}: {str(e)}")
                continue
        
        # Sort by engagement (likes + retweets) and return top items
        all_tweets.sort(key=lambda x: x.get("engagement_score", 0), reverse=True)
        return all_tweets[:limit]
    
    async def _get_user_tweets(self, username: str, limit: int) -> List[Dict[str, Any]]:
        """Get recent tweets from a specific user."""
        try:
            # Get user ID
            user = self.client.get_user(username=username)
            if not user.data:
                return []
            
            # Get recent tweets (last 24 hours)
            end_time = datetime.now()
            start_time = end_time - timedelta(days=1)
            
            tweets = self.client.get_users_tweets(
                user.data.id,
                max_results=min(limit, 100),
                start_time=start_time,
                end_time=end_time,
                tweet_fields=["created_at", "public_metrics", "context_annotations"],
                exclude=["retweets", "replies"]
            )
            
            if not tweets.data:
                return []
            
            standardized_tweets = []
            for tweet in tweets.data:
                # Filter for ML-related content
                if self._is_ml_related(tweet):
                    standardized_tweet = self._standardize_content({
                        "id": tweet.id,
                        "title": f"Tweet by @{username}",
                        "content": tweet.text,
                        "author": username,
                        "published_at": tweet.created_at,
                        "url": f"https://twitter.com/{username}/status/{tweet.id}",
                        "engagement_score": (
                            tweet.public_metrics.get("like_count", 0) + 
                            tweet.public_metrics.get("retweet_count", 0) * 2
                        ),
                        "tags": self._extract_tags(tweet)
                    })
                    standardized_tweets.append(standardized_tweet)
            
            return standardized_tweets
            
        except Exception as e:
            self.logger.error(f"Error fetching tweets for @{username}: {str(e)}")
            return []
    
    def _is_ml_related(self, tweet) -> bool:
        """Check if tweet is ML-related based on content and context."""
        ml_keywords = [
            "machine learning", "ml", "ai", "artificial intelligence",
            "deep learning", "neural network", "transformer", "llm",
            "computer vision", "nlp", "reinforcement learning", "pytorch",
            "tensorflow", "model", "dataset", "training", "inference"
        ]
        
        text = tweet.text.lower()
        
        # Check for ML keywords
        if any(keyword in text for keyword in ml_keywords):
            return True
        
        # Check context annotations if available
        if hasattr(tweet, 'context_annotations') and tweet.context_annotations:
            for annotation in tweet.context_annotations:
                if annotation.get('domain', {}).get('name') in ['Technology', 'Science']:
                    return True
        
        return False
    
    def _extract_tags(self, tweet) -> List[str]:
        """Extract relevant tags from tweet."""
        tags = []
        
        # Extract hashtags
        if hasattr(tweet, 'entities') and tweet.entities:
            hashtags = tweet.entities.get('hashtags', [])
            tags.extend([tag['tag'] for tag in hashtags])
        
        # Add context-based tags
        text = tweet.text.lower()
        if 'pytorch' in text:
            tags.append('pytorch')
        if 'tensorflow' in text:
            tags.append('tensorflow')
        if 'computer vision' in text or 'cv' in text:
            tags.append('computer_vision')
        if 'nlp' in text or 'natural language' in text:
            tags.append('nlp')
        if 'transformer' in text:
            tags.append('transformer')
        if 'llm' in text or 'large language model' in text:
            tags.append('llm')
        
        return list(set(tags)) 