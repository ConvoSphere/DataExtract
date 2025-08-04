# API Reference

## Overview

The Universal File Extractor API provides a unified interface for extracting content from various file formats. It supports both synchronous and asynchronous processing modes.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

Currently, the API does not require authentication. For production deployments, consider implementing API key authentication or OAuth2.

## Endpoints

### Health Check

#### GET /health

Check the health status of the API.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.123Z",
  "version": "0.1.0"
}
```

### File Extraction

#### POST /extract

Extract content from a file synchronously.

**Parameters:**
- `file` (required): The file to extract content from
- `include_metadata` (optional): Include file metadata (default: true)
- `include_text` (optional): Include extracted text (default: true)
- `include_structured_data` (optional): Include structured data (default: false)
- `ocr_language` (optional): OCR language code (default: auto-detect)

**Response:**
```json
{
  "success": true,
  "file_metadata": {
    "filename": "document.pdf",
    "file_size": 1024000,
    "file_type": "application/pdf",
    "page_count": 5,
    "extraction_time": 2.5
  },
  "extracted_text": {
    "content": "Extracted text content...",
    "word_count": 1500,
    "character_count": 8500,
    "language": "en",
    "ocr_used": false
  },
  "structured_data": {
    "tables": [
      {
        "data": [["Header 1", "Header 2"], ["Row 1 Col 1", "Row 1 Col 2"]],
        "position": {"page": 1, "bbox": [100, 200, 300, 400]}
      }
    ],
    "headings": [
      {"text": "Chapter 1", "level": 1, "position": {"page": 1}}
    ],
    "entities": {
      "persons": ["John Doe", "Jane Smith"],
      "organizations": ["Acme Corp"],
      "locations": ["New York"]
    }
  }
}
```

#### POST /extract/async

Extract content from a file asynchronously.

**Parameters:**
- `file` (required): The file to extract content from
- `priority` (optional): Job priority (low, normal, high)
- `include_metadata` (optional): Include file metadata (default: true)
- `include_text` (optional): Include extracted text (default: true)
- `include_structured_data` (optional): Include structured data (default: false)
- `ocr_language` (optional): OCR language code (default: auto-detect)

**Response:**
```json
{
  "job_id": "abc123-def456-ghi789",
  "status": "queued",
  "message": "Job queued successfully"
}
```

### Job Management

#### GET /jobs/{job_id}

Get the status and result of an asynchronous extraction job.

**Response:**
```json
{
  "job_id": "abc123-def456-ghi789",
  "status": "completed",
  "progress": 100,
  "created_at": "2024-01-15T10:30:00.123Z",
  "completed_at": "2024-01-15T10:32:30.456Z",
  "result": {
    "success": true,
    "file_metadata": {...},
    "extracted_text": {...},
    "structured_data": {...}
  }
}
```

#### DELETE /jobs/{job_id}

Cancel a running job.

**Response:**
```json
{
  "success": true,
  "message": "Job cancelled successfully"
}
```

### Supported Formats

#### GET /formats

Get a list of supported file formats.

**Response:**
```json
{
  "supported_formats": {
    "documents": ["pdf", "docx", "doc", "rtf", "odt", "txt"],
    "spreadsheets": ["xlsx", "xls", "ods", "csv"],
    "presentations": ["pptx", "ppt", "odp"],
    "data": ["json", "xml", "html", "yaml"],
    "images": ["jpg", "jpeg", "png", "gif", "bmp", "tiff", "webp", "svg"],
    "media": ["mp4", "avi", "mov", "mp3", "wav", "flac"],
    "archives": ["zip", "rar", "7z", "tar", "gz"]
  }
}
```

## Error Handling

### Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid file format",
    "details": {
      "field": "file",
      "value": "unsupported.xyz"
    }
  }
}
```

### Common Error Codes

- `VALIDATION_ERROR`: Invalid input parameters
- `FILE_TOO_LARGE`: File exceeds maximum size limit
- `UNSUPPORTED_FORMAT`: File format not supported
- `EXTRACTION_FAILED`: Content extraction failed
- `JOB_NOT_FOUND`: Async job not found
- `INTERNAL_ERROR`: Server internal error

## Rate Limiting

The API implements rate limiting to prevent abuse:

- **Synchronous requests**: 100 requests per minute per IP
- **Asynchronous requests**: 50 requests per minute per IP
- **File size limit**: 150MB per file

## Examples

### Python

```python
import requests

# Synchronous extraction
with open('document.pdf', 'rb') as f:
    files = {'file': f}
    data = {
        'include_metadata': 'true',
        'include_text': 'true',
        'include_structured_data': 'true'
    }
    response = requests.post('http://localhost:8000/api/v1/extract', 
                           files=files, data=data)
    result = response.json()
    print(f"Extracted text: {result['extracted_text']['content'][:200]}...")

# Asynchronous extraction
with open('large_document.pdf', 'rb') as f:
    files = {'file': f}
    data = {'priority': 'high'}
    response = requests.post('http://localhost:8000/api/v1/extract/async', 
                           files=files, data=data)
    job_id = response.json()['job_id']

# Check job status
status_response = requests.get(f'http://localhost:8000/api/v1/jobs/{job_id}')
status = status_response.json()
print(f"Job status: {status['status']}, Progress: {status['progress']}%")
```

### cURL

```bash
# Synchronous extraction
curl -X POST http://localhost:8000/api/v1/extract \
  -F "file=@document.pdf" \
  -F "include_metadata=true" \
  -F "include_text=true"

# Asynchronous extraction
curl -X POST http://localhost:8000/api/v1/extract/async \
  -F "file=@large_document.pdf" \
  -F "priority=high"

# Check job status
curl http://localhost:8000/api/v1/jobs/{job_id}
```

### JavaScript

```javascript
// Synchronous extraction
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('include_metadata', 'true');
formData.append('include_text', 'true');

fetch('http://localhost:8000/api/v1/extract', {
  method: 'POST',
  body: formData
})
.then(response => response.json())
.then(result => {
  console.log('Extracted text:', result.extracted_text.content);
});

// Asynchronous extraction
fetch('http://localhost:8000/api/v1/extract/async', {
  method: 'POST',
  body: formData
})
.then(response => response.json())
.then(result => {
  const jobId = result.job_id;
  // Poll for job completion
  pollJobStatus(jobId);
});
```

## WebSocket Support

For real-time job status updates, the API supports WebSocket connections:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/jobs/{job_id}');

ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('Job update:', data);
};
```