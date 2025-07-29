.PHONY: help install dev test lint format docs build docker-build docker-run docker-stop clean

# Standardziel
help:
	@echo "Universal File Extractor API - Makefile"
	@echo ""
	@echo "Verfügbare Befehle:"
	@echo "  install      - Dependencies installieren"
	@echo "  dev          - Entwicklungsserver starten"
	@echo "  test         - Tests ausführen"
	@echo "  lint         - Code-Linting"
	@echo "  format       - Code formatieren"
	@echo "  docs         - Dokumentation starten"
	@echo "  build        - Produktions-Build"
	@echo "  docker-build - Docker-Image bauen"
	@echo "  docker-run   - Docker-Compose starten"
	@echo "  docker-stop  - Docker-Compose stoppen"
	@echo "  clean        - Aufräumen"

# Dependencies installieren
install:
	@echo "Installing dependencies..."
	poetry install
	poetry run pre-commit install

# Entwicklungsserver
dev:
	@echo "Starting development server..."
	poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Tests ausführen
test:
	@echo "Running tests..."
	poetry run pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing

# Code-Linting
lint:
	@echo "Running linters..."
	poetry run flake8 app/ tests/
	poetry run mypy app/
	poetry run black --check app/ tests/
	poetry run isort --check-only app/ tests/

# Code formatieren
format:
	@echo "Formatting code..."
	poetry run black app/ tests/
	poetry run isort app/ tests/

# Dokumentation
docs:
	@echo "Starting documentation server..."
	poetry run mkdocs serve

# Dokumentation bauen
docs-build:
	@echo "Building documentation..."
	poetry run mkdocs build

# Produktions-Build
build:
	@echo "Building production version..."
	poetry build

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
	poetry run python -m pytest tests/test_performance.py -v

# Security-Check
security-check:
	@echo "Running security checks..."
	poetry run bandit -r app/
	poetry run safety check

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
		.

# Release erstellen
release:
	@echo "Creating release..."
	poetry version patch
	git add pyproject.toml
	git commit -m "Bump version to $(poetry version -s)"
	git tag v$(poetry version -s)
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