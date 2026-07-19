@echo off
title VocabTool Dev Server Launcher

echo ===================================================
echo VocabTool Dev Server Launcher
echo ===================================================

echo Checking if port 8001 is in use...
set conflicting_pid=
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8001" ^| findstr "LISTENING"') do (
    set conflicting_pid=%%a
)

if defined conflicting_pid (
    echo [WARNING] Port 8001 is occupied by process PID %conflicting_pid%.
    echo Killing conflicting process to prevent freeze...
    taskkill /F /PID %conflicting_pid%
    timeout /t 1 > nul
) else (
    echo [INFO] Port 8001 is free.
)

echo [INFO] Starting new dev server...
start "VocabTool Server (Port 8001)" cmd /k "python -m http.server 8001"

echo ===================================================
echo [SUCCESS] Server started successfully in a new window!
echo Please open: http://localhost:8001
echo ===================================================
timeout /t 5
