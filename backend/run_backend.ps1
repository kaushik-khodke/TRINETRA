Write-Host "[*] Starting SatQuery AI FastAPI Backend..." -ForegroundColor Cyan
& "D:\satquery_env\Scripts\python.exe" -m pip install python-multipart langfuse --quiet
& "D:\satquery_env\Scripts\python.exe" run_backend.py
