# backend/scripts/dev.sh
#!/bin/bash

# Development script for AccessLens
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN} Starting AccessLens Development Environment${NC}"
echo "========================================"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for required tools
echo -e "\n${YELLOW}Checking prerequisites...${NC}"

if ! command_exists python3; then
    echo -e "${RED} Python 3 not found${NC}"
    exit 1
fi

if ! command_exists docker; then
    echo -e "${RED} Docker not found${NC}"
    exit 1
fi

if ! command_exists npm; then
    echo -e "${RED} npm not found${NC}"
    exit 1
fi

echo -e "${GREEN} All prerequisites satisfied${NC}"

# Activate virtual environment
echo -e "\n${YELLOW}Activating virtual environment...${NC}"
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo -e "${GREEN} Virtual environment activated${NC}"
else
    echo -e "${RED} Virtual environment not found. Run setup.sh first${NC}"
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${RED} .env file not found. Run setup.sh first${NC}"
    exit 1
fi

# Load environment variables
source .env

# Start services based on mode
case "$1" in
    "docker")
        echo -e "\n${YELLOW}Starting Docker services...${NC}"
        docker-compose up -d postgres redis
        echo -e "${GREEN} Docker services started${NC}"
        ;;
    "local")
        echo -e "\n${YELLOW}Using local services${NC}"
        ;;
    *)
        echo -e "\n${YELLOW}Starting in development mode${NC}"
        ;;
esac

# Start backend
echo -e "\n${YELLOW}Starting backend server...${NC}"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo -e "${GREEN} Backend started (PID: $BACKEND_PID)${NC}"

# Wait for backend to start
sleep 3

# Check if backend is responding
if curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN} Backend health check passed${NC}"
else
    echo -e "${RED} Backend health check failed${NC}"
    kill $BACKEND_PID
    exit 1
fi

# Start frontend
echo -e "\n${YELLOW}Starting frontend...${NC}"
cd ../frontend
npm run dev &
FRONTEND_PID=$!
cd ../backend
echo -e "${GREEN} Frontend started (PID: $FRONTEND_PID)${NC}"

echo -e "\n${GREEN} All services started!${NC}"
echo -e " Frontend: ${GREEN}http://localhost:3000${NC}"
echo -e " Backend API: ${GREEN}http://localhost:8000${NC}"
echo -e " API Docs: ${GREEN}http://localhost:8000/docs${NC}"
echo -e "\n${YELLOW}Press Ctrl+C to stop all services${NC}"

# Handle shutdown
trap 'echo -e "\n${YELLOW}Stopping services...${NC}"; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo -e "${GREEN} Services stopped${NC}"; exit 0' INT TERM

# Wait for processes
wait