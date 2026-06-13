#!/bin/bash

# Tech Team AI Agent — Demo Startup Script
# Chạy: bash start.sh

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}"
echo "  ████████╗███████╗ ██████╗██╗  ██╗"
echo "     ██╔══╝██╔════╝██╔════╝██║  ██║"
echo "     ██║   █████╗  ██║     ███████║"
echo "     ██║   ██╔══╝  ██║     ██╔══██║"
echo "     ██║   ███████╗╚██████╗██║  ██║"
echo "     ╚═╝   ╚══════╝ ╚═════╝╚═╝  ╚═╝"
echo -e "${NC}"
echo -e "${GREEN}  Tech Team AI Agent — Demo v1.0${NC}"
echo ""

# Check .env
if [ ! -f "backend/.env" ]; then
  echo -e "${YELLOW}⚠️  Chưa có file backend/.env${NC}"
  echo -e "   Tạo file từ mẫu và điền GREENODE_API_KEY:"
  echo -e "   ${BLUE}cp backend/.env.example backend/.env${NC}"
  echo ""
  read -p "Nhấn Enter sau khi đã tạo .env để tiếp tục..."
fi

# Check Greenode API Key
source backend/.env 2>/dev/null
if [ -z "$GREENODE_API_KEY" ] || [ "$GREENODE_API_KEY" = "api_key_here" ]; then
  echo -e "${RED}❌ GREENODE_API_KEY chưa được cấu hình trong backend/.env${NC}"
  echo -e "   Lấy API key tại: https://greenode.com"
  exit 1
fi

echo -e "${GREEN}✅ Greenode API Key OK${NC}"
echo ""

# Kill any process using a port (robust for macOS)
kill_port() {
  local port=$1
  local pids

  pids=$(lsof -ti tcp:"$port" 2>/dev/null)
  if [ -n "$pids" ]; then
    echo -e "${YELLOW}Port $port dang bi chiem → giai phong...${NC}"
    echo "$pids" | xargs kill -9 2>/dev/null
    sleep 1
  fi

  # Second pass
  pids=$(lsof -ti tcp:"$port" 2>/dev/null)
  if [ -n "$pids" ]; then
    echo "$pids" | xargs kill -9 2>/dev/null
    sleep 1
  fi

  if lsof -ti tcp:"$port" > /dev/null 2>&1; then
    echo -e "${RED}Khong the giai phong port $port. Chay: lsof -ti:$port | xargs kill -9${NC}"
    exit 1
  else
    echo -e "${GREEN}Port $port san sang${NC}"
  fi
}

kill_port 8000
kill_port 5173

# Setup Backend
echo -e "${BLUE}[1/4] Cài đặt Backend dependencies...${NC}"
cd backend

if [ ! -d "venv" ]; then
  python3 -m venv venv
fi

venv/bin/pip install -r requirements.txt -q

echo -e "${GREEN}✅ Backend ready${NC}"

# Start Backend
echo -e "${BLUE}[2/4] Khởi động Backend (port 8000)...${NC}"
venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Wait for backend to be healthy (max 10s)
echo -n "   Chờ backend khởi động"
for i in $(seq 1 10); do
  sleep 1
  if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e " ${GREEN}✅ Backend PID: $BACKEND_PID${NC}"
    break
  fi
  echo -n "."
  if [ "$i" -eq 10 ]; then
    echo -e "\n${RED}❌ Backend không khởi động được. Kiểm tra lại GREENODE_API_KEY và requirements.${NC}"
    exit 1
  fi
done

cd ..

# Setup Frontend
echo -e "${BLUE}[3/4] Cài đặt Frontend dependencies...${NC}"
cd frontend

if [ ! -d "node_modules" ]; then
  npm install -q
fi

# Copy env if not exists
if [ ! -f ".env" ]; then
  cp .env.example .env
fi

echo -e "${GREEN}✅ Frontend ready${NC}"

# Start Frontend
echo -e "${BLUE}[4/4] Khởi động Frontend (port 5173)...${NC}"
npm run dev &
FRONTEND_PID=$!

# Wait for frontend then open browser
echo -n "   Chờ frontend khởi động"
for i in $(seq 1 10); do
  sleep 1
  if curl -s http://localhost:5173 > /dev/null 2>&1; then
    echo -e " ${GREEN}✅${NC}"
    break
  fi
  echo -n "."
done

cd ..

# Auto open browser (macOS)
sleep 1
open http://localhost:5173 2>/dev/null || true

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  🚀 Agent đang chạy!${NC}"
echo ""
echo -e "  Frontend:  ${BLUE}http://localhost:5173${NC}"
echo -e "  Backend:   ${BLUE}http://localhost:8000${NC}"
echo -e "  API Docs:  ${BLUE}http://localhost:8000/docs${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "  Nhấn ${RED}Ctrl+C${NC} để dừng tất cả"
echo ""

# Cleanup on exit — kill both processes and free ports
cleanup() {
  echo ""
  echo -e "${YELLOW}Đang dừng tất cả services...${NC}"
  kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
  kill_port 8000
  kill_port 5173
  echo -e "${GREEN}✅ Đã dừng sạch${NC}"
  exit 0
}
trap cleanup INT TERM

wait