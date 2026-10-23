#!/usr/bin/env bash

# ==============================================================================
# SALEP Development Server Runner (Backend + Frontend)
# ==============================================================================

set -m # Enable job control so process groups can be signaled cleanly

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

# ANSI Colors
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${CYAN}${BOLD}====================================================${NC}"
echo -e "${CYAN}${BOLD}   🚀 Memulai SALEP Development Environment         ${NC}"
echo -e "${CYAN}${BOLD}====================================================${NC}"

# 1. Validasi Backend .venv
if [ ! -d "$BACKEND_DIR/.venv" ]; then
    echo -e "${RED}[ERROR] Virtual environment backend tidak ditemukan di: backend/.venv${NC}"
    echo -e "${YELLOW}Silakan buat virtual environment terlebih dahulu:${NC}"
    echo "  cd backend && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# 2. Validasi Frontend node_modules
if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    echo -e "${YELLOW}[INFO] node_modules frontend belum terpasang. Menjalankan npm install...${NC}"
    (cd "$FRONTEND_DIR" && npm install)
fi

# Fungsi pembersihan saat tombol Ctrl+C ditekan
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Menghentikan semua service SALEP...${NC}"
    # Matikan seluruh process group
    kill -- -$$ 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# Jalankan Backend (FastAPI / Uvicorn)
echo -e "${GREEN}▶ Menjalankan Backend:${NC}  http://localhost:8000"
(
    cd "$BACKEND_DIR"
    source .venv/bin/activate
    exec uvicorn app.main:app --reload --port 8000
) &
BE_PID=$!

# Beri jeda 1 detik agar log backend tidak tumpang tindih saat startup
sleep 1

# Jalankan Frontend (Next.js)
echo -e "${CYAN}▶ Menjalankan Frontend:${NC} http://localhost:3000"
(
    cd "$FRONTEND_DIR"
    exec npm run dev
) &
FE_PID=$!

echo -e "\n${BOLD}${GREEN}✔ Kedua service aktif!${NC}"
echo -e "Tekan ${BOLD}${YELLOW}Ctrl + C${NC} di terminal ini untuk mematikan BE dan FE sekaligus.\n"

# Tunggu hingga pengguna menekan Ctrl+C
wait
