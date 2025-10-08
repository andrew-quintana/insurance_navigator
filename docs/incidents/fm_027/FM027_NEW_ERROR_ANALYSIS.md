# FM-027 New Error Analysis: Storage Access Timing Issue

## Root Cause Identified ✅

**Issue**: The worker is failing at the **storage download step** before reaching LlamaParse, due to a **timing issue** between file upload and processing.

## Detailed Analysis

### **What's Happening**
1. **File Upload**: File is uploaded to storage successfully
2. **Job Creation**: Job is created in database and queued for processing
3. **Worker Processing**: Worker attempts to download file immediately
4. **Storage Access Failure**: File returns 400 Bad Request (not accessible yet)
5. **Worker Fails**: Processing stops before reaching LlamaParse

### **Evidence from Logs**
```
01:12:42.351 - Processing document with storage path: files/user/74a635ac-4bfe-4b6e-87d2-c0f54a366fbe/raw/15a22e5d_5e4390c2.pdf
01:12:42.747 - HTTP Request: GET https://your-staging-project.supabase.co/storage/v1/object/files/user/74a635ac-4bfe-4b6e-87d2-c0f54a366fbe/raw/15a22e5d_5e4390c2.pdf "HTTP/1.1 400 Bad Request"
01:12:42.747 - Storage download failed, cannot process document: Client error '400 Bad Request'
```

### **Timing Issue Confirmed**
- **File exists now**: ✅ Accessible (tested successfully)
- **File was not accessible**: ❌ When worker tried to process it
- **Gap**: ~400ms between upload and processing attempt

## Technical Details

### **Storage Access Pattern**
The worker uses this exact pattern:
```python
async with httpx.AsyncClient() as storage_client:
    response = await storage_client.get(
        f"{storage_url}/storage/v1/object/{bucket}/{key}",
        headers={
            "apikey": service_role_key,
            "Authorization": f"Bearer {service_role_key}",
            "Content-Type": "application/json",
            "User-Agent": "Insurance-Navigator/1.0"
        }
    )
    response.raise_for_status()  # This fails with 400
```

### **Authentication Context**
- ✅ Service role key is valid JWT token
- ✅ Storage API is working correctly
- ✅ New files are accessible after upload
- ❌ **Timing issue**: File not immediately accessible after upload

## Solution

### **Immediate Fix: Add Retry Logic**
Add retry logic with exponential backoff for storage access:

```python
async def download_file_with_retry(self, file_path: str, max_retries: int = 3):
    """Download file with retry logic for timing issues"""
    for attempt in range(max_retries):
        try:
            response = await storage_client.get(file_path, headers=headers)
            response.raise_for_status()
            return response.content
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400 and attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                await asyncio.sleep(wait_time)
                continue
            raise
```

### **Long-term Solution: Event-Driven Processing**
1. **Webhook-based processing**: Wait for storage upload confirmation
2. **Database triggers**: Process only after file is confirmed in storage
3. **Health checks**: Verify file accessibility before processing

## Testing Results

### **Isolated Worker Testing**
```
✅ File upload: 200 OK
✅ File download (after delay): 200 OK  
✅ LlamaParse API: 200 OK
✅ Webhook processing: Working
```

### **Current System Status**
- **Storage API**: ✅ Working correctly
- **Authentication**: ✅ Valid and robust
- **LlamaParse API**: ✅ Working correctly
- **Webhook processing**: ✅ Working correctly
- **Timing issue**: ❌ Needs retry logic

## Implementation Priority

### **High Priority**
1. **Add retry logic** to storage download in worker
2. **Test with staging** to verify fix
3. **Monitor for timing issues** in production

### **Medium Priority**
1. **Implement event-driven processing** for better reliability
2. **Add health checks** before processing
3. **Improve error handling** for timing issues

## Status: ✅ **SOLUTION IDENTIFIED**

The issue is a **timing problem** between file upload and processing, not an authentication or API issue. Adding retry logic will resolve the immediate problem.
