# FB Analyzer Tests

This directory contains tests for the FB Analyzer Event Fetcher service.

## Test Structure

- `services/` - Tests for service classes
  - `test_facebook_service.py` - Tests for Facebook Graph API connection
  - `test_facebook_event_fetching.py` - Tests for event fetching functionality

## Running Tests

Since this service is part of a nested repository structure, you should run these tests within the context of the service repository.

### Running Tests Locally

```bash
# Navigate to the service directory
cd services/fb-analyzer-post-fetcher

# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/services/test_facebook_service.py

# Run with verbose output
python -m pytest -v

# Run with coverage report
python -m pytest --cov=app
```

### Running Tests in Docker

```bash
# Navigate to the main repository
cd fb-analyzer

# Build and run tests in the container
docker-compose run --rm fb-analyzer-event-fetcher python -m pytest
```

## Creating New Tests

When creating new tests, follow these guidelines:

1. Place tests in the appropriate subdirectory based on what they're testing
2. Use pytest fixtures for common setup
3. Use mocking for external dependencies (like the Facebook API)
4. Follow the naming convention `test_*.py` for test files

## Branch Protection Workflow

Remember that this repository follows a branch protection workflow:

1. Create a new branch for your test changes
2. Make your changes and commit them
3. Push the branch and create a pull request
4. Get the PR reviewed and merged

Do not push directly to the main branch.
