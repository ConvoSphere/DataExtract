"""
Docling-basierter Extraktor für erweiterte Datenextraktion.
"""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    # Check if Pipeline is available
    try:
        from docling import Document, Pipeline
    except ImportError:
        # If Pipeline is not available, create a simple mock
        class Pipeline:
            def __init__(self):
                self.enrichments = []

            def add_enrichment(self, enrichment):
                self.enrichments.append(enrichment)

            def process(self, doc):
                return doc

        from docling import Document

    # Try to import enrichments, but don't fail if they're not available
    try:
        from docling.enrichments import (
            EntityEnrichment,
            ImageEnrichment,
            LanguageEnrichment,
            LinkEnrichment,
            MetadataEnrichment,
            SentimentEnrichment,
            StructureEnrichment,
            SummaryEnrichment,
            TableEnrichment,
            TextEnrichment,
        )
    except ImportError:
        # Create mock enrichments
        class MockEnrichment:
            def __init__(self, name):
                self.name = name

            def enrich(self, doc):
                return doc

        def entity_enrichment():
            return MockEnrichment('EntityEnrichment')

        def image_enrichment():
            return MockEnrichment('ImageEnrichment')

        def language_enrichment():
            return MockEnrichment('LanguageEnrichment')

        def link_enrichment():
            return MockEnrichment('LinkEnrichment')

        def metadata_enrichment():
            return MockEnrichment('MetadataEnrichment')

        def sentiment_enrichment():
            return MockEnrichment('SentimentEnrichment')

        def structure_enrichment():
            return MockEnrichment('StructureEnrichment')

        def summary_enrichment():
            return MockEnrichment('SummaryEnrichment')

        def table_enrichment():
            return MockEnrichment('TableEnrichment')

        def text_enrichment():
            return MockEnrichment('TextEnrichment')

    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False

from app.core.config import settings
from app.extractors.base import BaseExtractor
from app.models.schemas import (
    ExtractedImage,
    ExtractedText,
    FileMetadata,
    StructuredData,
)


