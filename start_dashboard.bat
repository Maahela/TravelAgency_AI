@echo off
REM Unified launcher for Admin Dashboard (Backend + Frontend)

echo ==========================================
echo Starting JAK Email Bot Admin Dashboard
echo ==========================================

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Start backend in background
echo Starting backend server...
cd admin_dashboard\backend
start /B python main.py
timeout /t 3 /nobreak >nul

REM Start frontend
echo Starting frontend dev server...
cd ..\frontend
start /B npm run dev

echo.
echo ==========================================
echo Dashboard is running!
echo Backend:  http://localhost:4002
echo Frontend: http://localhost:3000
echo ==========================================
echo.
echo Press Ctrl+C to stop (you may need to manually kill processes)
pause
