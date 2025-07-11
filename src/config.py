"""Configuration settings for the Pulse bot."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    
    # API Keys
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    twitter_bearer_token: Optional[str] = None
    
    # Twitter scraping
    twitter_accounts: List[str] = [
        "AndrewYNg",
        "ylecun", 
        "karpathy",
        "goodfellow_ian",
        "fchollet",
        "jeffdean",
        "hardmaru",
        "gabrielpeyre",
        "SebastianRuder",
        "jeremyphoward"
    ]
    
    # Research paper sources
    arxiv_categories: List[str] = [
        "cs.AI",  # Artificial Intelligence
        "cs.LG",  # Machine Learning
        "cs.CV",  # Computer Vision
        "cs.CL",  # Computation and Language
        "cs.NE",  # Neural and Evolutionary Computing
        "stat.ML"  # Machine Learning (Statistics)
    ]
    
    # Blog sources
    ml_blogs: List[str] = [
        "https://ai.googleblog.com/feeds/posts/default",
        "https://openai.com/blog/rss.xml",
        "https://blog.google/technology/ai/",
        "https://research.facebook.com/feed/",
        "https://www.deepmind.com/blog/rss.xml",
        "https://distill.pub/rss.xml",
        "https://blog.paperspace.com/rss/",
        "https://blog.research.google/feeds/posts/default"
    ]
    
    # Summarization settings
    max_summary_length: int = 500
    min_summary_length: int = 100
    max_items_per_source: int = 10
    
    # AWS settings
    aws_region: str = "us-east-1"
    s3_bucket: Optional[str] = None
    
    # Logging
    log_level: str = "INFO"
    
    # Local testing
    local_output_dir: str = "output"


# Global settings instance
settings = Settings() 