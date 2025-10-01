import httpx
import logging
import os
from typing import Dict, Any, Optional, Union
from datetime import datetime, timedelta
import json
import hashlib
import hmac
import secrets
from ..logging.structured_logger import StructuredLogger

logger = StructuredLogger(__name__)

class StorageManager:
    """Storage manager for blob storage operations with Supabase integration"""
    
    def __init__(self, config: Dict[str, Any]):
        self.base_url = config.get("storage_url", "")
        self.anon_key = config.get("anon_key", "")
        self.service_role_key = config.get("service_role_key", "")
        self.timeout = config.get("timeout", 60)
        
        # Validate service role key
        if not self.service_role_key or self.service_role_key.strip() == "":
            # Load from environment variables - try both SUPABASE_SERVICE_ROLE_KEY and SERVICE_ROLE_KEY
            self.service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", os.getenv("SERVICE_ROLE_KEY", ""))
            if not self.service_role_key:
                raise ValueError("SUPABASE_SERVICE_ROLE_KEY environment variable must be set")
            logger.info("Service role key loaded from environment variables")
        
        # HTTP client configuration
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            headers={
                "apikey": self.service_role_key,
                "Authorization": f"Bearer {self.service_role_key}"
            }
        )
        
        logger.info(f"Storage manager initialized for {self.base_url}")
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
    
    async def read_blob(self, path: str) -> Optional[str]:
        """Read blob content from storage"""
        try:
            # Extract bucket and key from path
            bucket, key = self._parse_storage_path(path)
            
            # Use direct access with service role key (same pattern as webhook)
            # This avoids the signed URL generation issues in production
            storage_endpoint = f"{self.base_url}/storage/v1/object/{bucket}/{key}"
            
            # Read content using direct HTTP request
            response = await self.client.get(storage_endpoint)
            response.raise_for_status()
            
            content = response.text
            logger.info(f"Blob read successfully", path=path, size=len(content))
            
            return content
            
        except Exception as e:
            logger.error(f"Failed to read blob: {path}, error: {str(e)}")
            return None
    
    async def write_blob(self, path: str, content: str, content_type: str = "text/plain") -> bool:
        """Write blob content to storage"""
        try:
            # Extract bucket and key from path
            bucket, key = self._parse_storage_path(path)
            
            # Use direct access with service role key (same pattern as webhook)
            # This avoids the signed URL generation issues in production
            storage_endpoint = f"{self.base_url}/storage/v1/object/{bucket}/{key}"
            
            # Write content using direct HTTP request
            response = await self.client.put(
                storage_endpoint,
                content=content.encode('utf-8'),
                headers={"Content-Type": content_type}
            )
            response.raise_for_status()
            
            logger.info(f"Blob written successfully", path=path, size=len(content))
            return True
            
        except Exception as e:
            logger.error(f"Failed to write blob", path=path, error=str(e))
            return False
    
    async def delete_blob(self, path: str) -> bool:
        """Delete blob from storage"""
        try:
            # Extract bucket and key from path
            bucket, key = self._parse_storage_path(path)
            
            # Get signed URL for deletion
            signed_url = await self._get_signed_url(bucket, key, "DELETE")
            
            # Delete content
            response = await self.client.delete(signed_url)
            response.raise_for_status()
            
            logger.info(f"Blob deleted successfully", path=path)
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete blob", path=path, error=str(e))
            return False
    
    async def blob_exists(self, path: str) -> bool:
        """Check if blob exists in storage"""
        try:
            # Extract bucket and key from path
            bucket, key = self._parse_storage_path(path)
            
            # Use correct Supabase storage API endpoint
            storage_endpoint = f"{self.base_url}/storage/v1/object/{bucket}/{key}"
            
            # Check if exists using direct HTTP request
            response = await self.client.head(storage_endpoint)
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Failed to check blob existence", path=path, error=str(e))
            return False
    
    async def get_blob_metadata(self, path: str) -> Optional[Dict[str, Any]]:
        """Get blob metadata from storage"""
        try:
            # Extract bucket and key from path
            bucket, key = self._parse_storage_path(path)
            
            # Use direct access with service role key (same pattern as webhook)
            # This avoids the signed URL generation issues in production
            storage_endpoint = f"{self.base_url}/storage/v1/object/{bucket}/{key}"
            
            # Get metadata using direct HTTP request
            response = await self.client.head(storage_endpoint)
            response.raise_for_status()
            
            metadata = {
                "size": int(response.headers.get("content-length", 0)),
                "content_type": response.headers.get("content-type", ""),
                "last_modified": response.headers.get("last-modified", ""),
                "etag": response.headers.get("etag", "")
            }
            
            logger.info(f"Blob metadata retrieved", path=path, metadata=metadata)
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to get blob metadata", path=path, error=str(e))
            return None
    
    def _parse_storage_path(self, path: str) -> tuple[str, str]:
        """Parse storage path to extract bucket and key"""
        # Handle both formats:
        # 1. storage://{bucket}/user/{user_id}/{document_id}.{ext}
        # 2. files/user/{user_id}/{document_id}.{ext} (legacy format from database)
        
        if path.startswith("storage://"):
            # Remove storage:// prefix
            path_without_prefix = path[10:]
        elif path.startswith("files/"):
            # Legacy format: files/user/... -> bucket=files, key=user/...
            path_without_prefix = path
        else:
            raise ValueError(f"Invalid storage path format: {path}. Expected 'storage://' or 'files/' prefix")
        
        # Split by first slash to get bucket
        parts = path_without_prefix.split("/", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid storage path format: {path}")
        
        bucket, key = parts
        return bucket, key
    
    async def _get_signed_url(self, bucket: str, key: str, method: str) -> str:
        """Get signed URL for storage operation"""
        try:
            # For local development, we'll use direct URLs
            # In production, this would call Supabase storage API to get signed URLs
            if "localhost" in self.base_url or "127.0.0.1" in self.base_url:
                # Local development - direct access
                if method == "GET":
                    return f"{self.base_url}/storage/v1/object/{bucket}/{key}"
                else:
                    return f"{self.base_url}/storage/v1/object/{method}/{bucket}/{key}"
            else:
                # Production - get signed URL from Supabase
                response = await self.client.post(
                    f"{self.base_url}/storage/v1/object/sign/{bucket}/{key}",
                    json={
                        "expiresIn": 300,  # 5 minutes
                        "method": method
                    }
                )
                response.raise_for_status()
                result = response.json()
                return result["signedUrl"]
                
        except Exception as e:
            logger.error(f"Failed to get signed URL", bucket=bucket, key=key, method=method, error=str(e))
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on storage service"""
        try:
            # Simple health check
            response = await self.client.get(f"{self.base_url}/health")
            response.raise_for_status()
            
            return {
                "status": "healthy",
                "service": "storage",
                "base_url": self.base_url,
                "response_time_ms": response.elapsed.total_seconds() * 1000
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "service": "storage",
                "base_url": self.base_url,
                "error": str(e)
            }

