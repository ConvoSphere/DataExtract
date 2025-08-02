"""
Extraktor für Bilddateien mit OCR-Funktionalität.
"""

from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

try:
    import easyocr
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

from app.core.config import settings
from app.extractors.base import BaseExtractor
from app.models.schemas import (
    ExtractedImage,
    ExtractedText,
    FileMetadata,
    StructuredData,
)


class ImageExtractor(BaseExtractor):
    """Extraktor für Bilddateien mit OCR."""

    def __init__(self):
        super().__init__()
        if not OCR_AVAILABLE:
            pass

        self.supported_extensions = [
            '.jpg', '.jpeg', '.png', '.gif', '.bmp',
            '.tiff', '.tif', '.webp', '.svg',
        ]
        self.supported_mime_types = [
            'image/jpeg', 'image/png', 'image/gif', 'image/bmp',
            'image/tiff', 'image/webp', 'image/svg+xml',
        ]
        self.max_file_size = settings.image_max_size

    def can_extract(self, file_path: Path, mime_type: str) -> bool:
        """Prüft, ob der Extraktor die Bilddatei verarbeiten kann."""
        return (
            file_path.suffix.lower() in self.supported_extensions or
            mime_type in self.supported_mime_types
        )

    def extract_metadata(self, file_path: Path) -> FileMetadata:
        """Extrahiert Metadaten aus der Bilddatei."""
        stat = file_path.stat()

        metadata = FileMetadata(
            filename=file_path.name,
            file_size=stat.st_size,
            file_type=self._get_mime_type(file_path),
            file_extension=file_path.suffix.lower(),
            created_date=datetime.fromtimestamp(stat.st_ctime),
            modified_date=datetime.fromtimestamp(stat.st_mtime),
        )

        try:
            with Image.open(file_path) as img:
                # Bild-Dimensionen
                metadata.dimensions = {
                    'width': img.width,
                    'height': img.height,
                }

                # Auflösung
                if hasattr(img, 'info') and 'dpi' in img.info:
                    dpi = img.info['dpi']
                    metadata.resolution = f'{dpi[0]}x{dpi[1]} DPI'

                # Farbraum
                metadata.color_space = img.mode

                # EXIF-Daten (falls verfügbar)
                if hasattr(img, '_getexif') and img._getexif():
                    exif = img._getexif()
                    if exif:
                        # EXIF-Tags für Metadaten
                        exif_tags = {
                            270: 'title',      # ImageDescription
                            315: 'author',     # Artist
                            33432: 'author',   # Copyright
                        }

                        for tag_id, field_name in exif_tags.items():
                            if tag_id in exif:
                                value = exif[tag_id]
                                if hasattr(metadata, field_name):
                                    setattr(metadata, field_name, str(value))

        except Exception:
            pass

        return metadata

    def extract_text(self, file_path: Path) -> ExtractedText:
        """Extrahiert Text aus der Bilddatei mittels OCR."""
        content = ''
        ocr_used = False
        ocr_confidence = 0.0

        if not settings.extract_image_text or not OCR_AVAILABLE:
            return ExtractedText(
                content=content,
                ocr_used=ocr_used,
                ocr_confidence=ocr_confidence,
            )

        try:
            # Bild laden
            with Image.open(file_path) as img:
                # Bild für OCR vorbereiten
                img_array = self._prepare_image_for_ocr(img)

                # OCR mit EasyOCR (bessere Ergebnisse)
                try:
                    reader = easyocr.Reader(['de', 'en'])
                    results = reader.readtext(img_array)

                    if results:
                        ocr_used = True
                        text_parts = []
                        total_confidence = 0.0

                        for (_bbox, text, confidence) in results:
                            text_parts.append(text)
                            total_confidence += confidence

                        content = ' '.join(text_parts)
                        ocr_confidence = total_confidence / len(results) if results else 0.0

                except Exception:
                    # Fallback zu Tesseract
                    try:
                        content = pytesseract.image_to_string(img, lang='deu+eng')
                        ocr_used = True
                        ocr_confidence = 0.8  # Standard-Konfidenz für Tesseract
                    except Exception:
                        pass

        except Exception:
            pass

        # Statistiken berechnen
        word_count = len(content.split()) if content else 0
        character_count = len(content)

        return ExtractedText(
            content=content,
            word_count=word_count,
            character_count=character_count,
            ocr_used=ocr_used,
            ocr_confidence=ocr_confidence,
        )

    def extract_structured_data(self, file_path: Path) -> StructuredData:
        """Extrahiert strukturierte Daten aus der Bilddatei."""
        images = []

        try:
            with Image.open(file_path) as img:
                # Bild-Informationen extrahieren
                image_info = self._extract_image_info(img, file_path)
                images.append(image_info)

        except Exception:
            pass

        return StructuredData(images=images)

    def _get_mime_type(self, file_path: Path) -> str:
        """Ermittelt den MIME-Type der Bilddatei."""
        extension = file_path.suffix.lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
            '.tiff': 'image/tiff',
            '.tif': 'image/tiff',
            '.webp': 'image/webp',
            '.svg': 'image/svg+xml',
        }
        return mime_types.get(extension, 'image/jpeg')

    def _prepare_image_for_ocr(self, img: Image.Image) -> np.ndarray:
        """Bereitet ein Bild für OCR vor."""
        # Zu RGB konvertieren
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # Zu NumPy-Array konvertieren
        img_array = np.array(img)

        # Graustufen konvertieren
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

        # Rauschunterdrückung
        denoised = cv2.medianBlur(gray, 3)

        # Kontrastverbesserung
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        return clahe.apply(denoised)


    def _extract_image_info(self, img: Image.Image, file_path: Path) -> ExtractedImage:
        """Extrahiert detaillierte Bild-Informationen."""
        # Basis-Informationen
        image_info = ExtractedImage(
            image_index=0,
            image_type=file_path.suffix.lower()[1:],  # Ohne Punkt
            dimensions={
                'width': img.width,
                'height': img.height,
            },
            file_size=file_path.stat().st_size,
        )

        # OCR-Text extrahieren
        if settings.extract_image_text and OCR_AVAILABLE:
            try:
                img_array = self._prepare_image_for_ocr(img)
                reader = easyocr.Reader(['de', 'en'])
                results = reader.readtext(img_array)

                if results:
                    text_parts = []
                    total_confidence = 0.0

                    for (_bbox, text, confidence) in results:
                        text_parts.append(text)
                        total_confidence += confidence

                    image_info.extracted_text = ' '.join(text_parts)
                    image_info.ocr_confidence = total_confidence / len(results)

            except Exception:
                pass

        # Farbpalette extrahieren
        try:
            image_info.color_palette = self._extract_color_palette(img)
        except Exception:
            pass

        return image_info

    def _extract_color_palette(self, img: Image.Image, num_colors: int = 5) -> list[str]:
        """Extrahiert die dominanten Farben aus einem Bild."""
        try:
            # Bild auf kleinere Größe reduzieren für schnellere Verarbeitung
            img_small = img.resize((150, 150))

            # Farben quantisieren
            img_quantized = img_small.quantize(colors=num_colors)

            # Dominante Farben extrahieren
            colors = []
            for color in img_quantized.getcolors():
                if color:
                    # RGB-Werte in Hex-Format konvertieren
                    rgb = img_quantized.getpalette()[color[1]*3:color[1]*3+3]
                    hex_color = f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}'
                    colors.append(hex_color)

            return colors[:num_colors]

        except Exception:
            return []
