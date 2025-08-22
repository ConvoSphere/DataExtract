# Development Guide

## Getting Started

### Prerequisites

- Python 3.11+
- UV Package Manager
- Docker and Docker Compose
- Git

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/universal-file-extractor-api
cd universal-file-extractor-api

# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync --group dev

# Install pre-commit hooks
uv pip install pre-commit
pre-commit install

# Start development environment
docker-compose -f docker-compose.test.yml up -d
```

## Project Structure

```
universal-file-extractor-api/
├── app/                    # Main application code
│   ├── api/               # API routes and endpoints
│   ├── core/              # Core configuration and utilities
│   ├── extractors/        # File extraction modules
│   ├── models/            # Pydantic models
│   ├── workers/           # Celery tasks and workers
│   └── main.py           # FastAPI application entry point
├── tests/                 # Test files
├── docs/                  # Documentation
├── config/                # Configuration files
├── grafana/              # Grafana dashboards and datasources
├── ssl/                  # SSL certificates
├── logs/                 # Application logs
├── docker-compose.yml    # Development environment
├── docker-compose.test.yml # Testing environment
├── docker-compose.prod.yml # Production environment
├── Dockerfile            # Multi-stage Docker build
├── pyproject.toml        # Project configuration
└── README.md             # Project overview
```

## Development Workflow

### Code Quality

The project uses several tools to maintain code quality:

```bash
# Run all quality checks
make quality

# Format code
uv run ruff format app/ tests/

# Lint code
uv run ruff check app/ tests/

# Type checking
uv run mypy app/

# Security checks
uv run bandit -r app/
uv run safety check
```

### Testing

```bash
# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=app --cov-report=html

# Run specific test file
uv run pytest tests/test_extractors.py

# Run tests in parallel
uv run pytest -n auto

# Run integration tests
uv run pytest tests/integration/
```

### Pre-commit Hooks

The project uses pre-commit hooks to ensure code quality:

```bash
# Install hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files

# Run specific hook
pre-commit run ruff --all-files
```

## Adding New Extractors

### 1. Create Extractor Class

```python
# app/extractors/new_format_extractor.py
from pathlib import Path
from typing import Dict, Any, Optional
from app.core.base_extractor import BaseExtractor
from app.models.extraction_result import ExtractionResult

