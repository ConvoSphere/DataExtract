#!/usr/bin/env python3

import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("Testing app import...")
    from app.main import app
    print("✓ App imported successfully")
    
    print("Testing app startup...")
    # Try to access the app's routes
    routes = app.routes
    print(f"✓ App has {len(routes)} routes")
    
    print("Testing root endpoint...")
    # Try to create a test request
    from fastapi.testclient import TestClient
    client = TestClient(app)
    response = client.get("/")
    print(f"✓ Root endpoint returned status {response.status_code}")
    print(f"Response: {response.json()}")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()