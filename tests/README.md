# Auto-SEO Test Suite

This directory contains all tests for the Auto-SEO platform.

## Directory Structure

```
tests/
├── e2e/                    # End-to-end Playwright tests
│   ├── specs/              # Test specifications
│   ├── fixtures/           # Test data fixtures
│   ├── playwright.config.ts
│   └── package.json
├── integration/            # Integration tests
│   ├── test_event_flow.py  # Event-driven flow tests
│   ├── test_service_integration.py
│   └── conftest.py
└── performance/            # Load testing
    ├── locustfile.py       # Locust load test scenarios
    └── requirements.txt
```

## E2E Tests (Playwright)

End-to-end tests cover complete user workflows.

### Setup

```bash
cd tests/e2e
npm install
npx playwright install
```

### Running Tests

```bash
# Run all tests
npm test

# Run with UI
npm run test:ui

# Run specific test file
npx playwright test specs/authentication.spec.ts

# Run in headed mode
npm run test:headed
```

### Test Scenarios

1. **Content Creation Flow** - Complete workflow from login to article publication
2. **Authentication** - Login, registration, and protected routes
3. **SEO Scoring** - Score viewing and article optimization

## Integration Tests (Python)

Integration tests verify service communication and event flows.

### Setup

```bash
pip install pytest pytest-asyncio
```

### Running Tests

```bash
# From repository root
pytest tests/integration/ -v

# Run specific test
pytest tests/integration/test_event_flow.py -v

# Run with coverage
pytest tests/integration/ --cov=services --cov-report=html
```

### Test Scenarios

1. **Event Flow** - Tests the complete event chain from keyword import to publishing
2. **Service Integration** - Tests inter-service API communication

## Performance Tests (Locust)

Load tests to verify system performance under concurrent users.

### Setup

```bash
pip install -r tests/performance/requirements.txt
```

### Running Tests

```bash
# With web UI
locust -f tests/performance/locustfile.py --host=http://localhost:8000

# Headless mode for CI
locust -f tests/performance/locustfile.py \
  --host=http://localhost:8000 \
  --users 100 \
  --spawn-rate 10 \
  --run-time 5m \
  --headless
```

### User Types

1. **AutoSEOUser** - Standard user behavior
2. **ContentCreationUser** - Focused on content creation workflow
3. **AnalyticsUser** - Focused on viewing analytics

## Running All Tests

```bash
# E2E tests
cd tests/e2e && npm test

# Integration tests
pytest tests/integration/ -v

# Performance tests (requires running services)
locust -f tests/performance/locustfile.py --headless --users 50 --run-time 1m
```

## CI/CD Integration

Tests are automatically run in the CI pipeline:

- E2E tests run on PRs to main
- Integration tests run on every push
- Performance tests run on release branches

## Test Data

Test fixtures are stored in:
- `tests/e2e/fixtures/` - E2E test data (keywords, user data)
- Services maintain their own test fixtures in `services/<service>/tests/`

## Writing New Tests

### E2E Test Example

```typescript
import { test, expect } from '@playwright/test';

test('my new e2e test', async ({ page }) => {
  await page.goto('/my-page');
  await expect(page.locator('.my-element')).toBeVisible();
});
```

### Integration Test Example

```python
import pytest

@pytest.mark.asyncio
async def test_my_integration():
    # Arrange
    event_bus = MockEventBus()
    
    # Act
    await event_bus.publish("my.event", {"data": "test"})
    
    # Assert
    events = event_bus.get_events("my.event")
    assert len(events) == 1
```

## Troubleshooting

### E2E Tests Failing

1. Ensure the frontend dev server is running
2. Check that all dependencies are installed
3. Verify test user credentials

### Integration Tests Failing

1. Check that mock services are correctly configured
2. Verify test database is clean

### Performance Tests Failing

1. Ensure all services are running
2. Check that the host URL is correct
3. Verify sufficient system resources
