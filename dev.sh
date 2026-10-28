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

# 0. Bersihkan proses lama & lock jika masih ada yang nyangkut di port 8000 / 3000
EXISTING_PIDS=$(lsof -ti :8000,3000 2>/dev/null)
if [ -n "$EXISTING_PIDS" ]; then
    echo -e "${YELLOW}[INFO] Terdeteksi proses yang masih menggunakan port 8000 / 3000. Membersihkan...${NC}"
    kill -9 $EXISTING_PIDS 2>/dev/null
    sleep 0.5
fi
rm -f "$FRONTEND_DIR/.next/dev/lock" 2>/dev/null

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

BE_PID=0
FE_PID=0
MONITOR_PID=0
CLEANED_UP=0

# Fungsi pembersihan saat tombol Ctrl+C ditekan atau saat script exit
cleanup() {
    # Hindari eksekusi berulang
    if [ "$CLEANED_UP" -eq 1 ]; then
        return
    fi
    CLEANED_UP=1
    trap - SIGINT SIGTERM EXIT

    echo ""
    echo -e "${YELLOW}🛑 Menghentikan semua service SALEP...${NC}"

    # Hentikan monitor background jika ada
    if [ "$MONITOR_PID" -gt 0 ] && kill -0 "$MONITOR_PID" 2>/dev/null; then
        kill "$MONITOR_PID" 2>/dev/null
        wait "$MONITOR_PID" 2>/dev/null
    fi

    # 1. Matikan Backend jika aktif
    if [ "$BE_PID" -gt 0 ] && kill -0 "$BE_PID" 2>/dev/null; then
        kill -TERM "-$BE_PID" 2>/dev/null || kill -TERM "$BE_PID" 2>/dev/null
    fi

    # 2. Matikan Frontend jika aktif
    if [ "$FE_PID" -gt 0 ] && kill -0 "$FE_PID" 2>/dev/null; then
        kill -TERM "-$FE_PID" 2>/dev/null || kill -TERM "$FE_PID" 2>/dev/null
    fi

    # 3. Tunggu sejenak, jika masih ada sisa proses di port 8000/3000 lakukan force kill
    sleep 0.5
    local REMAINING_PIDS
    REMAINING_PIDS=$(lsof -ti :8000,3000 2>/dev/null)
    if [ -n "$REMAINING_PIDS" ]; then
        kill -9 $REMAINING_PIDS 2>/dev/null
    fi

    rm -f "$FRONTEND_DIR/.next/dev/lock" 2>/dev/null
    echo -e "${GREEN}✔ Semua service berhasil dimatikan.${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# Jalankan Backend (FastAPI / Uvicorn)
echo -e "${GREEN}▶ Menjalankan Backend:${NC}  http://localhost:8000"
(
    cd "$BACKEND_DIR"
    source .venv/bin/activate
    exec uvicorn app.main:app --reload --port 8000
) < /dev/null &
BE_PID=$!

# Beri jeda 2 detik dan cek apakah Backend berhasil jalan
sleep 2
if ! kill -0 "$BE_PID" 2>/dev/null; then
    echo -e "\n${RED}[ERROR] Backend gagal berjalan atau berhenti mendadak!${NC}"
    echo -e "${YELLOW}Silakan periksa pesan error backend di atas.${NC}"
    cleanup
fi

# Jalankan Frontend (Next.js)
echo -e "${CYAN}▶ Menjalankan Frontend:${NC} http://localhost:3000"
(
    cd "$FRONTEND_DIR"
    exec npm run dev
) < /dev/null &
FE_PID=$!

echo -e "\n${BOLD}${GREEN}✔ Kedua service aktif!${NC}"
echo -e "Tekan ${BOLD}${YELLOW}Ctrl + C${NC} di terminal ini untuk mematikan BE dan FE sekaligus.\n"

# Monitor di background: jika BE atau FE mati mendadak, picu cleanup pada script utama
MAIN_PID=$$
(
    while kill -0 "$BE_PID" 2>/dev/null && kill -0 "$FE_PID" 2>/dev/null; do
        sleep 1
    done
    kill -INT "$MAIN_PID" 2>/dev/null
) &
MONITOR_PID=$!

# Tunggu sinyal secara instan via built-in wait (responsif terhadap Ctrl+C)
wait
