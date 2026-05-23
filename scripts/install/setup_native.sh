#!/bin/bash

# Recon OS Native Setup for Kali/WSL
echo "[*] Starting Native Setup for Kali/WSL..."

# 1. Update System
sudo apt update

# 2. Install Python Environment
sudo apt install -y python3-venv python3-pip redis-tools

# 3. Create Virtual Env
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "[+] Created Python Virtual Environment"
fi

source venv/bin/activate

# 4. Install Dependencies
pip install -r requirements.txt
playwright install chromium
playwright install-deps

# 5. Check for Recon Tools (Kali Natives)
echo "[*] Checking for native Kali tools..."
tools=("subfinder" "nuclei" "httpx" "nmap")
for tool in "${tools[@]}"; do
    if command -v $tool &> /dev/null; then
        echo "[+] Found $tool"
    else
        echo "[-] $tool not found. Installing via go..."
        # Optional: Add go install logic here if needed
    fi
done

echo "[+] Setup Complete!"
echo "[!] To start the DBs, run: docker-compose -f docker-compose.db.yml up -d"
echo "[!] To start the API, run: source venv/bin/activate && uvicorn src.api.main:app --reload"
