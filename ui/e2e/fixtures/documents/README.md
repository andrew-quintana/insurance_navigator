# Test Documents for E2E Testing

This directory contains test documents used for E2E testing of the document upload functionality.

## Document Types

### Sample Insurance Policy (sample-policy.pdf)
- **Purpose**: Basic document upload testing
- **Size**: Small (< 1MB)
- **Content**: Sample insurance policy with deductible information
- **Use Case**: Standard upload flow testing

### Large Insurance Handbook (large-policy.pdf)
- **Purpose**: Large file upload testing
- **Size**: Large (20-50MB)
- **Content**: Comprehensive benefits handbook
- **Use Case**: Performance testing with large files

### User-Specific Policies
- **user1-policy.pdf**: Test user 1's policy document
- **user2-policy.pdf**: Test user 2's policy document
- **Purpose**: Multi-user document isolation testing

### Invalid Documents
- **corrupted-document.pdf**: Corrupted PDF for error testing
- **Purpose**: Error handling validation

## Usage in Tests

These documents are referenced in the E2E tests to validate:
1. Document upload functionality
2. File validation and error handling
3. Large file performance
4. Multi-user document isolation
5. Chat interface document context integration

## Note

For actual testing, you may need to create real PDF documents or use existing sample documents from your project. The tests are designed to handle cases where these files don't exist by simulating the upload process.
