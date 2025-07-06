from dataclasses import dataclass


@dataclass
class SimplePollingConfig:
    """Simple polling configuration for auction data collection"""
    
    retry_delay_seconds: int = 30  # 30 seconds between retries
    head_timeout_seconds: int = 10  # Timeout for HEAD requests
    collection_minute: int = 30  # Collect at :30 past each hour
