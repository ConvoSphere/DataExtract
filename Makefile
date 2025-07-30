.PHONY: help install dev test lint format docs build docker-build docker-run docker-stop clean

# Standardziel
help:
	@echo "Universal File Extractor API - Makefile"
	@echo ""
	@echo "Verfügbare Befehle:"
	@echo "  install      - Dependencies installieren"
	@echo "  dev          - Entwicklungsserver starten"
	@echo "  test         - Tests ausführen"
	@echo "  lint         - Code-Linting mit Ruff"
	@echo "  format       - Code formatieren mit Ruff"
	@echo "  docs         - Dokumentation starten"
	@echo "  build        - Produktions-Build"
	@echo "  docker-build - Docker-Image bauen"
	@echo "  docker-run   - Docker-Compose starten"
	@echo "  docker-stop  - Docker-Compose stoppen"
	@echo "  clean        - Aufräumen"

# Dependencies installieren
install:
	@echo "Installing dependencies with UV..."
	uv sync
	uv pip install pre-commit
	pre-commit install

# Entwicklungsserver
dev:
	@echo "Starting development server..."
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Tests ausführen
test:
	@echo "Running tests..."
	uv run pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing

# Unit-Tests ausführen
test-unit:
	@echo "Running unit tests..."
	uv run pytest tests/ -v -m "not integration and not performance" --cov=app --cov-report=term-missing

# Integration-Tests ausführen
test-integration:
	@echo "Running integration tests..."
	uv run pytest tests/test_integration.py -v --cov=app --cov-report=term-missing

# Performance-Tests ausführen
test-performance:
	@echo "Running performance tests..."
	uv run pytest tests/test_performance.py -v

# Alle Tests mit Coverage
test-all:
	@echo "Running all tests with coverage..."
	uv run pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing --cov-report=xml

# Code-Linting mit Ruff
lint:
	@echo "Running Ruff linter..."
	uv run ruff check app/ tests/
	uv run ruff check --select I app/ tests/  # Import sorting

# Code formatieren mit Ruff
format:
	@echo "Formatting code with Ruff..."
	uv run ruff format app/ tests/
	uv run ruff check --fix app/ tests/

# Code-Linting und Formatierung
lint-fix: format lint

# Dokumentation
docs:
	@echo "Starting documentation server..."
	uv run mkdocs serve

# Dokumentation bauen
docs-build:
	@echo "Building documentation..."
	uv run mkdocs build

# Produktions-Build
build:
	@echo "Building production version..."
	uv build

# Docker-Image bauen
docker-build:
	@echo "Building Docker image..."
	docker build -t file-extractor-api .

# Docker-Compose starten
docker-run:
	@echo "Starting Docker Compose..."
	docker-compose up -d

# Docker-Compose stoppen
docker-stop:
	@echo "Stopping Docker Compose..."
	docker-compose down

# Docker-Compose mit Logs
docker-logs:
	@echo "Showing Docker logs..."
	docker-compose logs -f

# Docker-Compose neu starten
docker-restart:
	@echo "Restarting Docker Compose..."
	docker-compose restart

# Docker-Compose mit Build
docker-up:
	@echo "Building and starting Docker Compose..."
	docker-compose up --build -d

# Test-Umgebung starten
test-env:
	@echo "Starting test environment with monitoring..."
	docker-compose -f docker-compose.test.yml up --build -d

# Test-Umgebung stoppen
test-env-stop:
	@echo "Stopping test environment..."
	docker-compose -f docker-compose.test.yml down

# Test-Umgebung Logs
test-env-logs:
	@echo "Showing test environment logs..."
	docker-compose -f docker-compose.test.yml logs -f

# Test-Umgebung neu starten
test-env-restart:
	@echo "Restarting test environment..."
	docker-compose -f docker-compose.test.yml restart

# Kubernetes Deployment
k8s-deploy:
	@echo "Deploying to Kubernetes..."
	kubectl apply -f k8s/

# Kubernetes Status
k8s-status:
	@echo "Kubernetes status..."
	kubectl get pods -l app=file-extractor-api

# Kubernetes Logs
k8s-logs:
	@echo "Kubernetes logs..."
	kubectl logs -l app=file-extractor-api -f

# Aufräumen
clean:
	@echo "Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf dist/
	rm -rf build/
	rm -rf .ruff_cache/

# Vollständige Bereinigung (inkl. Docker)
clean-all: clean
	@echo "Full cleanup including Docker..."
	docker-compose down -v
	docker system prune -f
	docker volume prune -f

