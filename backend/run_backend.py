"""
SatQuery AI — Backend Launcher
Can be run directly from inside backend/
Usage:
  python run_backend.py
"""

import os
import sys
import subprocess

# Auto-detect dedicated D: drive virtual environment if run from global Python
VENV_PYTHON = r"D:\satquery_env\Scripts\python.exe"
if os.path.exists(VENV_PYTHON):
    current_exe = os.path.normcase(os.path.abspath(sys.executable))
    target_exe = os.path.normcase(os.path.abspath(VENV_PYTHON))
    if current_exe != target_exe:
        print(f"[*] Running from: {sys.executable}")
        print(f"[*] Auto-switching to dedicated D: drive environment: {VENV_PYTHON}")
        sys.exit(subprocess.call([VENV_PYTHON] + sys.argv))

# Verify required packages are installed in the active environment
for pkg, mod in [("python-multipart", "multipart"), ("langfuse", "langfuse")]:
    try:
        __import__(mod)
    except ImportError:
        print(f"[*] Installing required '{pkg}' into virtual environment...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

import uvicorn

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

if __name__ == "__main__":
    print(f"[*] Starting SatQuery AI FastAPI Backend from {BACKEND_DIR}...")
    print(f"[*] API will be live at: http://127.0.0.1:8000")
    print(f"[*] Docs available at: http://127.0.0.1:8000/docs")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True, app_dir=BACKEND_DIR)