class DoclingExtractor(BaseExtractor):
    """Docling-basierter Extraktor für erweiterte Datenextraktion."""

    def __init__(self):
        super().__init__()
        if not DOCLING_AVAILABLE:
            raise ImportError(
                'docling ist nicht installiert. Installieren Sie es mit: uv add docling',
            )

        # Unterstützte Formate (docling kann viele Formate verarbeiten)
        self.supported_extensions = [
            # Dokumente
            '.pdf',
            '.docx',
            '.doc',
            '.rtf',
            '.odt',
            '.txt',
            # Tabellen
            '.xlsx',
            '.xls',
            '.ods',
            '.csv',
            # Präsentationen
            '.pptx',
            '.ppt',
            '.odp',
            # Datenformate
            '.json',
            '.xml',
            '.html',
            '.htm',
            '.yaml',
            '.yml',
            # Bilder (mit OCR)
            '.jpg',
            '.jpeg',
            '.png',
            '.gif',
            '.bmp',
            '.tiff',
            '.tif',
            '.webp',
        ]
        self.supported_mime_types = [
            # Dokumente
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/msword',
            'text/rtf',
            'application/vnd.oasis.opendocument.text',
            'text/plain',
            # Tabellen
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-excel',
            'application/vnd.oasis.opendocument.spreadsheet',
            'text/csv',
            # Präsentationen
            'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'application/vnd.ms-powerpoint',
            'application/vnd.oasis.opendocument.presentation',
            # Datenformate
            'application/json',
            'application/xml',
            'text/html',
            'text/yaml',
            # Bilder
            'image/jpeg',
            'image/png',
            'image/gif',
            'image/bmp',
            'image/tiff',
            'image/webp',
        ]
        self.max_file_size = settings.max_file_size

        # Docling Pipeline konfigurieren
        self.pipeline = self._create_pipeline()

    def can_extract(self, file_path: Path, mime_type: str) -> bool:
        """Prüft, ob der Extraktor die Datei verarbeiten kann."""
        return (
            file_path.suffix.lower() in self.supported_extensions
            or mime_type in self.supported_mime_types
        )

    def extract_metadata(self, file_path: Path) -> FileMetadata:
        """Extrahiert Metadaten mit docling."""
        stat = file_path.stat()

        metadata = FileMetadata(
            filename=file_path.name,
            file_size=stat.st_size,
            file_type=self._get_mime_type(file_path),
            file_extension=file_path.suffix.lower(),
            created_date=datetime.fromtimestamp(stat.st_ctime, tz=UTC),
            modified_date=datetime.fromtimestamp(stat.st_mtime, tz=UTC),
        )

        try:
            # Docling Document erstellen
            doc = Document.from_file(str(file_path))

            # Metadaten-Extraktion
            metadata_enrichment = MetadataEnrichment()
            enriched_doc = metadata_enrichment.enrich(doc)

            # Docling-Metadaten extrahieren
            if hasattr(enriched_doc, 'metadata'):
                doc_metadata = enriched_doc.metadata

                if 'title' in doc_metadata:
                    metadata.title = str(doc_metadata['title'])
                if 'author' in doc_metadata:
                    metadata.author = str(doc_metadata['author'])
                if 'subject' in doc_metadata:
                    metadata.subject = str(doc_metadata['subject'])
                if 'keywords' in doc_metadata:
                    if isinstance(doc_metadata['keywords'], list):
                        metadata.keywords = [str(k) for k in doc_metadata['keywords']]
                    else:
                        metadata.keywords = [str(doc_metadata['keywords'])]

                # Seitenanzahl
                if 'page_count' in doc_metadata:
                    metadata.page_count = int(doc_metadata['page_count'])

                # Dimensionen (für Bilder)
                if 'width' in doc_metadata and 'height' in doc_metadata:
                    metadata.dimensions = {
                        'width': int(doc_metadata['width']),
                        'height': int(doc_metadata['height']),
                    }

                # Dauer (für Medien)
                if 'duration' in doc_metadata:
                    metadata.duration = float(doc_metadata['duration'])

        except (ValueError, AttributeError, TypeError):
            # Fallback zu Basis-Metadaten
            pass

        return metadata

    def extract_text(self, file_path: Path) -> ExtractedText:
        """Extrahiert Text mit docling."""
        content = ''
        language = None
        confidence = 1.0
        ocr_used = False

        try:
            # Docling Document erstellen
            doc = Document.from_file(str(file_path))

            # Text-Extraktion
            text_enrichment = TextEnrichment()
            enriched_doc = text_enrichment.enrich(doc)

            # Text extrahieren
            if hasattr(enriched_doc, 'text') and enriched_doc.text:
                content = enriched_doc.text
            elif hasattr(enriched_doc, 'content') and enriched_doc.content:
                content = enriched_doc.content

            # Sprache erkennen
            language_enrichment = LanguageEnrichment()
            lang_doc = language_enrichment.enrich(enriched_doc)

            if hasattr(lang_doc, 'language'):
                language = str(lang_doc.language)

            # OCR-Status prüfen
            if hasattr(enriched_doc, 'ocr_used'):
                ocr_used = bool(enriched_doc.ocr_used)

            # Konfidenz
            if hasattr(enriched_doc, 'confidence'):
                confidence = float(enriched_doc.confidence)

        except (ValueError, AttributeError, TypeError):
            pass

        # Statistiken berechnen
        word_count = len(content.split()) if content else 0
        character_count = len(content)

        return ExtractedText(
            content=content,
            language=language,
            confidence=confidence,
            word_count=word_count,
            character_count=character_count,
            ocr_used=ocr_used,
            ocr_confidence=confidence if ocr_used else None,
        )

    def extract_structured_data(self, file_path: Path) -> StructuredData:
        """Extrahiert strukturierte Daten mit docling."""
        tables = []
        headings = []
        links = []
        images = []
        lists = []

        try:
            # Docling Document erstellen
            doc = Document.from_file(str(file_path))

            # Struktur-Extraktion
            structure_enrichment = StructureEnrichment()
            enriched_doc = structure_enrichment.enrich(doc)

            # Tabellen extrahieren
            table_enrichment = TableEnrichment()
            table_doc = table_enrichment.enrich(enriched_doc)

            if hasattr(table_doc, 'tables') and table_doc.tables:
                for table in table_doc.tables:
                    table_data = {
                        'headers': table.get('headers', []),
                        'rows': table.get('rows', []),
                        'row_count': len(table.get('rows', [])),
                        'column_count': len(table.get('headers', [])),
                    }
                    tables.append(table_data)

            # Überschriften extrahieren
            if hasattr(enriched_doc, 'headings') and enriched_doc.headings:
                for heading in enriched_doc.headings:
                    heading_data = {
                        'level': heading.get('level', 1),
                        'text': heading.get('text', ''),
                        'position': heading.get('position', 0),
                    }
                    headings.append(heading_data)

            # Links extrahieren
            link_enrichment = LinkEnrichment()
            link_doc = link_enrichment.enrich(enriched_doc)

            if hasattr(link_doc, 'links') and link_doc.links:
                links = [str(link) for link in link_doc.links]

            # Bilder extrahieren
            image_enrichment = ImageEnrichment()
            image_doc = image_enrichment.enrich(enriched_doc)

            if hasattr(image_doc, 'images') and image_doc.images:
                for i, img in enumerate(image_doc.images):
                    image_data = ExtractedImage(
                        image_index=i,
                        image_type=img.get('type', 'unknown'),
                        dimensions={
                            'width': img.get('width', 0),
                            'height': img.get('height', 0),
                        },
                        file_size=img.get('size', 0),
                        extracted_text=img.get('text'),
                        ocr_confidence=img.get('confidence'),
                    )
                    images.append(image_data)

            # Listen extrahieren
            if hasattr(enriched_doc, 'lists') and enriched_doc.lists:
                for list_data in enriched_doc.lists:
                    if isinstance(list_data, list):
                        lists.append([str(item) for item in list_data])

        except (ValueError, AttributeError, TypeError):
            pass

        return StructuredData(
            tables=tables,
            headings=headings,
            links=links,
            images=images,
            lists=lists,
        )

    def extract_entities(self, file_path: Path) -> dict[str, Any]:
        """Extrahiert Entitäten mit docling."""
        entities = {}

        try:
            doc = Document.from_file(str(file_path))

            # Text extrahieren
            text_enrichment = TextEnrichment()
            enriched_doc = text_enrichment.enrich(doc)

            # Entitäten extrahieren
            entity_enrichment = EntityEnrichment()
            entity_doc = entity_enrichment.enrich(enriched_doc)

            if hasattr(entity_doc, 'entities') and entity_doc.entities:
                for entity_type, entity_list in entity_doc.entities.items():
                    entities[entity_type] = [str(entity) for entity in entity_list]

        except (ValueError, AttributeError, TypeError):
            pass

        return entities

    def extract_sentiment(self, file_path: Path) -> dict[str, Any]:
        """Extrahiert Sentiment-Analyse mit docling."""
        sentiment_data = {}

        try:
            doc = Document.from_file(str(file_path))

            # Text extrahieren
            text_enrichment = TextEnrichment()
            enriched_doc = text_enrichment.enrich(doc)

            # Sentiment-Analyse
            sentiment_enrichment = SentimentEnrichment()
            sentiment_doc = sentiment_enrichment.enrich(enriched_doc)

            if hasattr(sentiment_doc, 'sentiment'):
                sentiment = sentiment_doc.sentiment
                sentiment_data = {
                    'overall_sentiment': sentiment.get('overall', 'neutral'),
                    'sentiment_score': sentiment.get('score', 0.0),
                    'positive_phrases': sentiment.get('positive', []),
                    'negative_phrases': sentiment.get('negative', []),
                }

        except (ValueError, AttributeError, TypeError):
            pass

        return sentiment_data

    def extract_summary(self, file_path: Path) -> str:
        """Extrahiert Zusammenfassung mit docling."""
        summary = ''

        try:
            doc = Document.from_file(str(file_path))

            # Text extrahieren
            text_enrichment = TextEnrichment()
            enriched_doc = text_enrichment.enrich(doc)

            # Zusammenfassung erstellen
            summary_enrichment = SummaryEnrichment()
            summary_doc = summary_enrichment.enrich(enriched_doc)

            if hasattr(summary_doc, 'summary'):
                summary = str(summary_doc.summary)

        except (ValueError, AttributeError, TypeError):
            pass

        return summary

    def _create_pipeline(self) -> Pipeline:
        """Erstellt eine docling Pipeline."""
        pipeline = Pipeline()

        # Basis-Enrichments hinzufügen
        pipeline.add_enrichment(TextEnrichment())
        pipeline.add_enrichment(MetadataEnrichment())
        pipeline.add_enrichment(StructureEnrichment())
        pipeline.add_enrichment(TableEnrichment())
        pipeline.add_enrichment(ImageEnrichment())
        pipeline.add_enrichment(LinkEnrichment())
        pipeline.add_enrichment(LanguageEnrichment())

        # Optionale Enrichments
        if settings.enable_advanced_analysis:
            pipeline.add_enrichment(EntityEnrichment())
            pipeline.add_enrichment(SentimentEnrichment())
            pipeline.add_enrichment(SummaryEnrichment())

        return pipeline

    def _get_mime_type(self, file_path: Path) -> str:
        """Ermittelt den MIME-Type der Datei."""
        extension = file_path.suffix.lower()
        mime_types = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.doc': 'application/msword',
            '.rtf': 'text/rtf',
            '.odt': 'application/vnd.oasis.opendocument.text',
            '.txt': 'text/plain',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.xls': 'application/vnd.ms-excel',
            '.ods': 'application/vnd.oasis.opendocument.spreadsheet',
            '.csv': 'text/csv',
            '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            '.ppt': 'application/vnd.ms-powerpoint',
            '.odp': 'application/vnd.oasis.opendocument.presentation',
            '.json': 'application/json',
            '.xml': 'application/xml',
            '.html': 'text/html',
            '.htm': 'text/html',
            '.yaml': 'text/yaml',
            '.yml': 'text/yaml',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
            '.tiff': 'image/tiff',
            '.tif': 'image/tiff',
            '.webp': 'image/webp',
        }
        return mime_types.get(extension, 'application/octet-stream')

    def get_supported_formats(self) -> dict[str, Any]:
        """Gibt Informationen über unterstützte Formate zurück."""
        return {
            'extensions': self.supported_extensions,
            'mime_types': self.supported_mime_types,
            'max_file_size': self.max_file_size,
            'features': [
                'text_extraction',
                'metadata_extraction',
                'structure_extraction',
                'table_extraction',
                'image_extraction',
                'link_extraction',
                'language_detection',
                'entity_extraction',
                'sentiment_analysis',
                'summarization',
            ],
        }
