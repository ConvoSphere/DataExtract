"""
Performance-Tests für die Universal File Extractor API.
"""

import tempfile
import time
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Test-Client für die FastAPI-Anwendung."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def large_text_file() -> Generator[Path, None, None]:
    """Erstellt eine große Text-Datei für Performance-Tests."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        # 1MB Text-Datei erstellen
        content = 'Dies ist ein Test-Dokument für Performance-Tests. ' * 10000
        f.write(content)
        temp_file = Path(f.name)

    yield temp_file

    # Cleanup
    temp_file.unlink(missing_ok=True)


class TestResponseTime:
    """Tests für Response-Zeiten."""

    def test_health_endpoint_response_time(self, client: TestClient):
        """Testet Response-Zeit des Health-Endpoints."""
        start_time = time.time()

        response = client.get('/api/v1/health')

        end_time = time.time()
        response_time = end_time - start_time

        assert response.status_code == 200
        assert response_time < 0.1  # Sollte unter 100ms sein

    def test_formats_endpoint_response_time(self, client: TestClient):
        """Testet Response-Zeit des Formats-Endpoints."""
        start_time = time.time()

        response = client.get('/api/v1/formats')

        end_time = time.time()
        response_time = end_time - start_time

        assert response.status_code == 200
        assert response_time < 0.1  # Sollte unter 100ms sein

    def test_small_file_extraction_time(self, client: TestClient):
        """Testet Extraktionszeit für kleine Dateien."""
        # Kleine Test-Datei erstellen
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('Kleine Test-Datei für Performance-Tests.')
            temp_file = Path(f.name)

        try:
            start_time = time.time()

            with open(temp_file, 'rb') as f:
                response = client.post(
                    '/api/v1/extract',
                    files={'file': ('small.txt', f, 'text/plain')},
                    data={
                        'include_metadata': 'true',
                        'include_text': 'true',
                        'include_structure': 'false',
                    },
                )

            end_time = time.time()
            extraction_time = end_time - start_time

            assert response.status_code == 200
            assert extraction_time < 1.0  # Sollte unter 1 Sekunde sein

        finally:
            temp_file.unlink(missing_ok=True)

    def test_large_file_extraction_time(self, client: TestClient, large_text_file: Path):
        """Testet Extraktionszeit für große Dateien."""
        start_time = time.time()

        with open(large_text_file, 'rb') as f:
            response = client.post(
                '/api/v1/extract',
                files={'file': ('large.txt', f, 'text/plain')},
                data={
                    'include_metadata': 'true',
                    'include_text': 'true',
                    'include_structure': 'false',
                },
            )

        end_time = time.time()
        extraction_time = end_time - start_time

        assert response.status_code == 200
        assert extraction_time < 5.0  # Sollte unter 5 Sekunden sein


class TestConcurrency:
    """Tests für gleichzeitige Requests."""

    def test_concurrent_health_checks(self, client: TestClient):
        """Testet gleichzeitige Health-Check Requests."""
        import concurrent.futures
        import time

        def make_health_check():
            start_time = time.time()
            response = client.get('/api/v1/health')
            end_time = time.time()
            return response.status_code, end_time - start_time

        start_time = time.time()

        # 10 gleichzeitige Health-Checks
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_health_check) for _ in range(10)]
            results = [future.result() for future in futures]

        end_time = time.time()
        total_time = end_time - start_time

        # Alle Requests sollten erfolgreich sein
        status_codes, response_times = zip(*results, strict=False)
        assert all(status == 200 for status in status_codes)

        # Gesamtzeit sollte unter 2 Sekunden sein
        assert total_time < 2.0

        # Durchschnittliche Response-Zeit sollte unter 100ms sein
        avg_response_time = sum(response_times) / len(response_times)
        assert avg_response_time < 0.1

    def test_concurrent_file_extractions(self, client: TestClient):
        """Testet gleichzeitige Datei-Extraktionen."""
        import concurrent.futures
        import time

        def make_extraction_request():
            # Kleine Test-Datei für jeden Request
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(f'Test-Datei für Request {time.time()}')
                temp_file = Path(f.name)

            try:
                start_time = time.time()

                with open(temp_file, 'rb') as f:
                    response = client.post(
                        '/api/v1/extract',
                        files={'file': ('test.txt', f, 'text/plain')},
                        data={
                            'include_metadata': 'true',
                            'include_text': 'true',
                            'include_structure': 'false',
                        },
                    )

                end_time = time.time()
                return response.status_code, end_time - start_time
            finally:
                temp_file.unlink(missing_ok=True)

        start_time = time.time()

        # 5 gleichzeitige Extraktionen
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_extraction_request) for _ in range(5)]
            results = [future.result() for future in futures]

        end_time = time.time()
        total_time = end_time - start_time

        # Alle Requests sollten erfolgreich sein
        status_codes, response_times = zip(*results, strict=False)
        assert all(status == 200 for status in status_codes)

        # Gesamtzeit sollte unter 10 Sekunden sein
        assert total_time < 10.0

        # Durchschnittliche Response-Zeit sollte unter 2 Sekunden sein
        avg_response_time = sum(response_times) / len(response_times)
        assert avg_response_time < 2.0


class TestMemoryUsage:
    """Tests für Speicherverbrauch."""

    def test_memory_usage_small_file(self, client: TestClient):
        """Testet Speicherverbrauch bei kleinen Dateien."""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Kleine Test-Datei
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('Kleine Test-Datei')
            temp_file = Path(f.name)

        try:
            with open(temp_file, 'rb') as f:
                response = client.post(
                    '/api/v1/extract',
                    files={'file': ('small.txt', f, 'text/plain')},
                    data={
                        'include_metadata': 'true',
                        'include_text': 'true',
                    },
                )

            final_memory = process.memory_info().rss
            memory_increase = final_memory - initial_memory

            assert response.status_code == 200
            # Speicherzuwachs sollte unter 50MB sein
            assert memory_increase < 50 * 1024 * 1024

        finally:
            temp_file.unlink(missing_ok=True)

    def test_memory_usage_large_file(self, client: TestClient, large_text_file: Path):
        """Testet Speicherverbrauch bei großen Dateien."""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        with open(large_text_file, 'rb') as f:
            response = client.post(
                '/api/v1/extract',
                files={'file': ('large.txt', f, 'text/plain')},
                data={
                    'include_metadata': 'true',
                    'include_text': 'true',
                },
            )

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        assert response.status_code == 200
        # Speicherzuwachs sollte unter 200MB sein
        assert memory_increase < 200 * 1024 * 1024


class TestThroughput:
    """Tests für Durchsatz."""

    def test_requests_per_second(self, client: TestClient):
        """Testet Requests pro Sekunde."""
        import time

        num_requests = 10
        start_time = time.time()

        for _ in range(num_requests):
            response = client.get('/api/v1/health')
            assert response.status_code == 200

        end_time = time.time()
        total_time = end_time - start_time
        requests_per_second = num_requests / total_time

        # Sollte mindestens 10 Requests pro Sekunde schaffen
        assert requests_per_second > 10.0

    def test_extractions_per_minute(self, client: TestClient):
        """Testet Extraktionen pro Minute."""
        import time

        num_extractions = 5
        start_time = time.time()

        for i in range(num_extractions):
            # Kleine Test-Datei für jede Extraktion
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(f'Test-Datei {i}')
                temp_file = Path(f.name)

            try:
                with open(temp_file, 'rb') as f:
                    response = client.post(
                        '/api/v1/extract',
                        files={'file': (f'test_{i}.txt', f, 'text/plain')},
                        data={
                            'include_metadata': 'true',
                            'include_text': 'true',
                        },
                    )
                assert response.status_code == 200
            finally:
                temp_file.unlink(missing_ok=True)

        end_time = time.time()
        total_time = end_time - start_time
        extractions_per_minute = (num_extractions / total_time) * 60

        # Sollte mindestens 30 Extraktionen pro Minute schaffen
        assert extractions_per_minute > 30.0


class TestScalability:
    """Tests für Skalierbarkeit."""

    def test_file_size_scalability(self, client: TestClient):
        """Testet Skalierbarkeit mit verschiedenen Dateigrößen."""
        import time

        file_sizes = [1024, 10240, 102400]  # 1KB, 10KB, 100KB
        extraction_times = []

        for size in file_sizes:
            # Datei mit entsprechender Größe erstellen
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                content = 'x' * size
                f.write(content)
                temp_file = Path(f.name)

            try:
                start_time = time.time()

                with open(temp_file, 'rb') as f:
                    response = client.post(
                        '/api/v1/extract',
                        files={'file': (f'test_{size}.txt', f, 'text/plain')},
                        data={
                            'include_metadata': 'true',
                            'include_text': 'true',
                        },
                    )

                end_time = time.time()
                extraction_time = end_time - start_time
                extraction_times.append(extraction_time)

                assert response.status_code == 200
            finally:
                temp_file.unlink(missing_ok=True)

        # Extraktionszeit sollte linear mit der Dateigröße skalieren
        # (mit gewisser Toleranz für Overhead)
        time_ratio_1 = extraction_times[1] / extraction_times[0]  # 10KB / 1KB
        time_ratio_2 = extraction_times[2] / extraction_times[0]  # 100KB / 1KB

        # Verhältnis sollte etwa 10:1 und 100:1 sein (mit Toleranz)
        assert 1.2 <= time_ratio_1 <= 25  # Toleranz für 10x
        assert 20 <= time_ratio_2 <= 250  # Toleranz für 100x
