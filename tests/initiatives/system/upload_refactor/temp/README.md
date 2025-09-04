# Temporary Tests Directory

This directory contains temporary test files, experimental scripts, and one-off tests that are used during development but are not part of the main test suite.

## Purpose

- Store exploratory tests and experiments
- Keep one-off test scripts organized
- Provide a sandbox for testing new features or debugging issues
- Prevent clutter in the main test directories

## Usage

Feel free to add temporary test files here, but note that these files:

1. Are not automatically run as part of CI/CD pipelines
2. May not be maintained or updated with the rest of the codebase
3. Could be cleaned up periodically

## Moving to Production

If a test in this directory proves useful for long-term use:

1. Refactor it to follow the project's testing standards
2. Move it to the appropriate test directory (unit, integration, etc.)
3. Add documentation as needed
4. Include it in the test suite configuration

## Examples of Appropriate Files

- Proof-of-concept scripts
- Debugging utilities
- Mock generators
- Performance test experiments
- API exploration scripts
- LangSmith integration tests
- Mock validation tests 