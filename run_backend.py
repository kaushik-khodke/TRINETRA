"""
TRINETRA (SatQuery AI) — Backend Server Runner
Run this script to launch the FastAPI backend server on http://127.0.0.1:8000
"""

import os
import sys

# Add project root and backend to python path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import uvicorn

if __name__ == "__main__":
    print("=" * 65)
    print(" 🚀 SATQUERY AI (TRINETRA) FASTAPI BACKEND INITIALIZING")
    print(" 📡 Host: http://127.0.0.1:8000")
    print(" 📚 API Documentation (Swagger): http://127.0.0.1:8000/docs")
    print(" 🩺 Health Check: http://127.0.0.1:8000/api/v1/health")
    print("=" * 65)
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
