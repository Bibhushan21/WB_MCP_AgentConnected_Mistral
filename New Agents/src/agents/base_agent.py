from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import aiohttp
import asyncio
from datetime import datetime, timedelta
import logging

class BaseAgent(ABC):
    def __init__(self, name: str, cache_duration: int = 3600):
        self.name = name
        self.cache = {}
        self.cache_duration = cache_duration
        self.session: Optional[aiohttp.ClientSession] = None
        self.logger = logging.getLogger(name)

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    @abstractmethod
    async def fetch_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Abstract method to fetch data from the specific data source
        """
        pass

    @abstractmethod
    async def transform_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Abstract method to transform data into the unified schema
        """
        pass

    def get_cache_key(self, params: Dict[str, Any]) -> str:
        """
        Generate a cache key from the parameters
        """
        return f"{self.name}_{str(sorted(params.items()))}"

    def is_cache_valid(self, cache_key: str) -> bool:
        """
        Check if the cached data is still valid
        """
        if cache_key not in self.cache:
            return False
        cached_time = self.cache[cache_key]["timestamp"]
        return (datetime.now() - cached_time).seconds < self.cache_duration

    async def get_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main method to get data with caching and error handling
        """
        cache_key = self.get_cache_key(params)
        
        if self.is_cache_valid(cache_key):
            self.logger.info(f"Returning cached data for {cache_key}")
            return self.cache[cache_key]["data"]

        try:
            raw_data = await self.fetch_data(params)
            transformed_data = await self.transform_data(raw_data)
            
            self.cache[cache_key] = {
                "data": transformed_data,
                "timestamp": datetime.now()
            }
            
            return transformed_data
        except Exception as e:
            self.logger.error(f"Error in {self.name}: {str(e)}")
            raise

    async def handle_retry(self, func, max_retries: int = 3, delay: int = 1):
        """
        Retry mechanism for failed requests
        """
        for attempt in range(max_retries):
            try:
                return await func()
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                self.logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay} seconds...")
                await asyncio.sleep(delay)
                delay *= 2  # Exponential backoff 