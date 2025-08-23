"""
Ende-zu-Ende Black-Box Tests gegen die laufende Container-API.

Diese Tests bauen/ starten das Testing-Docker-Compose, warten auf Readiness
und testen alle externen API-Endpunkte über echte HTTP-Requests.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import TYPE_CHECKING

import httpx
import pytest

if TYPE_CHECKING:
    from collections.abc import Generator, Iterator

API_BASE = 'http://localhost:8000/api/v1'
COMPOSE_FILE = 'docker-compose.test.yml'


def _docker_compose_base_cmd() -> list[str] | None:
    """Findet einen verfügbaren Docker Compose Befehl.

    Präferiert Docker Compose v2 ("docker compose"), fällt zurück auf v1 ("docker-compose").
    Gibt None zurück wenn keine Variante verfügbar ist.
    """
    if shutil.which('docker') is not None:
        # Teste ob "docker compose" verfügbar ist
        try:
            subprocess.run(
                ['docker', 'compose', 'version'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )
            return ['docker', 'compose']
        except Exception:
            pass
    if shutil.which('docker-compose') is not None:
        return ['docker-compose']
    return None


@pytest.fixture(scope='session')
def _compose_up() -> Iterator[None]:
    """Startet docker-compose für die Testumgebung und räumt am Ende auf."""
    base = _docker_compose_base_cmd()
    if base is None:
        pytest.skip('Docker/Compose nicht verfügbar – E2E-Tests werden übersprungen')

    # Build + Up (non-interaktiv)
    cmd_up = [*base, '-f', COMPOSE_FILE, 'up', '-d', '--build']
    subprocess.run(cmd_up, check=True)

    # Warten bis API healthy ist
    deadline = time.time() + 300  # 5 Minuten Timeout für kalten Start
    last_err: str | None = None
    while time.time() < deadline:
        try:
            resp = httpx.get(f'{API_BASE}/health', timeout=5.0)
            if resp.status_code == 200 and resp.json().get('status') in {
                'healthy',
                'ready',
            }:
                break
            last_err = f'status={resp.status_code} body={resp.text!r}'
        except Exception as e:
            last_err = str(e)
        time.sleep(2)
    else:
        raise RuntimeError(f'API did not become ready in time: {last_err}')

    yield

    # Down + prune volumes of this stack
    cmd_down = [*base, '-f', COMPOSE_FILE, 'down', '-v', '--remove-orphans']
    subprocess.run(cmd_down, check=False)


@pytest.fixture(scope='session')
def http_client(_compose_up: None) -> Generator[httpx.Client, None, None]:
    """HTTP-Client gegen die laufende API im Container."""
    with httpx.Client(base_url=API_BASE, timeout=30.0) as client:
        yield client


@pytest.fixture
def sample_text_file() -> Generator[Path, None, None]:
    """Erstellt eine temporäre Textdatei für Upload-Tests."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write('Dies ist ein Test-Dokument.\nEs enthält mehrere Zeilen.\n')
        temp_path = Path(f.name)
    yield temp_path
    temp_path.unlink(missing_ok=True)


@pytest.fixture
def sample_pdf_file() -> Generator[Path, None, None]:
    """Erstellt eine minimale PDF-Datei für Upload-Tests."""
    pdf_bytes = (
        b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n'
        b'2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n'
        b'3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n'
        b'4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Test PDF) Tj\nET\nendstream\nendobj\n'
        b'xref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000204 00000 n \n'
        b'trailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n297\n%%EOF\n'
    )
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False) as f:
        f.write(pdf_bytes)
        temp_path = Path(f.name)
    yield temp_path
    temp_path.unlink(missing_ok=True)


