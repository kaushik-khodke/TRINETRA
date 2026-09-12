"""
SatQuery AI — Universal Backend Launcher
Can be run from either project root (TRINETRA/) or from inside (backend/).
Usage:
  python run_backend.py
"""

import os
import sys
import uvicorn

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# If run from root, add backend to sys.path
backend_dir = os.path.join(CURRENT_DIR, "backend") if os.path.exists(os.path.join(CURRENT_DIR, "backend")) else CURRENT_DIR
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

if __name__ == "__main__":
    print(f"[*] Starting SatQuery AI FastAPI Backend...")
    print(f"[*] Working Directory: {backend_dir}")
    print(f"[*] API will be live at: http://127.0.0.1:8000")
    print(f"[*] Docs available at: http://127.0.0.1:8000/docs")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True, app_dir=backend_dir)
