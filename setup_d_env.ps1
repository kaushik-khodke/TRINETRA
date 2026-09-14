# TRINETRA / SatQuery AI — Install PyTorch CUDA 100% on D: Drive
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Setting up Python Environment & PyTorch CUDA on D: Drive" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Set temporary directories to D: drive (bypasses full C: drive)
New-Item -ItemType Directory -Path "D:\pip_temp" -Force | Out-Null
New-Item -ItemType Directory -Path "D:\pip_cache" -Force | Out-Null
$env:TMP = "D:\pip_temp"
$env:TEMP = "D:\pip_temp"
$env:PIP_CACHE_DIR = "D:\pip_cache"
Write-Host "[1/4] Configured temporary scratch space to D:\pip_temp" -ForegroundColor Green

# 2. Create Python virtual environment on D: drive
Write-Host "[2/4] Creating virtual environment at D:\satquery_env..." -ForegroundColor Yellow
py -3.10 -m venv D:\satquery_env
if (-not (Test-Path "D:\satquery_env\Scripts\python.exe")) {
    Write-Host "[ERROR] Failed to create venv at D:\satquery_env" -ForegroundColor Red
    exit 1
}
Write-Host "[SUCCESS] Virtual environment created on D: drive!" -ForegroundColor Green

# 3. Install the already downloaded CUDA wheels from D:\torch_wheels
Write-Host "[3/4] Installing CUDA PyTorch into D:\satquery_env (uses 0 bytes on C:)..." -ForegroundColor Yellow
$torchWhl = "D:\torch_wheels\torch-2.5.1+cu121-cp310-cp310-win_amd64.whl"
$visionWhl = "D:\torch_wheels\torchvision-0.20.1+cu121-cp310-cp310-win_amd64.whl"

& "D:\satquery_env\Scripts\python.exe" -m pip install $torchWhl $visionWhl --no-deps
& "D:\satquery_env\Scripts\python.exe" -m pip install numpy pillow torchvision pyyaml matplotlib

# 4. Test CUDA on RTX 3050 GPU
Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "[4/4] Verifying CUDA on your NVIDIA RTX 3050 GPU..." -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
& "D:\satquery_env\Scripts\python.exe" -c "import torch; print('CUDA Available:', torch.cuda.is_available(), '| GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'None')"

Write-Host "`n[DONE] To train models on your GPU in the future, use:" -ForegroundColor Green
Write-Host '& "D:\satquery_env\Scripts\python.exe" backend/training/03_grounding/train.py --data_dir "D:\datasets\DIOR_RSVG" --profile balanced --export' -ForegroundColor White
