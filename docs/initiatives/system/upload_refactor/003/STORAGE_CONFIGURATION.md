# Storage Configuration for 003 Worker Refactor

## Overview

This document describes the environment-based storage configuration system implemented to resolve the issue where signed URLs were pointing to production Supabase storage instead of development storage. The system now supports seamless switching between development, staging, and production environments.

## Problem Solved

**Previous Issue**: Signed URLs were hardcoded to point to `https://storage.supabase.co` (production), making it impossible to test file uploads in local development environments.

**Solution**: Implemented environment-based configuration that automatically generates appropriate storage URLs based on the current environment:
- **Development**: `http://localhost:5001` (local mock storage service)
- **Staging**: `https://staging-storage.supabase.co` (staging storage)
- **Production**: `https://storage.supabase.co` (production storage)

## Implementation Details

### 1. Configuration Updates

#### API Configuration (`api/upload_pipeline/config.py`)
- Added `storage_environment` field with validation
- Added `storage_url` field for environment-specific URLs
- Added environment validation for both `environment` and `storage_environment`

#### Upload Endpoint (`api/upload_pipeline/endpoints/upload.py`)
- Updated `_generate_signed_url` function to use environment-based configuration
- Development environment generates URLs pointing to local mock storage
- Staging/Production environments generate URLs pointing to appropriate Supabase storage

### 2. Environment Configuration Files

#### Development (`config/environment/development.yaml`)
- Storage environment: `development`
- Storage URL: `http://localhost:5001`
- Uses mock services for external APIs

#### Staging (`config/environment/staging.yaml`)
- Storage environment: `staging`
- Storage URL: `https://staging-storage.supabase.co`
- Uses real external APIs

#### Production (`config/environment/production.yaml`)
- Storage environment: `production`
- Storage URL: `https://storage.supabase.co`
- Uses real external APIs

### 3. Docker Compose Configuration

#### Local Storage Service
- **Service**: `local-storage`
- **Port**: `5001` (changed from 5000 to avoid conflicts)
- **Type**: Mock storage service for development
- **Health Check**: `/health` endpoint

#### Environment Variables
- `UPLOAD_PIPELINE_STORAGE_ENVIRONMENT`: Controls storage URL generation
- `UPLOAD_PIPELINE_STORAGE_URL`: Base URL for storage service
- `UPLOAD_PIPELINE_ENVIRONMENT`: Overall environment setting

### 4. Mock Storage Service

#### Purpose
- Simulates Supabase storage API for local development
- Provides endpoints for upload, download, and file management
- In-memory storage for testing purposes

#### Endpoints
- `GET /health` - Health check
- `GET /` - Service information
- `GET /storage/v1/object/upload/{path}` - Mock upload endpoint
- `POST /storage/v1/object/sign/{bucket}/{path}` - Mock signed URL creation
- `GET /storage/v1/object/download/{bucket}/{path}` - Mock file download
- `GET /storage/v1/bucket/{bucket}/object/list` - Mock object listing
- `DELETE /storage/v1/object/{bucket}/{path}` - Mock file deletion

## Usage

### Environment Switching

#### Development Environment
```bash
./scripts/switch-environment.sh development
```
- Storage URLs point to `http://localhost:5001`
- Mock services are used for external APIs
- Local development and testing

#### Staging Environment
```bash
./scripts/switch-environment.sh staging
```
- Storage URLs point to `https://staging-storage.supabase.co`
- Real external APIs are used
- Staging/testing environment

#### Production Environment
```bash
./scripts/switch-environment.sh production
```
- Storage URLs point to `https://storage.supabase.co`
- Real external APIs are used
- Production environment

### Testing

#### Test Scripts
- `scripts/test-signed-urls.py` - Tests signed URL generation logic
- `scripts/test-upload-api.py` - Tests API and storage integration
- `scripts/test-signed-url-integration.py` - Tests complete integration

