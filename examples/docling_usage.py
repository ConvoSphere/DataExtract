"""
Beispiel für die Verwendung von docling in der Universal File Extractor API.
"""

from pathlib import Path
from typing import Any

import requests


def extract_with_docling(
    file_path: str,
    api_url: str = 'http://localhost:8000',
) -> dict[str, Any]:
    """
    Extrahiert Inhalte aus einer Datei mit docling-Unterstützung.

    Args:
        file_path: Pfad zur Datei
        api_url: URL der API

    Returns:
        Extraktionsergebnis
    """

    # Datei hochladen
    with open(file_path, 'rb') as f:
        files = {'file': f}
        data = {
            'include_metadata': 'true',
            'include_text': 'true',
            'include_structure': 'true',
            'include_images': 'true',
            'include_media': 'true',
        }

        response = requests.post(
            f'{api_url}/api/v1/extract',
            files=files,
            data=data,
        )

    if response.status_code == 200:
        return response.json()
    raise Exception(f'API-Fehler: {response.status_code} - {response.text}')


def extract_async_with_docling(
    file_path: str,
    api_url: str = 'http://localhost:8000',
) -> dict[str, Any]:
    """
    Asynchrone Extraktion mit docling-Unterstützung.

    Args:
        file_path: Pfad zur Datei
        api_url: URL der API

    Returns:
        Job-Informationen
    """

    # Asynchrone Extraktion starten
    with open(file_path, 'rb') as f:
        files = {'file': f}
        data = {
            'include_metadata': 'true',
            'include_text': 'true',
            'include_structure': 'true',
            'include_images': 'true',
            'include_media': 'true',
            'priority': 'high',
        }

        response = requests.post(
            f'{api_url}/api/v1/extract/async',
            files=files,
            data=data,
        )

    if response.status_code == 200:
        return response.json()
    raise Exception(f'API-Fehler: {response.status_code} - {response.text}')


def get_job_status(
    job_id: str,
    api_url: str = 'http://localhost:8000',
) -> dict[str, Any]:
    """
    Abfrage des Job-Status.

    Args:
        job_id: Job-ID
        api_url: URL der API

    Returns:
        Job-Status
    """

    response = requests.get(f'{api_url}/api/v1/jobs/{job_id}')

    if response.status_code == 200:
        return response.json()
    raise Exception(f'API-Fehler: {response.status_code} - {response.text}')


def analyze_document(file_path: str) -> None:
    """
    Vollständige Dokumentenanalyse mit docling-Features.

    Args:
        file_path: Pfad zur Datei
    """

    try:
        # Synchrone Extraktion
        result = extract_with_docling(file_path)

        # Basis-Informationen

        # Text-Extraktion
        if result.get('extracted_text'):
            text = result['extracted_text']

            # Text-Vorschau
            content = text.get('content', '')
            if content:
                content[:200] + '...' if len(content) > 200 else content

        # Strukturierte Daten
        if result.get('structured_data'):
            structured = result['structured_data']

            if structured.get('tables'):
                for _i, _table in enumerate(structured['tables']):
                    pass

            if structured.get('headings'):
                for _heading in structured['headings'][:5]:  # Erste 5
                    pass

            if structured.get('links'):
                for _link in structured['links'][:3]:  # Erste 3
                    pass

            if structured.get('images'):
                for _img in structured['images']:
                    pass

        # Metadaten
        metadata = result['file_metadata']
        if metadata.get('title'):
            pass
        if metadata.get('author'):
            pass
        if metadata.get('subject'):
            pass
        if metadata.get('keywords'):
            pass

        # Performance

    except Exception:
        pass


def analyze_large_document(file_path: str) -> None:
    """
    Analyse eines großen Dokuments mit asynchroner Verarbeitung.

    Args:
        file_path: Pfad zur Datei
    """

    try:
        # Asynchrone Extraktion starten
        job_info = extract_async_with_docling(file_path)
        job_id = job_info['job_id']

        # Status abfragen
        import time

        while True:
            time.sleep(2)  # 2 Sekunden warten
            status = get_job_status(job_id)

            if status['status'] in ['completed', 'failed']:
                break

        # Ergebnis anzeigen
        if status['status'] == 'completed' and status.get('result'):
            result = status['result']

            if result.get('extracted_text'):
                result['extracted_text']

        elif status['status'] == 'failed':
            pass

    except Exception:
        pass


def main():
    """Hauptfunktion mit Beispielen."""

    # Beispiel-Dateien (anpassen an Ihre Dateien)
    sample_files = [
        'samples/sample.txt',
        'samples/sample.json',
        'samples/sample.csv',
    ]

    # API-Status prüfen
    try:
        response = requests.get('http://localhost:8000/api/v1/health')
        if response.status_code == 200:
            response.json()
        else:
            return
    except Exception:
        return

    # Dateien analysieren
    for file_path in sample_files:
        if Path(file_path).exists():
            analyze_document(file_path)
        else:
            pass

    # Beispiel für große Datei (asynchron)
    large_file = 'samples/large_document.pdf'
    if Path(large_file).exists():
        analyze_large_document(large_file)
    else:
        pass


if __name__ == '__main__':
    main()