@pytest.mark.e2e
class TestE2EHealth:
    def test_health(self, http_client: httpx.Client) -> None:
        resp = http_client.get('/health')
        assert resp.status_code == 200
        data = resp.json()
        assert data.get('status') in {'healthy', 'ready'}

    def test_health_ready(self, http_client: httpx.Client) -> None:
        resp = http_client.get('/health/ready')
        assert resp.status_code == 200
        assert resp.json().get('status') in {'ready', 'not_ready'}

    def test_health_live(self, http_client: httpx.Client) -> None:
        resp = http_client.get('/health/live')
        assert resp.status_code == 200
        assert resp.json().get('status') == 'alive'

    def test_health_detailed(self, http_client: httpx.Client) -> None:
        resp = http_client.get('/health/detailed')
        assert resp.status_code == 200
        assert 'configuration' in resp.json()


@pytest.mark.e2e
class TestE2EFormats:
    def test_formats(self, http_client: httpx.Client) -> None:
        resp = http_client.get('/formats')
        assert resp.status_code == 200
        data = resp.json()
        assert 'formats' in data
        assert 'total_count' in data
        assert isinstance(data['formats'], list)


@pytest.mark.e2e
class TestE2EExtract:
    def test_extract_text(
        self,
        http_client: httpx.Client,
        sample_text_file: Path,
    ) -> None:
        with sample_text_file.open('rb') as f:
            files = {'file': ('test.txt', f, 'text/plain')}
            data = {
                'include_metadata': 'true',
                'include_text': 'true',
                'include_structure': 'false',
            }
            resp = http_client.post('/extract', files=files, data=data)
        assert resp.status_code == 200
        payload = resp.json()
        assert payload.get('success') is True
        assert payload.get('file_metadata', {}).get('filename') == 'test.txt'
        assert payload.get('extracted_text', {}).get('content') is not None

    @pytest.mark.slow
    def test_extract_pdf(
        self,
        http_client: httpx.Client,
        sample_pdf_file: Path,
    ) -> None:
        with sample_pdf_file.open('rb') as f:
            files = {'file': ('test.pdf', f, 'application/pdf')}
            data = {
                'include_metadata': 'true',
                'include_text': 'true',
                'include_structure': 'false',
            }
            resp = http_client.post('/extract', files=files, data=data)
        assert resp.status_code == 200
        payload = resp.json()
        assert payload.get('success') is True
        assert payload.get('file_metadata', {}).get('filename') == 'test.pdf'


@pytest.mark.e2e
class TestE2EAsync:
    def test_async_job_flow(
        self,
        http_client: httpx.Client,
        sample_text_file: Path,
    ) -> None:
        # Job starten
        with sample_text_file.open('rb') as f:
            files = {'file': ('async.txt', f, 'text/plain')}
            data = {
                'include_metadata': 'true',
                'include_text': 'true',
                'include_structure': 'false',
                'priority': 'normal',
            }
            resp = http_client.post('/extract/async', files=files, data=data)
        assert resp.status_code == 200
        job = resp.json()
        job_id = job.get('job_id')
        assert job_id

        # Status pollen
        deadline = time.time() + 180  # 3 Minuten
        status_val = None
        while time.time() < deadline:
            resp = http_client.get(f'/jobs/{job_id}')
            assert resp.status_code == 200
            status_val = resp.json().get('status')
            if status_val in {'completed', 'failed'}:
                break
            time.sleep(2)
        assert status_val in {'completed', 'failed'}

        # Queue-Statistiken
        resp = http_client.get('/jobs')
        assert resp.status_code == 200
        assert 'queue_stats' in resp.json()

    def test_async_cancel_not_found(self, http_client: httpx.Client) -> None:
        # Erwartet 404 für unbekannte Jobs oder bereits abgeschlossene Jobs
        resp = http_client.delete('/jobs/does-not-exist')
        assert resp.status_code == 404

    def test_jobs_cleanup(self, http_client: httpx.Client) -> None:
        resp = http_client.post('/jobs/cleanup')
        assert resp.status_code == 200
        data = resp.json()
        assert 'deleted_count' in data
        assert 'max_age_hours' in data
