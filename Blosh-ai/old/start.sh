#!/bin/bash

# Blosh AI Startup Script
echo "🚀 Starting Blosh AI..."

# Check if we're in the right directory
if [ ! -d "server" ] || [ ! -d "client" ]; then
    echo "❌ Please run this script from the Blosh-ai root directory"
    exit 1
fi

# Start Flask server in background
echo "🐍 Starting Flask server..."
cd server
python3 app.py &
FLASK_PID=$!
cd ..

# Wait a moment for Flask to start
sleep 2

# Start React development server
echo "⚛️  Starting React development server..."
cd client
npm start &
REACT_PID=$!
cd ..

echo "✅ Both servers started!"
echo "📝 Flask server: http://localhost:5001"
echo "🌐 React app: http://localhost:3000"
echo ""
echo "Default login credentials:"
echo "Username: blosh"
echo "Password: blosh12!"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for user to stop
trap "echo '🛑 Stopping servers...'; kill $FLASK_PID $REACT_PID; exit" INT
wait