#### Manual Testing
1. Start services: `docker-compose up -d`
2. Check API health: `curl http://localhost:8000/health`
3. Check storage health: `curl http://localhost:5001/health`
4. Test upload endpoint: `curl "http://localhost:5001/storage/v1/object/upload/test.pdf"`

## Benefits

### 1. Local Development
- **Complete Upload Flow Testing**: Can now test both signed URL generation and file upload
- **No Production Dependencies**: All testing happens locally
- **Fast Iteration**: No network latency for storage operations

### 2. Environment Isolation
- **Clear Separation**: Development, staging, and production are completely isolated
- **Safe Testing**: No risk of affecting production data
- **Consistent Behavior**: Same code works across all environments

### 3. Configuration Management
- **Environment-Specific Settings**: Each environment has its own configuration
- **Easy Switching**: Simple script to change environments
- **Version Control**: Configuration files are tracked in git

### 4. Testing and Validation
- **Comprehensive Testing**: Can test the complete upload pipeline
- **Mock Services**: Reliable, predictable behavior for testing
- **Integration Testing**: End-to-end testing of the upload flow

## Technical Details

### URL Generation Logic

#### Development Environment
```python
if config.storage_environment == "development":
    storage_base_url = "http://localhost:5001"
    # Generate direct upload URLs
    return f"{storage_base_url}/storage/v1/object/upload/{key}"
```

#### Staging/Production Environment
```python
else:  # staging or production
    storage_base_url = "https://staging-storage.supabase.co"  # or production
    # Generate Supabase signed URLs
    return f"{storage_base_url}/files/{key}?signed=true&ttl={ttl_seconds}"
```

### Storage Path Handling

#### New Format (`files/user/{userId}/raw/{datetime}_{hash}.{ext}`)
- Full path is used as the storage key
- Maintains Supabase storage structure
- Compatible with existing storage logic

#### Legacy Format (`storage://{bucket}/{key}`)
- Extracts bucket and key from path
- Maintains backward compatibility
- Supports existing storage patterns

## Future Enhancements

### 1. Advanced Storage Features
- **File Compression**: Automatic compression for large files
- **CDN Integration**: Content delivery network for faster access
- **Backup and Replication**: Automatic backup and cross-region replication

### 2. Monitoring and Observability
- **Storage Metrics**: Track storage usage and performance
- **Upload Analytics**: Monitor upload patterns and success rates
- **Error Tracking**: Detailed error reporting and debugging

### 3. Security Enhancements
- **Encryption**: End-to-end encryption for sensitive documents
- **Access Control**: Fine-grained permissions and access management
- **Audit Logging**: Comprehensive audit trail for all operations

## Troubleshooting

### Common Issues

#### Port Conflicts
- **Problem**: Port 5000 is used by macOS AirPlay
- **Solution**: Changed to port 5001 for local storage service

#### Service Startup Issues
- **Problem**: Complex Supabase storage service dependencies
- **Solution**: Implemented simple mock storage service

#### Environment Configuration
- **Problem**: Environment variables not being loaded correctly
- **Solution**: Use `./scripts/switch-environment.sh` to manage configuration

### Debugging

#### Check Service Status
```bash
docker-compose ps
docker-compose logs local-storage
docker-compose logs api-server
```

#### Verify Configuration
```bash
./scripts/switch-environment.sh
```

#### Test Endpoints
```bash
curl http://localhost:8000/health
curl http://localhost:5001/health
```

## Conclusion

The environment-based storage configuration system successfully resolves the issue of signed URLs pointing to production storage in development environments. The implementation provides:

1. **Complete Local Testing**: Full upload flow can now be tested locally
2. **Environment Isolation**: Clear separation between development, staging, and production
3. **Easy Configuration Management**: Simple scripts for environment switching
4. **Comprehensive Testing**: Mock services and test scripts for validation
5. **Future-Proof Architecture**: Extensible design for additional features

This solution enables developers to work locally without affecting production systems while maintaining the ability to test the complete upload pipeline end-to-end.
