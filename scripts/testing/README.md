# Testing Scripts

This directory contains scripts for testing various system components.

## Scripts

### CORS Testing
- `test_cors.py` - Comprehensive CORS testing and validation tool
- `test_cors_centralized.py` - Centralized CORS testing with specific focus areas
- `test_specific_url.py` - Test CORS for a specific URL/deployment

## Usage

### Comprehensive CORS Scan
```bash
python scripts/testing/test_cors.py --comprehensive-scan
```

### Test Specific Deployment
```bash
python scripts/testing/test_specific_url.py
```

### Centralized CORS Testing
```bash
python scripts/testing/test_cors_centralized.py
```

## Dependencies

These scripts require:
- Python 3.8+
- `aiohttp` library for async HTTP requests
- Access to the backend API endpoints

## Test Results

CORS test results are automatically saved to `logs/cors_testing/` with timestamps. 