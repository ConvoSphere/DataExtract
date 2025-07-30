"""Tests für die Pydantic-Schemas."""

from datetime import datetime

from app.models.schemas import (
    AsyncExtractionRequest,
    ExtractedText,
    ExtractionRequest,
    ExtractionResult,
    FileMetadata,
    JobStatus,
    StructuredData,
    SupportedFormat,
)


def test_file_metadata():
    """Testet FileMetadata Schema."""
    metadata = FileMetadata(
        filename='test.txt',
        file_size=1024,
        file_type='text/plain',
        file_extension='.txt',
        created_date=datetime.now(),
        modified_date=datetime.now(),
    )

    assert metadata.filename == 'test.txt'
    assert metadata.file_size == 1024
    assert metadata.file_type == 'text/plain'
    assert metadata.file_extension == '.txt'


def test_extracted_text():
    """Testet ExtractedText Schema."""
    text = ExtractedText(
        content='Test content',
        word_count=2,
        character_count=12,
        language='de',
        confidence=0.95,
    )

    assert text.content == 'Test content'
    assert text.word_count == 2
    assert text.character_count == 12
    assert text.language == 'de'
    assert text.confidence == 0.95


def test_structured_data():
    """Testet StructuredData Schema."""
    data = StructuredData(
        tables=[{'headers': ['col1', 'col2'], 'rows': [['val1', 'val2']]}],
        headings=[{'text': 'Heading 1', 'level': 1}, {'text': 'Heading 2', 'level': 2}],
        lists=[['Item 1', 'Item 2'], ['Item 3', 'Item 4']],
    )

    assert len(data.tables) == 1
    assert len(data.headings) == 2
    assert len(data.lists) == 2


def test_extraction_request():
    """Testet ExtractionRequest Schema."""
    request = ExtractionRequest(
        include_text=True,
        include_metadata=True,
        include_structure=False,
    )

    assert request.include_text is True
    assert request.include_metadata is True
    assert request.include_structure is False


def test_extraction_result():
    """Testet ExtractionResult Schema."""
    result = ExtractionResult(
        success=True,
        file_metadata=FileMetadata(
            filename='test.txt',
            file_size=1024,
            file_type='text/plain',
            file_extension='.txt',
            created_date=datetime.now(),
            modified_date=datetime.now(),
        ),
        extracted_text=ExtractedText(
            content='Test content',
            word_count=2,
            character_count=12,
        ),
        extraction_time=1.5,
    )

    assert result.success is True
    assert result.file_metadata is not None
    assert result.extracted_text is not None
    assert result.extraction_time == 1.5


def test_async_extraction_request():
    """Testet AsyncExtractionRequest Schema."""
    request = AsyncExtractionRequest(
        callback_url='http://example.com/callback',
        priority='normal',
        retention_hours=24,
    )

    assert request.callback_url == 'http://example.com/callback'
    assert request.priority == 'normal'
    assert request.retention_hours == 24


def test_job_status():
    """Testet JobStatus Schema."""
    status = JobStatus(
        job_id='test-job-123',
        status='completed',
        created_at=datetime.now(),
        progress=100.0,
    )

    assert status.job_id == 'test-job-123'
    assert status.status == 'completed'
    assert status.progress == 100.0


def test_supported_format():
    """Testet SupportedFormat Schema."""
    format_info = SupportedFormat(
        extension='.pdf',
        mime_type='application/pdf',
        description='Portable Document Format',
        features=['text', 'metadata', 'images'],
        category='document',
        extraction_methods=['native', 'ocr'],
    )

    assert format_info.extension == '.pdf'
    assert format_info.mime_type == 'application/pdf'
    assert format_info.description == 'Portable Document Format'
    assert len(format_info.features) == 3
    assert format_info.category == 'document'
