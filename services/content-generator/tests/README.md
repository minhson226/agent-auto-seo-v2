# Testing External Integrations

This document explains how external services are mocked in the content-generator test suite, allowing tests to run in CI without real API credentials or external service connections.

## Overview

The content-generator service integrates with several external services:

1. **OpenAI API** - For content generation using GPT-3.5
2. **RabbitMQ** - For event publishing
3. **S3/MinIO** - For image storage

All tests run with mock implementations of these services, ensuring:
- Tests pass without real secrets being set
- No real network calls are made during testing
- Tests are fast and deterministic
- CI pipelines work without external dependencies

## Mock Configurations

### OpenAI (ContentGenerator)

When the `OPENAI_API_KEY` environment variable is empty or not set, the `ContentGenerator` automatically falls back to generating mock content:

```python
# In conftest.py
os.environ["OPENAI_API_KEY"] = ""  # Empty key triggers mock mode
```

The mock content includes:
- A properly structured Markdown article
- Title and keyword incorporation
- Deterministic cost calculations
- Token usage statistics with `-mock` suffix on model name

### RabbitMQ (EventPublisher)

When the `RABBITMQ_URL` starts with `mock://`, the `EventPublisher` operates in mock mode:

```python
# In conftest.py
os.environ["RABBITMQ_URL"] = "mock://localhost:5672/"
```

In mock mode:
- No real RabbitMQ connection is established
- Events are stored in memory (accessible via `publisher.published_events`)
- All publish operations succeed and log appropriately
- Useful for verifying event publishing behavior in tests

### S3/MinIO (ImageStorageService)

When the `S3_ENDPOINT` starts with `mock://`, the `ImageStorageService` operates in mock mode:

```python
# In conftest.py
os.environ["S3_ENDPOINT"] = "mock://localhost:9000"
```

In mock mode:
- No real S3/MinIO connection is established
- Images are stored in an in-memory dictionary
- All upload/delete operations succeed and log appropriately
- Useful for testing image upload workflows without object storage

## Test Settings

The `get_test_settings()` function in `conftest.py` provides a complete test configuration:

```python
def get_test_settings() -> Settings:
    return Settings(
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        JWT_SECRET_KEY="test-secret-key",
        RABBITMQ_URL="mock://localhost:5672/",
        OPENAI_API_KEY="",  # Empty triggers mock content generation
        S3_ENDPOINT="mock://localhost:9000",
        S3_ACCESS_KEY="mock-access-key",
        S3_SECRET_KEY="mock-secret-key",
    )
```

## Running Tests

Tests can be run without any environment configuration:

```bash
# From the content-generator directory
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=term-missing
```

## Testing Real Integrations

If you need to test against real services during development:

1. Set the appropriate environment variables:
   ```bash
   export OPENAI_API_KEY="your-real-api-key"
   export RABBITMQ_URL="amqp://guest:guest@localhost:5672/"
   export S3_ENDPOINT="http://localhost:9000"
   ```

2. Run tests (they will use real services):
   ```bash
   pytest tests/ -v
   ```

**Warning**: Running tests with real API keys will incur costs (OpenAI API calls) and require running services (RabbitMQ, MinIO).

## Verifying Mock Behavior

### ContentGenerator Mock

```python
from app.services.content_generator import ContentGenerator

# Create generator with no API key
generator = ContentGenerator(api_key="")

# Generate mock content
result = await generator.generate_article(
    title="Test Article",
    target_keywords=["seo", "content"],
)

# Verify mock behavior
assert "-mock" in result.model
assert result.content is not None
```

### EventPublisher Mock

```python
from app.services.event_publisher import EventPublisher

# Create publisher in mock mode
publisher = EventPublisher(mock_mode=True)
await publisher.connect()

# Publish event
await publisher.publish("test.event", {"key": "value"})

# Verify event was recorded
assert len(publisher.published_events) == 1
assert publisher.published_events[0]["event_type"] == "test.event"
```

### ImageStorageService Mock

```python
from app.services.image_storage import ImageStorageService

# Create storage in mock mode
storage = ImageStorageService(mock_mode=True)

# Upload image
path = await storage.upload_image(
    article_id=uuid4(),
    file_content=b"image data",
    original_filename="test.jpg",
    content_type="image/jpeg",
)

# Verify image was stored
assert path in storage.mock_storage
```

## Adding New External Services

When adding new external service integrations:

1. Add a mock mode flag to the service class
2. Check for mock mode at the start of methods that make external calls
3. Store results in memory for test inspection
4. Update `conftest.py` with appropriate mock settings
5. Document the mock behavior in this README
