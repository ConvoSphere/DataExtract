# Universal File Extractor API Makefile

.PHONY: help setup-dev setup-test setup-prod clean test quality docs docker-build docker-test docker-prod

# Default target
help:
	@echo "Universal File Extractor API - Available Commands:"
	@echo ""
	@echo "Setup Commands:"
	@echo "  setup-dev     - Setup development environment"
	@echo "  setup-test    - Setup testing environment with monitoring"
	@echo "  setup-prod    - Setup production environment"
	@echo ""
	@echo "Development Commands:"
	@echo "  install       - Install dependencies with UV"
	@echo "  test          - Run tests"
	@echo "  quality       - Run code quality checks"
	@echo "  format        - Format code with Ruff"
	@echo "  lint          - Lint code with Ruff"
	@echo "  type-check    - Run type checking with MyPy"
	@echo "  security      - Run security checks"
	@echo ""
	@echo "Docker Commands:"
	@echo "  docker-build  - Build Docker images"
	@echo "  docker-dev    - Start development environment"
	@echo "  docker-test   - Start testing environment"
	@echo "  docker-prod   - Start production environment"
	@echo "  docker-stop   - Stop all containers"
	@echo "  docker-clean  - Clean up Docker resources"
	@echo ""
	@echo "Documentation:"
	@echo "  docs          - Start documentation server"
	@echo "  docs-build    - Build documentation"
	@echo ""
	@echo "Utility Commands:"
	@echo "  clean         - Clean up temporary files"
	@echo "  logs          - Show application logs"
	@echo "  status        - Show service status"

# Setup Commands
setup-dev: install
	@echo "Setting up development environment..."
	pre-commit install
	@echo "Development environment ready!"

setup-test: install
	@echo "Setting up testing environment..."
	docker-compose -f docker-compose.test.yml up -d
	@echo "Testing environment ready! Access monitoring at:"
	@echo "  - Grafana: http://localhost:3000 (admin/admin)"
	@echo "  - Prometheus: http://localhost:9090"
	@echo "  - Jaeger: http://localhost:16686"
	@echo "  - Kibana: http://localhost:5601"

setup-prod: install
	@echo "Setting up production environment..."
	@if [ ! -f .env.prod ]; then \
		echo "Creating .env.prod file..."; \
		cp .env.example .env.prod; \
		echo "Please edit .env.prod with your production settings"; \
	fi
	docker-compose -f docker-compose.prod.yml up -d
	@echo "Production environment ready!"

# Development Commands
install:
	@echo "Installing dependencies with UV..."
	uv sync --group dev
	@echo "Dependencies installed!"

test:
	@echo "Running tests..."
	USE_FAKE_QUEUE=1 uv run pytest tests/ -v --cov=app --cov-report=term-missing

test-coverage:
	@echo "Running tests with coverage report..."
	USE_FAKE_QUEUE=1 uv run pytest tests/ --cov=app --cov-report=html --cov-report=xml

quality: format lint type-check security
	@echo "All quality checks completed!"

format:
	@echo "Formatting code with Ruff..."
	uv run ruff format app/ tests/

lint:
	@echo "Linting code with Ruff..."
	uv run ruff check app/ tests/

type-check:
	@echo "Running type checking with MyPy..."
	uv run mypy app/

security:
	@echo "Running security checks..."
	uv run bandit -r app/ -f json -o bandit-report.json || true
	uv run safety check --json --output safety-report.json || true

# Docker Commands
docker-build:
	@echo "Building Docker images..."
	docker-compose build

docker-dev:
	@echo "Starting development environment..."
	docker-compose up -d
	@echo "Development environment started!"
	@echo "API available at: http://localhost:8000"
	@echo "API docs at: http://localhost:8000/docs"

docker-test:
	@echo "Starting testing environment..."
	docker-compose -f docker-compose.test.yml up -d
	@echo "Testing environment started!"
	@echo "Monitoring available at:"
	@echo "  - Grafana: http://localhost:3000 (admin/admin)"
	@echo "  - Prometheus: http://localhost:9090"
	@echo "  - Jaeger: http://localhost:16686"
	@echo "  - Kibana: http://localhost:5601"

docker-prod:
	@echo "Starting production environment..."
	docker-compose -f docker-compose.prod.yml up -d
	@echo "Production environment started!"
	@echo "API available at: http://localhost:8000 (via nginx)"

