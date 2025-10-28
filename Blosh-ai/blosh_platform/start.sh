#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting Blosh Platform...${NC}"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is not installed. Please install Python 3.${NC}"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}Node.js is not installed. Please install Node.js.${NC}"
    exit 1
fi

# Start backend
echo -e "${GREEN}Starting backend server...${NC}"
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${BLUE}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
echo -e "${BLUE}Installing Python dependencies...${NC}"
pip install -r requirements.txt > /dev/null 2>&1

# Start Flask server in background
python app.py &
BACKEND_PID=$!
echo -e "${GREEN}Backend server started (PID: $BACKEND_PID)${NC}"

cd ..

# Start frontend
echo -e "${GREEN}Starting frontend server...${NC}"
cd frontend

# Install npm dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo -e "${BLUE}Installing npm dependencies (this may take a few minutes)...${NC}"
    npm install
fi

# Start React app
npm start &
FRONTEND_PID=$!

cd ..

echo -e "${GREEN}✓ Blosh Platform is starting!${NC}"
echo -e "${BLUE}Backend running on: http://localhost:5001${NC}"
echo -e "${BLUE}Frontend running on: http://localhost:3000${NC}"
echo -e "${BLUE}Password: Bloshai12!${NC}"
echo ""
echo -e "${GREEN}NOTE: Port 5000 is used by macOS AirPlay, so we use 5001${NC}"
echo ""
echo -e "Press Ctrl+C to stop all servers"

# Function to cleanup on exit
cleanup() {
    echo -e "\n${RED}Stopping servers...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    # Kill any remaining processes
    pkill -9 -f "python.*app.py" 2>/dev/null
    pkill -9 -f "react-scripts start" 2>/dev/null
    pkill -9 -f "node.*react-scripts" 2>/dev/null
    echo -e "${GREEN}Servers stopped.${NC}"
    exit 0
}

# Trap Ctrl+C
trap cleanup INT

# Wait for processes
wait