class NewFormatExtractor(BaseExtractor):
    """Extractor for new file format."""

    def __init__(self):
        super().__init__()
        self.supported_formats = ['.newformat']

    async def extract(
        self,
        file_path: Path,
        include_metadata: bool = True,
        include_text: bool = True,
        include_structured_data: bool = False,
        **kwargs
    ) -> ExtractionResult:
        """Extract content from new format file."""

        # Implementation here
        content = await self._extract_content(file_path)

        return ExtractionResult(
            success=True,
            content=content,
            metadata=self._get_metadata(file_path) if include_metadata else None,
            structured_data=self._get_structured_data(content) if include_structured_data else None
        )

    async def _extract_content(self, file_path: Path) -> str:
        """Extract text content from file."""
        # Implementation here
        pass

    def _get_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Get file metadata."""
        # Implementation here
        pass

    def _get_structured_data(self, content: str) -> Dict[str, Any]:
        """Extract structured data from content."""
        # Implementation here
        pass
```

### 2. Register Extractor

```python
# app/core/extractor_registry.py
from app.extractors.new_format_extractor import NewFormatExtractor

EXTRACTORS = {
    # ... existing extractors
    '.newformat': NewFormatExtractor,
}
```

### 3. Add Tests

```python
# tests/test_extractors/test_new_format_extractor.py
import pytest
from pathlib import Path
from app.extractors.new_format_extractor import NewFormatExtractor

class TestNewFormatExtractor:
    @pytest.fixture
    def extractor(self):
        return NewFormatExtractor()

    @pytest.fixture
    def sample_file(self, tmp_path):
        file_path = tmp_path / "sample.newformat"
        file_path.write_text("Sample content")
        return file_path

    async def test_extract_success(self, extractor, sample_file):
        result = await extractor.extract(sample_file)
        assert result.success is True
        assert "Sample content" in result.content

    async def test_extract_unsupported_format(self, extractor, tmp_path):
        file_path = tmp_path / "sample.txt"
        file_path.write_text("Content")

        with pytest.raises(ValueError):
            await extractor.extract(file_path)
```

## API Development

### Adding New Endpoints

```python
# app/api/routes/new_endpoint.py
from fastapi import APIRouter, UploadFile, File, Form
from app.models.extraction_result import ExtractionResult

router = APIRouter()

@router.post("/new-endpoint")
async def new_endpoint(
    file: UploadFile = File(...),
    option: str = Form(default="default")
) -> ExtractionResult:
    """New endpoint description."""

    # Implementation here
    pass
```

### Register Routes

```python
# app/main.py
from app.api.routes import new_endpoint

app.include_router(new_endpoint.router, prefix="/api/v1")
```

## Worker Development

### Adding New Tasks

```python
# app/workers/tasks.py
from celery import shared_task
from app.extractors.extractor_factory import ExtractorFactory

@shared_task(bind=True)
def extract_file_task(self, file_path: str, options: dict):
    """Celery task for file extraction."""

    try:
        extractor = ExtractorFactory.get_extractor(file_path)
        result = extractor.extract_sync(file_path, **options)

        # Update task progress
        self.update_state(
            state='SUCCESS',
            meta={'result': result.dict()}
        )

        return result.dict()

    except Exception as exc:
        self.update_state(
            state='FAILURE',
            meta={'error': str(exc)}
        )
        raise
```

## Configuration

### Environment Variables

```python
# app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Add new configuration options
    NEW_FEATURE_ENABLED: bool = Field(default=False)
    NEW_API_KEY: str = Field(default="")

    class Config:
        env_file = ".env"
```

### Testing Configuration

```python
# tests/conftest.py
import pytest
from app.core.config import Settings

@pytest.fixture
def test_settings():
    return Settings(
        DEBUG=True,
        NEW_FEATURE_ENABLED=True,
        TESTING=True
    )
```

## Database and Caching

### Redis Operations

```python
# app/core/cache.py
import redis
from app.core.config import settings

redis_client = redis.Redis.from_url(settings.REDIS_URL)

async def cache_result(key: str, value: dict, ttl: int = 3600):
    """Cache extraction result."""
    redis_client.setex(key, ttl, json.dumps(value))

async def get_cached_result(key: str) -> Optional[dict]:
    """Get cached result."""
    result = redis_client.get(key)
    return json.loads(result) if result else None
```

## Monitoring and Logging

### Adding Custom Metrics

```python
# app/core/metrics.py
from prometheus_client import Counter, Histogram

# Custom metrics
extraction_requests = Counter(
    'extraction_requests_total',
    'Total extraction requests',
    ['format', 'status']
)

extraction_duration = Histogram(
    'extraction_duration_seconds',
    'Extraction duration in seconds',
    ['format']
)

# Usage in code
@extraction_duration.time()
async def extract_file(file_path: Path):
    try:
        result = await extractor.extract(file_path)
        extraction_requests.labels(
            format=file_path.suffix,
            status='success'
        ).inc()
        return result
    except Exception:
        extraction_requests.labels(
            format=file_path.suffix,
            status='error'
        ).inc()
        raise
```

### Structured Logging

```python
# app/core/logging.py
import structlog

logger = structlog.get_logger()

# Usage in code
logger.info(
    "File extraction started",
    filename=file_path.name,
    file_size=file_path.stat().st_size,
    format=file_path.suffix
)
```

## Performance Optimization

### Async Processing

```python
# Use asyncio for I/O operations
import asyncio
import aiofiles

async def read_file_async(file_path: Path) -> str:
    async with aiofiles.open(file_path, 'r') as f:
        return await f.read()

# Parallel processing
async def process_multiple_files(file_paths: List[Path]):
    tasks = [extract_file(path) for path in file_paths]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

### Memory Optimization

```python
# Use generators for large files
def read_large_file(file_path: Path):
    with open(file_path, 'r') as f:
        for line in f:
            yield line.strip()

# Process in chunks
async def process_in_chunks(items: List, chunk_size: int = 100):
    for i in range(0, len(items), chunk_size):
        chunk = items[i:i + chunk_size]
        await process_chunk(chunk)
```

## Debugging

### Local Development

```bash
# Start with debug mode
DEBUG=true uv run uvicorn app.main:app --reload

# Use debugger
import pdb; pdb.set_trace()

# Or use ipdb for better debugging
uv add --dev ipdb
import ipdb; ipdb.set_trace()
```

### Docker Debugging

```bash
# Access running container
docker-compose exec api bash

# View logs
docker-compose logs -f api

# Debug with docker-compose override
# docker-compose.override.yml
version: '3.8'
services:
  api:
    command: ["uv", "run", "uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
    volumes:
      - .:/app
```

## Contributing

### Pull Request Process

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make your changes
4. Run tests: `uv run pytest`
5. Run quality checks: `make quality`
6. Commit your changes: `git commit -m "Add new feature"`
7. Push to the branch: `git push origin feature/new-feature`
8. Create a Pull Request

### Code Review Checklist

- [ ] Code follows project style guidelines
- [ ] Tests are included and passing
- [ ] Documentation is updated
- [ ] No security vulnerabilities
- [ ] Performance impact is considered
- [ ] Backward compatibility is maintained

### Release Process

```bash
# Update version
uv run bump2version patch  # or minor/major

# Create release
git tag v0.1.1
git push origin v0.1.1

# Build and publish
docker build -t universal-file-extractor:v0.1.1 .
docker push your-registry/universal-file-extractor:v0.1.1
```
