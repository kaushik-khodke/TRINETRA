"""
SatQuery AI — Backend Launcher
Can be run directly from inside backend/
Usage:
  python run_backend.py
"""

import os
import sys
import uvicorn

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))
    reload = os.environ.get("RELOAD", "true").lower() == "true"
    print(f"[*] Starting SatQuery AI FastAPI Backend from {BACKEND_DIR}...")
    print(f"[*] API will be live at: http://{host}:{port}")
    uvicorn.run("app.main:app", host=host, port=port, reload=reload, app_dir=BACKEND_DIR, timeout_keep_alive=75)
