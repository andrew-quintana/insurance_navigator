# Test Fixtures for Full System Integration

This directory contains test fixtures used for comprehensive frontend integration testing.

## Document Fixtures

### Sample Insurance Policy Documents
- `sample-insurance-policy.pdf` - Standard insurance policy for basic testing
- `large-insurance-handbook.pdf` - Large document for performance testing
- `user1-policy.pdf` - Policy document for user isolation testing
- `user2-policy.pdf` - Different policy document for user isolation testing
- `quality-test-policy.pdf` - Document with specific content for conversation quality testing
- `session-test-policy.pdf` - Document for session management testing
- `network-test-policy.pdf` - Document for network interruption testing
- `concurrent-doc-*.pdf` - Documents for concurrent user testing
- `corrupted-document.pdf` - Corrupted document for error handling testing

### Test User Data
- `test-users.json` - Predefined test user accounts for integration testing

## Usage

These fixtures are used by the full system integration tests to validate:
- Document upload and processing
- User data isolation
- Performance under load
- Error handling scenarios
- Conversation quality with real documents

## Adding New Fixtures

When adding new test documents:
1. Ensure they are valid PDF files
2. Include realistic insurance policy content
3. Name them descriptively based on their test purpose
4. Update this README with the new fixture description
