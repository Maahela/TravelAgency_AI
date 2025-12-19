#!/bin/bash
# Unified launcher for Admin Dashboard (Backend + Frontend)

echo "=========================================="
echo "Starting JAK Email Bot Admin Dashboard"
echo "=========================================="

# Start backend in background
echo "Starting backend server..."
cd admin_dashboard/backend
python main.py &
BACKEND_PID=$!
echo "Backend started (PID: $BACKEND_PID)"

# Wait for backend to initialize
sleep 3

# Start frontend
echo "Starting frontend dev server..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!
echo "Frontend started (PID: $FRONTEND_PID)"

echo ""
echo "=========================================="
echo "Dashboard is running!"
echo "Backend:  http://localhost:4002"
echo "Frontend: http://localhost:3000"
echo "=========================================="
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for Ctrl+C
trap "echo 'Stopping servers...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
