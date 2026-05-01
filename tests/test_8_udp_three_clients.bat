@echo off
:: ============================================================
:: Scenario 8 — Three simultaneous UDP clients
:: Tests: multi-agent handling without connection state
:: ============================================================
title Socket Test - UDP 3 Clients Simultaneous
echo.
echo [TEST] Scenario 8 (UDP): 3 simultaneous clients
echo ============================================================
echo.

cd /d "%~dp0.."

echo [Step 1] Starting UDP server (GUI dashboard, port 5001)...
start "UDP-Server" cmd /k python code\server\serveurUDP.py
timeout /t 2 /nobreak > nul

echo [Step 2] Starting UDP Client 1 (hostname: UDP-Client-ONE)...
start "UDP-Client 1" cmd /k python code\client\clientUDP.py UDP-Client-ONE
timeout /t 1 /nobreak > nul

echo [Step 3] Starting UDP Client 2 (hostname: UDP-Client-TWO)...
start "UDP-Client 2" cmd /k python code\client\clientUDP.py UDP-Client-TWO
timeout /t 1 /nobreak > nul

echo [Step 4] Starting UDP Client 3 (hostname: UDP-Client-THREE)...
start "UDP-Client 3" cmd /k python code\client\clientUDP.py UDP-Client-THREE
timeout /t 2 /nobreak > nul

echo.
echo [INFO] 3 agents should appear on the UDP server dashboard.
echo [INFO] Press Ctrl+C in each window to stop cleanly.
echo [INFO] Close this window when done.
pause
