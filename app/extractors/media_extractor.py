"""
Extraktor für Medien-Dateien (Video/Audio) mit Transkription.
"""

import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import cv2

try:
    from moviepy.editor import VideoFileClip, AudioFileClip
    from pydub import AudioSegment
    import speech_recognition as sr
    MEDIA_AVAILABLE = True
except ImportError:
    MEDIA_AVAILABLE = False

from app.extractors.base import BaseExtractor
from app.models.schemas import (
    ExtractedText, 
    FileMetadata, 
    StructuredData,
    ExtractedMedia
)
from app.core.config import settings


class MediaExtractor(BaseExtractor):
    """Extraktor für Medien-Dateien (Video/Audio)."""
    
    def __init__(self):
        super().__init__()
        if not MEDIA_AVAILABLE:
            print("Warnung: Medien-Bibliotheken nicht verfügbar. Installieren Sie moviepy, pydub und speechrecognition.")
        
        self.supported_extensions = [
            # Video
            ".mp4", ".avi", ".mov", ".wmv", ".flv", ".webm", ".mkv", ".m4v",
            # Audio
            ".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma"
        ]
        self.supported_mime_types = [
            # Video
            "video/mp4", "video/avi", "video/quicktime", "video/x-ms-wmv",
            "video/x-flv", "video/webm", "video/x-matroska",
            # Audio
            "audio/mpeg", "audio/wav", "audio/flac", "audio/aac", "audio/ogg"
        ]
        self.max_file_size = 150 * 1024 * 1024  # 150MB
    
    def can_extract(self, file_path: Path, mime_type: str) -> bool:
        """Prüft, ob der Extraktor die Mediendatei verarbeiten kann."""
        return (
            file_path.suffix.lower() in self.supported_extensions or
            mime_type in self.supported_mime_types
        )
    
    def extract_metadata(self, file_path: Path) -> FileMetadata:
        """Extrahiert Metadaten aus der Mediendatei."""
        stat = file_path.stat()
        
        metadata = FileMetadata(
            filename=file_path.name,
            file_size=stat.st_size,
            file_type=self._get_mime_type(file_path),
            file_extension=file_path.suffix.lower(),
            created_date=datetime.fromtimestamp(stat.st_ctime),
            modified_date=datetime.fromtimestamp(stat.st_mtime)
        )
        
        try:
            if self._is_video_file(file_path):
                # Video-Metadaten
                clip = VideoFileClip(str(file_path))
                metadata.duration = clip.duration
                metadata.dimensions = {
                    "width": int(clip.w),
                    "height": int(clip.h)
                }
                metadata.resolution = f"{int(clip.w)}x{int(clip.h)}"
                metadata.fps = clip.fps
                clip.close()
                
            elif self._is_audio_file(file_path):
                # Audio-Metadaten
                audio = AudioSegment.from_file(str(file_path))
                metadata.duration = len(audio) / 1000.0  # Konvertiere zu Sekunden
                metadata.channels = audio.channels
                metadata.sample_rate = audio.frame_rate
                
        except Exception:
            pass
        
        return metadata
    
    def extract_text(self, file_path: Path) -> ExtractedText:
        """Extrahiert Text aus der Mediendatei (Transkription)."""
        content = ""
        
        if not settings.extract_audio_transcript or not MEDIA_AVAILABLE:
            return ExtractedText(content=content)
        
        try:
            if self._is_audio_file(file_path):
                # Audio-Transkription
                content = self._transcribe_audio(file_path)
            elif self._is_video_file(file_path):
                # Video-Transkription (Audio-Extraktion + Transkription)
                content = self._transcribe_video(file_path)
                
        except Exception as e:
            print(f"Transkriptions-Fehler für {file_path}: {e}")
        
        # Statistiken berechnen
        word_count = len(content.split()) if content else 0
        character_count = len(content)
        
        return ExtractedText(
            content=content,
            word_count=word_count,
            character_count=character_count
        )
    
    def extract_structured_data(self, file_path: Path) -> StructuredData:
        """Extrahiert strukturierte Daten aus der Mediendatei."""
        media_list = []
        
        try:
            if self._is_video_file(file_path):
                media_info = self._extract_video_info(file_path)
                media_list.append(media_info)
            elif self._is_audio_file(file_path):
                media_info = self._extract_audio_info(file_path)
                media_list.append(media_info)
                
        except Exception:
            pass
        
        return StructuredData(media=media_list)
    
    def _get_mime_type(self, file_path: Path) -> str:
        """Ermittelt den MIME-Type der Mediendatei."""
        extension = file_path.suffix.lower()
        mime_types = {
            # Video
            ".mp4": "video/mp4",
            ".avi": "video/avi",
            ".mov": "video/quicktime",
            ".wmv": "video/x-ms-wmv",
            ".flv": "video/x-flv",
            ".webm": "video/webm",
            ".mkv": "video/x-matroska",
            # Audio
            ".mp3": "audio/mpeg",
            ".wav": "audio/wav",
            ".flac": "audio/flac",
            ".aac": "audio/aac",
            ".ogg": "audio/ogg"
        }
        return mime_types.get(extension, "application/octet-stream")
    
    def _is_video_file(self, file_path: Path) -> bool:
        """Prüft, ob es sich um eine Videodatei handelt."""
        video_extensions = [".mp4", ".avi", ".mov", ".wmv", ".flv", ".webm", ".mkv", ".m4v"]
        return file_path.suffix.lower() in video_extensions
    
    def _is_audio_file(self, file_path: Path) -> bool:
        """Prüft, ob es sich um eine Audiodatei handelt."""
        audio_extensions = [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma"]
        return file_path.suffix.lower() in audio_extensions
    
    def _transcribe_audio(self, file_path: Path) -> str:
        """Transkribiert eine Audiodatei."""
        try:
            # Audio zu WAV konvertieren (für bessere Kompatibilität)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
                audio = AudioSegment.from_file(str(file_path))
                audio.export(temp_wav.name, format="wav")
                temp_wav_path = temp_wav.name
            
            try:
                # Speech Recognition
                recognizer = sr.Recognizer()
                with sr.AudioFile(temp_wav_path) as source:
                    audio_data = recognizer.record(source)
                    text = recognizer.recognize_google(audio_data, language="de-DE")
                    return text
            finally:
                # Temporäre Datei löschen
                if os.path.exists(temp_wav_path):
                    os.unlink(temp_wav_path)
                    
        except Exception as e:
            print(f"Audio-Transkription fehlgeschlagen: {e}")
            return ""
    
    def _transcribe_video(self, file_path: Path) -> str:
        """Transkribiert ein Video (extrahiert Audio und transkribiert)."""
        try:
            # Audio aus Video extrahieren
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
                video = VideoFileClip(str(file_path))
                video.audio.write_audiofile(temp_audio.name, verbose=False, logger=None)
                video.close()
                temp_audio_path = temp_audio.name
            
            try:
                # Audio transkribieren
                return self._transcribe_audio(Path(temp_audio_path))
            finally:
                # Temporäre Datei löschen
                if os.path.exists(temp_audio_path):
                    os.unlink(temp_audio_path)
                    
        except Exception as e:
            print(f"Video-Transkription fehlgeschlagen: {e}")
            return ""
    
    def _extract_video_info(self, file_path: Path) -> ExtractedMedia:
        """Extrahiert Video-Informationen."""
        try:
            clip = VideoFileClip(str(file_path))
            
            media_info = ExtractedMedia(
                media_type="video",
                format=file_path.suffix.lower()[1:],  # Ohne Punkt
                duration=clip.duration,
                resolution=f"{int(clip.w)}x{int(clip.h)}",
                fps=clip.fps
            )
            
            clip.close()
            return media_info
            
        except Exception:
            # Fallback-Informationen
            return ExtractedMedia(
                media_type="video",
                format=file_path.suffix.lower()[1:],
                duration=0.0
            )
    
    def _extract_audio_info(self, file_path: Path) -> ExtractedMedia:
        """Extrahiert Audio-Informationen."""
        try:
            audio = AudioSegment.from_file(str(file_path))
            
            media_info = ExtractedMedia(
                media_type="audio",
                format=file_path.suffix.lower()[1:],  # Ohne Punkt
                duration=len(audio) / 1000.0,  # Konvertiere zu Sekunden
                channels=audio.channels,
                sample_rate=audio.frame_rate
            )
            
            return media_info
            
        except Exception:
            # Fallback-Informationen
            return ExtractedMedia(
                media_type="audio",
                format=file_path.suffix.lower()[1:],
                duration=0.0
            )