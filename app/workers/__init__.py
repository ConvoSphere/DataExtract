"""
Workers Package für asynchrone Verarbeitung.
"""

from app.workers.tasks import extract_file_task

__all__ = ['extract_file_task']