# Health-Check
health:
	@echo "Checking API health..."
	curl -f http://localhost:8000/api/v1/health/live || echo "API not responding"

# API-Dokumentation öffnen
docs-open:
	@echo "Opening API documentation..."
	xdg-open http://localhost:8000/docs 2>/dev/null || open http://localhost:8000/docs 2>/dev/null || echo "Please open http://localhost:8000/docs manually"

# Flower-Monitoring öffnen
flower-open:
	@echo "Opening Flower monitoring..."
	xdg-open http://localhost:5555 2>/dev/null || open http://localhost:5555 2>/dev/null || echo "Please open http://localhost:5555 manually"

# Grafana öffnen
grafana-open:
	@echo "Opening Grafana..."
	xdg-open http://localhost:3000 2>/dev/null || open http://localhost:3000 2>/dev/null || echo "Please open http://localhost:3000 manually"

# Prometheus öffnen
prometheus-open:
	@echo "Opening Prometheus..."
	xdg-open http://localhost:9090 2>/dev/null || open http://localhost:9090 2>/dev/null || echo "Please open http://localhost:9090 manually"

# Beispiel-Datei erstellen
create-sample:
	@echo "Creating sample files..."
	mkdir -p samples
	echo "Dies ist eine Beispiel-Textdatei für die API." > samples/sample.txt
	echo '{"name": "Beispiel", "type": "JSON", "data": [1, 2, 3]}' > samples/sample.json
	echo "Name,Alter,Stadt\nMax,25,Berlin\nAnna,30,München" > samples/sample.csv

# Performance-Test
perf-test:
	@echo "Running performance test..."
	uv run pytest tests/test_performance.py -v

# Security-Check
security-check:
	@echo "Running security checks..."
	uv run ruff check --select S app/  # Security rules
	uv run safety check

# Backup erstellen
backup:
	@echo "Creating backup..."
	tar -czf backup-$(date +%Y%m%d-%H%M%S).tar.gz \
		--exclude='.git' \
		--exclude='__pycache__' \
		--exclude='*.pyc' \
		--exclude='.pytest_cache' \
		--exclude='htmlcov' \
		--exclude='dist' \
		--exclude='build' \
		--exclude='.ruff_cache' \
		.

# Release erstellen
release:
	@echo "Creating release..."
	uv version patch
	git add pyproject.toml
	git commit -m "Bump version to $(uv version)"
	git tag v$(uv version)
	git push origin main --tags

# Development-Setup
setup-dev: install create-sample
	@echo "Development setup complete!"
	@echo "Run 'make dev' to start the development server"
	@echo "Run 'make docs' to start the documentation server"

# Production-Setup
setup-prod: docker-build docker-run
	@echo "Production setup complete!"
	@echo "API is running at http://localhost:8000"
	@echo "Documentation at http://localhost:8000/docs"
	@echo "Monitoring at http://localhost:5555 (Flower)"
	@echo "Metrics at http://localhost:9090 (Prometheus)"
	@echo "Dashboard at http://localhost:3000 (Grafana)"

# UV-spezifische Befehle
uv-sync:
	@echo "Syncing dependencies with UV..."
	uv sync

uv-add:
	@echo "Adding dependency with UV..."
	@read -p "Enter package name: " package; \
	uv add $$package

uv-add-dev:
	@echo "Adding dev dependency with UV..."
	@read -p "Enter package name: " package; \
	uv add --dev $$package

uv-remove:
	@echo "Removing dependency with UV..."
	@read -p "Enter package name: " package; \
	uv remove $$package

uv-update:
	@echo "Updating dependencies with UV..."
	uv lock --upgrade

# Ruff-spezifische Befehle
ruff-check:
	@echo "Running Ruff checks..."
	uv run ruff check app/ tests/

ruff-format:
	@echo "Running Ruff formatter..."
	uv run ruff format app/ tests/

ruff-fix:
	@echo "Running Ruff with auto-fix..."
	uv run ruff check --fix app/ tests/

# Docling-spezifische Befehle
install-docling:
	@echo "Installing docling..."
	uv add docling

test-docling:
	@echo "Testing docling integration..."
	uv run python -c "import docling; print('Docling version:', docling.__version__)"

# Code-Qualität
quality: lint-fix test
	@echo "Code quality check complete!"

# Vollständiger Check
check: quality security-check
	@echo "Full check complete!"