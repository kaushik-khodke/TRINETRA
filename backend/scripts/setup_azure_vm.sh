#!/usr/bin/env bash
# ==============================================================================
# TRINETRA / SatQuery AI — Azure VM Production Setup Script
# SIH 2026 • Problem Statement 26167 • Indian Space Research Organisation (ISRO)
# ==============================================================================
set -e

echo "=== [1/6] Updating system & installing dependencies ==="
sudo apt-get update -y
sudo apt-get install -y --no-install-recommends \
    python3-pip \
    python3-venv \
    python3-dev \
    git \
    git-lfs \
    curl \
    build-essential \
    libgdal-dev \
    gdal-bin \
    libgl1 \
    libglib2.0-0

echo "=== [2/6] Setting up virtual environment ==="
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"
cd "$BACKEND_DIR"

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

echo "=== [3/6] Installing CPU PyTorch (fast & lightweight) ==="
pip install --upgrade pip
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

echo "=== [4/6] Installing backend dependencies ==="
pip install -r requirements.txt

echo "=== [5/6] Creating required directories ==="
mkdir -p outputs/runs outputs/export_packages uploads/workstation

echo "=== [6/6] Configuring systemd service (auto-restart on crash & reboot) ==="
CURRENT_USER=$(whoami)
SERVICE_FILE="/etc/systemd/system/trinetra.service"

sudo bash -c "cat > $SERVICE_FILE" <<EOF
[Unit]
Description=TRINETRA FastAPI Backend Server
After=network.target

[Service]
User=$CURRENT_USER
WorkingDirectory=$BACKEND_DIR
ExecStart=$BACKEND_DIR/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --timeout-keep-alive 75
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable trinetra
sudo systemctl restart trinetra

echo "=============================================================================="
echo " [SUCCESS] TRINETRA Backend is now running as a persistent system service!"
echo " - Status check : sudo systemctl status trinetra"
echo " - Live logs    : sudo journalctl -u trinetra -f"
echo " - Health check : curl http://localhost:8000/api/v1/health"
echo "=============================================================================="
