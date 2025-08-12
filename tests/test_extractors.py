"""Tests für die Extraktoren."""

from pathlib import Path

import pytest

from app.extractors.base import BaseExtractor


def test_base_extractor_abstract_methods():
    """Testet, dass BaseExtractor abstrakte Methoden hat."""
    # BaseExtractor sollte nicht direkt instanziiert werden können
    with pytest.raises(TypeError):
        BaseExtractor()


def test_base_extractor_interface():
    """Testet das Interface des BaseExtractor."""

    # Mock-Extraktor erstellen, der BaseExtractor implementiert
    class MockExtractor(BaseExtractor):
        def can_extract(self, file_path: Path, mime_type: str) -> bool:
            return file_path.suffix == '.mock'

        def extract_metadata(self, file_path: Path):
            pass

        def extract_text(self, file_path: Path):
            pass

        def extract_structured_data(self, file_path: Path):
            pass

    # Extraktor sollte erfolgreich erstellt werden können
    extractor = MockExtractor()
    assert extractor is not None
    assert hasattr(extractor, 'can_extract')
    assert hasattr(extractor, 'extract_metadata')
    assert hasattr(extractor, 'extract_text')
    assert hasattr(extractor, 'extract_structured_data')


def test_mock_extractor_can_extract():
    """Testet die can_extract Methode eines Mock-Extraktors."""

    class MockExtractor(BaseExtractor):
        def can_extract(self, file_path: Path, mime_type: str) -> bool:
            return file_path.suffix == '.mock'

        def extract_metadata(self, file_path: Path):
            pass

        def extract_text(self, file_path: Path):
            pass

        def extract_structured_data(self, file_path: Path):
            pass

    extractor = MockExtractor()

    # Sollte .mock Dateien erkennen
    assert extractor.can_extract(Path('test.mock'), 'application/mock')

    # Sollte andere Dateien nicht erkennen
    assert not extractor.can_extract(Path('test.txt'), 'text/plain')
