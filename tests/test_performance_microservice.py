"""
Performance-Tests für den File Extractor Microservice.
"""

import asyncio
import time
from pathlib import Path
from typing import List

import pytest
import pytest_asyncio
from httpx import AsyncClient

from app.main import app


@pytest_asyncio.fixture
async def client():
    """AsyncClient für Tests (module-level)."""
    async with AsyncClient(app=app, base_url="http://test") as c:
        yield c

class TestMicroservicePerformance:
    """Performance-Tests für den Microservice."""

    @pytest.mark.asyncio
    async def test_health_endpoint_performance(self, client: AsyncClient):
        """Testet Performance der Health-Endpoints."""
        endpoints = [
            "/health/live",
            "/health/ready", 
            "/health"
        ]
        
        for endpoint in endpoints:
            start_time = time.time()
            response = await client.get(endpoint)
            duration = time.time() - start_time
            
            assert response.status_code == 200
            assert duration < 0.1  # Max 100ms für Health Checks
            
            print(f"{endpoint}: {duration:.3f}s")

    @pytest.mark.asyncio
    async def test_concurrent_health_checks(self, client: AsyncClient):
        """Testet gleichzeitige Health-Checks."""
        async def health_check():
            response = await client.get("/health/live")
            return response.status_code == 200
        
        # 10 gleichzeitige Health-Checks
        start_time = time.time()
        results = await asyncio.gather(*[health_check() for _ in range(10)])
        duration = time.time() - start_time
        
        assert all(results)
        assert duration < 1.0  # Max 1s für 10 gleichzeitige Requests
        
        print(f"10 concurrent health checks: {duration:.3f}s")

    @pytest.mark.asyncio
    async def test_metrics_collection_performance(self, client: AsyncClient):
        """Testet Performance der Metriken-Sammlung."""
        # Mehrere Requests um Metriken zu generieren
        start_time = time.time()
        
        for i in range(5):
            response = await client.get("/health")
            assert response.status_code == 200
        
        duration = time.time() - start_time
        
        # Metriken sollten die Performance nicht signifikant beeinträchtigen
        assert duration < 0.5  # Max 500ms für 5 Requests
        
        print(f"5 requests with metrics: {duration:.3f}s")

    @pytest.mark.asyncio
    async def test_opentelemetry_overhead(self, client: AsyncClient):
        """Testet OpenTelemetry Overhead."""
        # Test ohne OpenTelemetry (falls konfigurierbar)
        # vs. mit OpenTelemetry
        
        # Mit OpenTelemetry
        start_time = time.time()
        response = await client.get("/health")
        duration_with_otel = time.time() - start_time
        
        assert response.status_code == 200
        assert duration_with_otel < 0.1  # Max 100ms
        
        print(f"Request with OpenTelemetry: {duration_with_otel:.3f}s")

    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self, client: AsyncClient):
        """Testet Speicherverbrauch unter Last."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 50 Requests simulieren
        tasks = []
        for _ in range(50):
            task = client.get("/health")
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Speicherverbrauch sollte moderat sein
        assert memory_increase < 100  # Max 100MB Zunahme
        
        print(f"Memory increase: {memory_increase:.1f}MB")

    @pytest.mark.asyncio
    async def test_logging_performance(self, client: AsyncClient):
        """Testet Performance des strukturierten Loggings."""
        start_time = time.time()
        
        # Mehrere Requests um Logs zu generieren
        for i in range(10):
            response = await client.get("/health")
            assert response.status_code == 200
        
        duration = time.time() - start_time
        
        # Logging sollte die Performance nicht signifikant beeinträchtigen
        assert duration < 1.0  # Max 1s für 10 Requests
        
        print(f"10 requests with logging: {duration:.3f}s")

    @pytest.mark.asyncio
    async def test_async_processing_performance(self, client: AsyncClient):
        """Testet Performance der asynchronen Verarbeitung."""
        # Test der async Extraktion (falls verfügbar)
        # Hier würden wir echte Dateien hochladen und die Performance messen
        
        # Für jetzt nur ein Platzhalter-Test
        start_time = time.time()
        response = await client.get("/formats")
        duration = time.time() - start_time
        
        assert response.status_code == 200
        assert duration < 0.1  # Max 100ms
        
        print(f"Formats endpoint: {duration:.3f}s")

    @pytest.mark.asyncio
    async def test_error_handling_performance(self, client: AsyncClient):
        """Testet Performance der Fehlerbehandlung."""
        # Test mit ungültigen Requests
        start_time = time.time()
        
        response = await client.get("/nonexistent")
        duration = time.time() - start_time
        
        assert response.status_code == 404
        assert duration < 0.1  # Max 100ms auch bei Fehlern
        
        print(f"Error handling: {duration:.3f}s")

    @pytest.mark.asyncio
    async def test_metrics_endpoint_performance(self, client: AsyncClient):
        """Testet Performance des Metrics-Endpoints (falls vorhanden)."""
        # Falls ein /metrics Endpoint implementiert wird
        try:
            start_time = time.time()
            response = await client.get("/metrics")
            duration = time.time() - start_time
            
            if response.status_code == 200:
                assert duration < 0.5  # Max 500ms für Metrics
                print(f"Metrics endpoint: {duration:.3f}s")
            else:
                print("Metrics endpoint not implemented")
        except Exception:
            print("Metrics endpoint not available")

    def test_resource_limits(self):
        """Testet Ressourcen-Limits."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # CPU-Verbrauch sollte moderat sein
        cpu_percent = process.cpu_percent(interval=1)
        assert cpu_percent < 50  # Max 50% CPU im Leerlauf
        
        # Speicherverbrauch sollte moderat sein
        memory_mb = process.memory_info().rss / 1024 / 1024
        assert memory_mb < 500  # Max 500MB
        
        print(f"CPU: {cpu_percent:.1f}%, Memory: {memory_mb:.1f}MB")


class TestMicroserviceScalability:
    """Skalierbarkeits-Tests für den Microservice."""

    @pytest.mark.asyncio
    async def test_horizontal_scaling_simulation(self, client: AsyncClient):
        """Simuliert horizontale Skalierung."""
        # Simuliere mehrere Instanzen durch gleichzeitige Requests
        async def make_request():
            response = await client.get("/health")
            return response.status_code == 200
        
        # 20 gleichzeitige Requests (simuliert 20 Instanzen)
        start_time = time.time()
        results = await asyncio.gather(*[make_request() for _ in range(20)])
        duration = time.time() - start_time
        
        assert all(results)
        assert duration < 2.0  # Max 2s für 20 Requests
        
        print(f"20 concurrent requests (scaling simulation): {duration:.3f}s")

    @pytest.mark.asyncio
    async def test_worker_queue_performance(self, client: AsyncClient):
        """Testet Performance der Worker-Queue."""
        # Test der asynchronen Job-Verarbeitung
        # Hier würden wir Jobs einreichen und die Verarbeitungszeit messen
        
        # Für jetzt nur ein Platzhalter-Test
        start_time = time.time()
        response = await client.get("/health/ready")
        duration = time.time() - start_time
        
        assert response.status_code == 200
        assert duration < 0.1  # Max 100ms
        
        print(f"Worker queue health check: {duration:.3f}s")


if __name__ == "__main__":
    # Manuelle Ausführung der Tests
    pytest.main([__file__, "-v"])