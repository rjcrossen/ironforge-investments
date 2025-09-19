"""
Scraper module for fetching data from external sources.

This module provides components for scraping and collecting data
from the Blizzard API and other sources.
"""

from src.scraper.blizzard_api_utils import BlizzardAPI, BlizzardConfig

__all__ = [
    "BlizzardAPI",
    "BlizzardConfig",
]
