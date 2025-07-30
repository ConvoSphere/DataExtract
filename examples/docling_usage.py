"""
Beispiel für die Verwendung von docling in der Universal File Extractor API.
"""

import requests
import json
from pathlib import Path
from typing import Dict, Any


def extract_with_docling(file_path: str, api_url: str = "http://localhost:8000") -> Dict[str, Any]:
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
            f"{api_url}/api/v1/extract",
            files=files,
            data=data
        )
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"API-Fehler: {response.status_code} - {response.text}")


def extract_async_with_docling(file_path: str, api_url: str = "http://localhost:8000") -> Dict[str, Any]:
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
            f"{api_url}/api/v1/extract/async",
            files=files,
            data=data
        )
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"API-Fehler: {response.status_code} - {response.text}")


def get_job_status(job_id: str, api_url: str = "http://localhost:8000") -> Dict[str, Any]:
    """
    Abfrage des Job-Status.
    
    Args:
        job_id: Job-ID
        api_url: URL der API
        
    Returns:
        Job-Status
    """
    
    response = requests.get(f"{api_url}/api/v1/jobs/{job_id}")
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"API-Fehler: {response.status_code} - {response.text}")


def analyze_document(file_path: str) -> None:
    """
    Vollständige Dokumentenanalyse mit docling-Features.
    
    Args:
        file_path: Pfad zur Datei
    """
    
    print(f"Analysiere Dokument: {file_path}")
    print("=" * 50)
    
    try:
        # Synchrone Extraktion
        result = extract_with_docling(file_path)
        
        # Basis-Informationen
        print(f"Datei: {result['file_metadata']['filename']}")
        print(f"Größe: {result['file_metadata']['file_size']} Bytes")
        print(f"Typ: {result['file_metadata']['file_type']}")
        
        # Text-Extraktion
        if result.get('extracted_text'):
            text = result['extracted_text']
            print(f"\nText-Extraktion:")
            print(f"- Wörter: {text.get('word_count', 0)}")
            print(f"- Zeichen: {text.get('character_count', 0)}")
            print(f"- Sprache: {text.get('language', 'unbekannt')}")
            print(f"- OCR verwendet: {text.get('ocr_used', False)}")
            print(f"- Konfidenz: {text.get('confidence', 0.0):.2f}")
            
            # Text-Vorschau
            content = text.get('content', '')
            if content:
                preview = content[:200] + "..." if len(content) > 200 else content
                print(f"- Vorschau: {preview}")
        
        # Strukturierte Daten
        if result.get('structured_data'):
            structured = result['structured_data']
            print(f"\nStrukturierte Daten:")
            
            if structured.get('tables'):
                print(f"- Tabellen: {len(structured['tables'])}")
                for i, table in enumerate(structured['tables']):
                    print(f"  Tabelle {i+1}: {table.get('row_count', 0)} Zeilen, {table.get('column_count', 0)} Spalten")
            
            if structured.get('headings'):
                print(f"- Überschriften: {len(structured['headings'])}")
                for heading in structured['headings'][:5]:  # Erste 5
                    print(f"  {heading.get('level', 1)}: {heading.get('text', '')}")
            
            if structured.get('links'):
                print(f"- Links: {len(structured['links'])}")
                for link in structured['links'][:3]:  # Erste 3
                    print(f"  - {link}")
            
            if structured.get('images'):
                print(f"- Bilder: {len(structured['images'])}")
                for img in structured['images']:
                    print(f"  - {img.get('image_type', 'unknown')}: {img.get('dimensions', {})}")
        
        # Metadaten
        metadata = result['file_metadata']
        if metadata.get('title'):
            print(f"\nTitel: {metadata['title']}")
        if metadata.get('author'):
            print(f"Autor: {metadata['author']}")
        if metadata.get('subject'):
            print(f"Betreff: {metadata['subject']}")
        if metadata.get('keywords'):
            print(f"Schlüsselwörter: {', '.join(metadata['keywords'])}")
        
        # Performance
        print(f"\nExtraktionszeit: {result.get('extraction_time', 0):.2f} Sekunden")
        
    except Exception as e:
        print(f"Fehler bei der Analyse: {e}")


def analyze_large_document(file_path: str) -> None:
    """
    Analyse eines großen Dokuments mit asynchroner Verarbeitung.
    
    Args:
        file_path: Pfad zur Datei
    """
    
    print(f"Analysiere großes Dokument: {file_path}")
    print("=" * 50)
    
    try:
        # Asynchrone Extraktion starten
        job_info = extract_async_with_docling(file_path)
        job_id = job_info['job_id']
        
        print(f"Job gestartet: {job_id}")
        print(f"Status: {job_info['status']}")
        
        # Status abfragen
        import time
        while True:
            time.sleep(2)  # 2 Sekunden warten
            status = get_job_status(job_id)
            
            print(f"Status: {status['status']}, Fortschritt: {status['progress']:.1f}%")
            
            if status['status'] in ['completed', 'failed']:
                break
        
        # Ergebnis anzeigen
        if status['status'] == 'completed' and status.get('result'):
            result = status['result']
            print(f"\nErgebnis:")
            print(f"- Extraktionszeit: {result.get('extraction_time', 0):.2f} Sekunden")
            print(f"- Erfolg: {result.get('success', False)}")
            
            if result.get('extracted_text'):
                text = result['extracted_text']
                print(f"- Wörter extrahiert: {text.get('word_count', 0)}")
        
        elif status['status'] == 'failed':
            print(f"Fehler: {status.get('error', 'Unbekannter Fehler')}")
    
    except Exception as e:
        print(f"Fehler bei der Analyse: {e}")


def main():
    """Hauptfunktion mit Beispielen."""
    
    # Beispiel-Dateien (anpassen an Ihre Dateien)
    sample_files = [
        "samples/sample.txt",
        "samples/sample.json",
        "samples/sample.csv",
    ]
    
    print("Docling Integration - Universal File Extractor API")
    print("=" * 60)
    
    # API-Status prüfen
    try:
        response = requests.get("http://localhost:8000/api/v1/health")
        if response.status_code == 200:
            health = response.json()
            print(f"API Status: {health['status']}")
            print(f"Version: {health['version']}")
            print(f"Unterstützte Formate: {health['supported_formats_count']}")
        else:
            print("API nicht erreichbar")
            return
    except Exception as e:
        print(f"Fehler beim Verbinden zur API: {e}")
        return
    
    print("\n" + "=" * 60)
    
    # Dateien analysieren
    for file_path in sample_files:
        if Path(file_path).exists():
            analyze_document(file_path)
            print("\n" + "-" * 40 + "\n")
        else:
            print(f"Datei nicht gefunden: {file_path}")
    
    # Beispiel für große Datei (asynchron)
    large_file = "samples/large_document.pdf"
    if Path(large_file).exists():
        print("Große Datei gefunden - verwende asynchrone Verarbeitung")
        analyze_large_document(large_file)
    else:
        print("Keine große Datei gefunden - überspringe asynchrone Verarbeitung")


if __name__ == "__main__":
    main()