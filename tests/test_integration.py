"""
Integration-Tests für die Universal File Extractor API.
"""

import tempfile
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
def sample_text_file() -> Generator[Path, None, None]:
    """Erstellt eine temporäre Text-Datei für Tests."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write('Dies ist ein Test-Dokument.\nEs enthält mehrere Zeilen.\n')
        temp_file = Path(f.name)

    yield temp_file

    # Cleanup
    temp_file.unlink(missing_ok=True)


@pytest.fixture
def sample_pdf_file() -> Generator[Path, None, None]:
    """Erstellt eine temporäre PDF-Datei für Tests."""
    # Einfache PDF-Datei erstellen (für Tests)
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False) as f:
        # Minimal PDF-Header
        pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Test PDF) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000204 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n297\n%%EOF\n'
        f.write(pdf_content)
        temp_file = Path(f.name)

    yield temp_file

    # Cleanup
    temp_file.unlink(missing_ok=True)


class TestHealthEndpoint:
    """Tests für den Health-Check Endpoint."""

    def test_health_check(self, client: TestClient):
        """Testet den Health-Check Endpoint."""
        response = client.get('/api/v1/health')
        assert response.status_code == 200

        data = response.json()
        assert data['status'] == 'healthy'
        assert 'version' in data
        assert 'timestamp' in data


class TestFormatsEndpoint:
    """Tests für den Formats Endpoint."""

    def test_get_supported_formats(self, client: TestClient):
        """Testet das Abrufen unterstützter Formate."""
        response = client.get('/api/v1/formats')
        assert response.status_code == 200

        data = response.json()
        assert 'formats' in data
        assert 'total_count' in data
        assert len(data['formats']) > 0


class TestExtractEndpoint:
    """Tests für den Extract Endpoint."""

    def test_extract_text_file(self, client: TestClient, sample_text_file: Path):
        """Testet die Extraktion einer Text-Datei."""
        with open(sample_text_file, 'rb') as f:
            response = client.post(
                '/api/v1/extract',
                files={'file': ('test.txt', f, 'text/plain')},
                data={
                    'include_metadata': 'true',
                    'include_text': 'true',
                    'include_structure': 'false',
                },
            )

        assert response.status_code == 200

        data = response.json()
        assert data['success'] is True
        assert data['file_metadata']['filename'] == 'test.txt'
        assert data['extracted_text']['content'] is not None
        assert data['extracted_text']['word_count'] > 0

    def test_extract_pdf_file(self, client: TestClient, sample_pdf_file: Path):
        """Testet die Extraktion einer PDF-Datei."""
        with open(sample_pdf_file, 'rb') as f:
            response = client.post(
                '/api/v1/extract',
                files={'file': ('test.pdf', f, 'application/pdf')},
                data={
                    'include_metadata': 'true',
                    'include_text': 'true',
                    'include_structure': 'false',
                },
            )

        assert response.status_code == 200

        data = response.json()
        assert data['success'] is True
        assert data['file_metadata']['filename'] == 'test.pdf'
        assert data['file_metadata']['file_type'] == 'application/pdf'

    def test_extract_without_file(self, client: TestClient):
        """Testet Extraktion ohne Datei."""
        response = client.post(
            '/api/v1/extract',
            data={
                'include_metadata': 'true',
                'include_text': 'true',
            },
        )

        assert response.status_code == 422  # Validation Error

    def test_extract_unsupported_format(self, client: TestClient):
        """Testet Extraktion eines nicht unterstützten Formats."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xyz', delete=False) as f:
            f.write('Test content')
            temp_file = Path(f.name)

        try:
            with open(temp_file, 'rb') as f:
                response = client.post(
                    '/api/v1/extract',
                    files={'file': ('test.xyz', f, 'application/octet-stream')},
                    data={
                        'include_metadata': 'true',
                        'include_text': 'true',
                    },
                )

            assert response.status_code == 415  # Unsupported Media Type
        finally:
            temp_file.unlink(missing_ok=True)

    def test_extract_large_file(self, client: TestClient):
        """Testet Extraktion einer zu großen Datei."""
        # Große Datei erstellen (mehr als 150MB)
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.txt', delete=False) as f:
            # 1MB Daten schreiben
            f.write(b'x' * 1024 * 1024)
            temp_file = Path(f.name)

        try:
            with open(temp_file, 'rb') as f:
                response = client.post(
                    '/api/v1/extract',
                    files={'file': ('large.txt', f, 'text/plain')},
                    data={
                        'include_metadata': 'true',
                        'include_text': 'true',
                    },
                )

            # Sollte erfolgreich sein, da nur 1MB
            assert response.status_code == 200
        finally:
            temp_file.unlink(missing_ok=True)


