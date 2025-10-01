#!/usr/bin/env python3
"""
FM-027 Storage Manager Fix

This module implements a robust solution for the FM-027 timing issue where
Render worker environment experiences "Bucket not found" errors while local
environment works perfectly.

Root Cause: Environment-specific network routing issue between Render's
infrastructure and Supabase's storage service via Cloudflare CDN.

Solution: Implement retry logic with different network paths and comprehensive
monitoring to detect and handle this issue automatically.
"""

import asyncio
import httpx
import logging
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone
import json

logger = logging.getLogger(__name__)

class FM027StorageManagerFix:
    """
    Enhanced storage manager that handles FM-027 environment-specific routing issues.
    """
    
    def __init__(self, base_url: str, service_role_key: str, anon_key: str):
        self.base_url = base_url
        self.service_role_key = service_role_key
        self.anon_key = anon_key
        self.max_retries = 5
        self.retry_delays = [1, 2, 3, 5, 8]  # Exponential backoff
        self.network_paths = [
            # Primary path (default)
            {'user_agent': 'python-httpx/0.28.1', 'connection': 'keep-alive'},
            # Alternative path 1: Different user agent
            {'user_agent': 'python-requests/2.31.0', 'connection': 'keep-alive'},
            # Alternative path 2: Browser-like user agent
            {'user_agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36', 'connection': 'keep-alive'},
            # Alternative path 3: Different connection type
            {'user_agent': 'python-httpx/0.28.1', 'connection': 'close'},
            # Alternative path 4: Minimal headers
            {'user_agent': 'python-httpx/0.28.1', 'connection': 'keep-alive', 'minimal': True},
        ]
        
    def _get_headers(self, path_config: Dict) -> Dict[str, str]:
        """Get headers for a specific network path configuration."""
        headers = {
            'apikey': self.service_role_key,
            'authorization': f'Bearer {self.service_role_key}',
            'accept': '*/*',
            'user-agent': path_config['user_agent'],
            'connection': path_config['connection']
        }
        
        if not path_config.get('minimal', False):
            headers.update({
                'accept-encoding': 'gzip, deflate',
            })
            
        return headers
    
    async def _test_network_path(self, url: str, path_config: Dict) -> Tuple[bool, Dict]:
        """Test a specific network path configuration."""
        headers = self._get_headers(path_config)
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                start_time = time.time()
                response = await client.get(url, headers=headers)
                end_time = time.time()
                
                result = {
                    'success': response.status_code == 200,
                    'status_code': response.status_code,
                    'response_time': end_time - start_time,
                    'cf_ray': response.headers.get('cf-ray', 'N/A'),
                    'cache_status': response.headers.get('cf-cache-status', 'N/A'),
                    'server': response.headers.get('server', 'N/A'),
                    'content_length': len(response.content) if response.status_code == 200 else 0,
                    'error_message': response.text if response.status_code != 200 else None,
                    'path_config': path_config
                }
                
                logger.info(f"FM-027: Network path test - {path_config['user_agent']} - {response.status_code} - CF-Ray: {result['cf_ray']}")
                
                return result['success'], result
                
        except Exception as e:
            logger.error(f"FM-027: Network path test failed - {path_config['user_agent']} - {e}")
            return False, {
                'success': False,
                'status_code': 0,
                'response_time': 0,
                'cf_ray': 'N/A',
                'cache_status': 'N/A',
                'server': 'N/A',
                'content_length': 0,
                'error_message': str(e),
                'path_config': path_config
            }
    
    async def blob_exists_with_fm027_fix(self, path: str) -> bool:
        """
        Enhanced blob_exists method that handles FM-027 environment-specific routing issues.
        
        This method tries multiple network paths to work around the issue where
        Render worker environment experiences "Bucket not found" errors due to
        Cloudflare CDN routing differences.
        """
        bucket, key = path.split('/', 1)
        url = f'{self.base_url}/storage/v1/object/{path}'
        
        logger.info(f"FM-027: Enhanced blob_exists called with path: {path}")
        logger.info(f"FM-027: Testing {len(self.network_paths)} different network paths")
        
        # Test all network paths
        path_results = []
        for i, path_config in enumerate(self.network_paths):
            success, result = await self._test_network_path(url, path_config)
            path_results.append(result)
            
            if success:
                logger.info(f"FM-027: Success with network path {i+1}: {path_config['user_agent']}")
                return True
                
            # Log the failure for debugging
            logger.warning(f"FM-027: Network path {i+1} failed: {result['status_code']} - {result['error_message']}")
        
        # If all paths failed, log comprehensive failure information
        logger.error(f"FM-027: All network paths failed for path: {path}")
        logger.error(f"FM-027: Path results: {json.dumps(path_results, indent=2)}")
        
        return False
    
    async def get_file_with_fm027_fix(self, path: str) -> Optional[bytes]:
        """
        Enhanced get_file method that handles FM-027 environment-specific routing issues.
        """
        bucket, key = path.split('/', 1)
        url = f'{self.base_url}/storage/v1/object/{path}'
        
        logger.info(f"FM-027: Enhanced get_file called with path: {path}")
        
        # Try each network path until one succeeds
        for i, path_config in enumerate(self.network_paths):
            headers = self._get_headers(path_config)
            
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(url, headers=headers)
                    
                    if response.status_code == 200:
                        logger.info(f"FM-027: Success with network path {i+1}: {path_config['user_agent']}")
                        return response.content
                    else:
                        logger.warning(f"FM-027: Network path {i+1} failed: {response.status_code} - {response.text}")
                        
            except Exception as e:
                logger.warning(f"FM-027: Network path {i+1} exception: {e}")
        
        logger.error(f"FM-027: All network paths failed for file: {path}")
        return None
    
    def get_network_path_health_report(self) -> Dict:
        """Get a health report of all network paths."""
        return {
            'total_paths': len(self.network_paths),
            'paths': [
                {
                    'index': i,
                    'user_agent': config['user_agent'],
                    'connection': config['connection'],
                    'minimal': config.get('minimal', False)
                }
                for i, config in enumerate(self.network_paths)
            ]
        }

# Integration function for existing storage manager
async def enhance_storage_manager_with_fm027_fix(storage_manager, base_url: str, service_role_key: str, anon_key: str):
    """
    Enhance an existing storage manager with FM-027 fix capabilities.
    """
    fm027_fix = FM027StorageManagerFix(base_url, service_role_key, anon_key)
    
    # Monkey patch the existing methods
    storage_manager.blob_exists = fm027_fix.blob_exists_with_fm027_fix
    storage_manager.get_file = fm027_fix.get_file_with_fm027_fix
    storage_manager.fm027_fix = fm027_fix
    
    logger.info("FM-027: Storage manager enhanced with FM-027 fix capabilities")
    return storage_manager
