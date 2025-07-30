"""
API-Package für die Universal File Extractor API.
"""

from fastapi import APIRouter

from app.api.routes import async_extract, extract, health

# Haupt-Router erstellen
api_router = APIRouter()

# Routen registrieren
api_router.include_router(extract.router, tags=['extraction'])
api_router.include_router(health.router, tags=['health'])
api_router.include_router(async_extract.router, tags=['async'])
