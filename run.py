"""
Krishok-Bondhu: Server Launcher
Run with: python run.py
Starts the FastAPI application on http://localhost:8000
"""

import os
import sys

# Ensure root workspace directory is in python path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import uvicorn
from backend.main import app

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    print(f"🌾 Starting Krishok-Bondhu Server on http://localhost:{port}")
    print(f"📊 Single-Page Interactive Dashboard: http://localhost:{port}/")
    print(f"📑 API Documentation (Swagger): http://localhost:{port}/docs")
    uvicorn.run("backend.main:app", host=host, port=port, reload=False)
