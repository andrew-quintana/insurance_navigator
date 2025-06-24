import logging
import asyncio
from typing import Dict, Optional
import aiohttp
import backoff

logger = logging.getLogger(__name__)

class LlamaParseService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.llamacloud.ai/v1"
        self.session = None
        
        # Rate limiting configuration
        self.max_concurrent_requests = 2
        self.request_interval = 5  # seconds
        self.active_requests = 0
        self.last_request_time = 0
        
    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
        return self.session
        
    @backoff.on_exception(
        backoff.expo,
        (aiohttp.ClientError, asyncio.TimeoutError),
        max_tries=5,
        max_time=30
    )
    async def parse_document(
        self,
        file_data: bytes,
        filename: str,
        content_type: str
    ) -> Dict[str, str]:
        """
        Parse a document using LlamaParse with proper rate limiting and retries.
        """
        try:
            # Wait for rate limit slot
            await self._wait_for_rate_limit()
            
            session = await self.get_session()
            
            # Prepare upload data
            data = aiohttp.FormData()
            data.add_field(
                'file',
                file_data,
                filename=filename,
                content_type=content_type
            )
            
            self.active_requests += 1
            self.last_request_time = asyncio.get_event_loop().time()
            
            async with session.post(
                f"{self.base_url}/parse",
                data=data,
                timeout=60
            ) as response:
                if response.status == 429:
                    retry_after = int(response.headers.get('Retry-After', '5'))
                    logger.warning(f"Rate limited, waiting {retry_after}s")
                    await asyncio.sleep(retry_after)
                    raise aiohttp.ClientError("Rate limited")
                    
                response.raise_for_status()
                result = await response.json()
                
                return {
                    "success": True,
                    "text": result.get("text", ""),
                    "metadata": result.get("metadata", {})
                }
                
        except Exception as e:
            logger.error(f"LlamaParse error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
            
        finally:
            self.active_requests -= 1
            
    async def _wait_for_rate_limit(self):
        """Wait if we're at the rate limit."""
        while self.active_requests >= self.max_concurrent_requests:
            await asyncio.sleep(0.1)
            
        # Ensure minimum interval between requests
        time_since_last = asyncio.get_event_loop().time() - self.last_request_time
        if time_since_last < self.request_interval:
            await asyncio.sleep(self.request_interval - time_since_last) 