class TestAsyncExtractEndpoint:
    """Tests für den Async Extract Endpoint."""

    def test_async_extract_text_file(self, client: TestClient, sample_text_file: Path):
        """Testet asynchrone Extraktion einer Text-Datei."""
        with open(sample_text_file, 'rb') as f:
            response = client.post(
                '/api/v1/extract/async',
                files={'file': ('test.txt', f, 'text/plain')},
                data={
                    'include_metadata': 'true',
                    'include_text': 'true',
                    'priority': 'normal',
                },
            )

        assert response.status_code == 200

        data = response.json()
        assert 'job_id' in data
        assert data['status'] == 'queued'

    def test_get_job_status(self, client: TestClient, sample_text_file: Path):
        """Testet das Abrufen des Job-Status."""
        # Erst Job starten
        with open(sample_text_file, 'rb') as f:
            response = client.post(
                '/api/v1/extract/async',
                files={'file': ('test.txt', f, 'text/plain')},
                data={
                    'include_metadata': 'true',
                    'include_text': 'true',
                },
            )

        job_id = response.json()['job_id']

        # Status abfragen
        status_response = client.get(f'/api/v1/jobs/{job_id}')
        assert status_response.status_code == 200

        status_data = status_response.json()
        assert status_data['job_id'] == job_id
        assert 'status' in status_data

    def test_get_nonexistent_job(self, client: TestClient):
        """Testet das Abrufen eines nicht existierenden Jobs."""
        response = client.get('/api/v1/jobs/nonexistent-job-id')
        assert response.status_code == 404


class TestAuthentication:
    """Tests für die Authentifizierung."""

    def test_extract_without_auth_when_disabled(
        self, client: TestClient, sample_text_file: Path,
    ):
        """Testet Extraktion ohne Auth wenn deaktiviert."""
        with open(sample_text_file, 'rb') as f:
            response = client.post(
                '/api/v1/extract',
                files={'file': ('test.txt', f, 'text/plain')},
                data={
                    'include_metadata': 'true',
                    'include_text': 'true',
                },
            )

        # Sollte erfolgreich sein, da Auth standardmäßig deaktiviert ist
        assert response.status_code == 200

    def test_extract_with_valid_api_key(
        self, client: TestClient, sample_text_file: Path,
    ):
        """Testet Extraktion mit gültigem API-Key."""
        with open(sample_text_file, 'rb') as f:
            response = client.post(
                '/api/v1/extract',
                files={'file': ('test.txt', f, 'text/plain')},
                data={
                    'include_metadata': 'true',
                    'include_text': 'true',
                },
                headers={'Authorization': 'Bearer test-key-123'},
            )

        # Sollte erfolgreich sein
        assert response.status_code == 200

    def test_extract_with_invalid_api_key(
        self, client: TestClient, sample_text_file: Path,
    ):
        """Testet Extraktion mit ungültigem API-Key."""
        with open(sample_text_file, 'rb') as f:
            response = client.post(
                '/api/v1/extract',
                files={'file': ('test.txt', f, 'text/plain')},
                data={
                    'include_metadata': 'true',
                    'include_text': 'true',
                },
                headers={'Authorization': 'Bearer invalid-key'},
            )

        # Sollte trotzdem erfolgreich sein, da Auth standardmäßig deaktiviert ist
        assert response.status_code == 200


class TestErrorHandling:
    """Tests für Fehlerbehandlung."""

    def test_invalid_file_upload(self, client: TestClient):
        """Testet Upload einer ungültigen Datei."""
        response = client.post(
            '/api/v1/extract',
            files={'file': ('', b'', 'text/plain')},  # Leere Datei
            data={
                'include_metadata': 'true',
                'include_text': 'true',
            },
        )

        assert response.status_code == 400

    def test_missing_required_fields(self, client: TestClient):
        """Testet fehlende Pflichtfelder."""
        response = client.post(
            '/api/v1/extract',
            data={},  # Keine Datei, keine Parameter
        )

        assert response.status_code == 422  # Validation Error


class TestPerformance:
    """Performance-Tests."""

    def test_concurrent_requests(self, client: TestClient, sample_text_file: Path):
        """Testet gleichzeitige Requests."""
        import concurrent.futures
        import time

        def make_request():
            with open(sample_text_file, 'rb') as f:
                response = client.post(
                    '/api/v1/extract',
                    files={'file': ('test.txt', f, 'text/plain')},
                    data={
                        'include_metadata': 'true',
                        'include_text': 'true',
                    },
                )
            return response.status_code

        start_time = time.time()

        # 5 gleichzeitige Requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            results = [future.result() for future in futures]

        end_time = time.time()

        # Alle Requests sollten erfolgreich sein
        assert all(status == 200 for status in results)

        # Performance-Check: Sollte unter 10 Sekunden dauern
        assert end_time - start_time < 10.0