docker-stop:
	@echo "Stopping all containers..."
	docker-compose down
	docker-compose -f docker-compose.test.yml down
	docker-compose -f docker-compose.prod.yml down

docker-clean:
	@echo "Cleaning up Docker resources..."
	docker-compose down -v --remove-orphans
	docker-compose -f docker-compose.test.yml down -v --remove-orphans
	docker-compose -f docker-compose.prod.yml down -v --remove-orphans
	docker system prune -f
	docker volume prune -f

# Documentation Commands
docs:
	@echo "Starting documentation server..."
	uv run mkdocs serve

docs-build:
	@echo "Building documentation..."
	uv run mkdocs build

# Utility Commands
clean:
	@echo "Cleaning up temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf dist/
	rm -rf build/
	@echo "Cleanup completed!"

logs:
	@echo "Showing application logs..."
	docker-compose logs -f api

logs-test:
	@echo "Showing test environment logs..."
	docker-compose -f docker-compose.test.yml logs -f

logs-prod:
	@echo "Showing production environment logs..."
	docker-compose -f docker-compose.prod.yml logs -f

status:
	@echo "Development environment status:"
	docker-compose ps
	@echo ""
	@echo "Test environment status:"
	docker-compose -f docker-compose.test.yml ps
	@echo ""
	@echo "Production environment status:"
	docker-compose -f docker-compose.prod.yml ps

# Health checks
health:
	@echo "Checking API health..."
	curl -f http://localhost:8000/api/v1/health || echo "API not responding"

health-test:
	@echo "Checking test environment health..."
	curl -f http://localhost:8000/api/v1/health || echo "API not responding"
	curl -f http://localhost:3000/api/health || echo "Grafana not responding"
	curl -f http://localhost:9090/-/healthy || echo "Prometheus not responding"

# Backup and restore
backup:
	@echo "Creating backup..."
	mkdir -p backup/$(shell date +%Y%m%d)
	docker exec file_extractor_redis redis-cli BGSAVE
	docker cp file_extractor_redis:/data/dump.rdb backup/$(shell date +%Y%m%d)/
	tar -czf backup/$(shell date +%Y%m%d)/app-data.tar.gz logs/ temp_files/ 2>/dev/null || true
	@echo "Backup created in backup/$(shell date +%Y%m%d)/"

restore:
	@echo "Restoring from backup..."
	@if [ -z "$(BACKUP_DATE)" ]; then \
		echo "Usage: make restore BACKUP_DATE=YYYYMMDD"; \
		exit 1; \
	fi
	docker cp backup/$(BACKUP_DATE)/dump.rdb file_extractor_redis:/data/
	docker exec file_extractor_redis redis-cli BGREWRITEAOF
	@echo "Restore completed!"

# Performance testing
perf-test:
	@echo "Running performance tests..."
	USE_FAKE_QUEUE=1 uv run pytest tests/test_performance.py -v

# Integration testing
integration-test:
	@echo "Running integration tests..."
	USE_FAKE_QUEUE=1 uv run pytest tests/integration/ -v

# Load testing
load-test:
	@echo "Running load tests..."
	@if [ -z "$(REQUESTS)" ]; then \
		REQUESTS=100; \
	fi
	@if [ -z "$(CONCURRENT)" ]; then \
		CONCURRENT=10; \
	fi
	uv run python scripts/load_test.py --requests $(REQUESTS) --concurrent $(CONCURRENT)

# Development shortcuts
dev: docker-dev
	@echo "Development environment ready!"

dev-logs: logs
	@echo "Showing development logs..."

dev-restart:
	@echo "Restarting development environment..."
	docker-compose restart api worker

# Production shortcuts
prod: docker-prod
	@echo "Production environment ready!"

prod-logs: logs-prod
	@echo "Showing production logs..."

prod-restart:
	@echo "Restarting production environment..."
	docker-compose -f docker-compose.prod.yml restart api worker

# Testing shortcuts
test-env: docker-test
	@echo "Test environment ready!"

test-logs: logs-test
	@echo "Showing test environment logs..."

test-restart:
	@echo "Restarting test environment..."
	docker-compose -f docker-compose.test.yml restart api worker
