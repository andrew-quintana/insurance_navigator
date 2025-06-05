#!/usr/bin/env python3
import asyncio
import aiohttp
import sys
from test_cors import CORSValidator

async def test_specific_url():
    validator = CORSValidator()
    backend_url = 'https://insurance-navigator-api.onrender.com'
    test_origin = 'https://insurance-navigator-1x3xrmwl5-andrew-quintanas-projects.vercel.app'
    
    print(f'🧪 Testing specific failing URL: {test_origin}')
    
    # Test pattern validation
    result = validator.validate_origin_comprehensive(test_origin)
    print(f'📋 Pattern validation: {result}')
    
    # Test actual CORS
    async with aiohttp.ClientSession() as session:
        cors_result = await validator.test_cors_endpoint_comprehensive(session, backend_url, test_origin)
        print(f'🌐 CORS test result: {cors_result}')

if __name__ == "__main__":
    asyncio.run(test_specific_url()) 