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
    if sys.stdout.encoding != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass
    print("=" * 65)
    print(" [TRINETRA] SATQUERY AI FASTAPI BACKEND INITIALIZING")
    print(" [HOST] http://127.0.0.1:8000")
    print(" [DOCS] http://127.0.0.1:8000/docs")
    print(" [HEALTH] http://127.0.0.1:8000/api/v1/health")
    print("=" * 65)
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
