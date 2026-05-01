@echo off
:: ============================================================
:: Scenario 2 — Three simultaneous clients
:: Tests: multi-client handling, averaged stats on dashboard
:: ============================================================
title Socket Test - 3 Clients Simultaneous
echo.
echo [TEST] Scenario 2: 3 simultaneous clients
echo ============================================================
echo.

cd /d "%~dp0.."

echo [Step 1] Starting TCP server (GUI dashboard)...
start "TCP-Server" cmd /k python code\server\serveurTCP.py
timeout /t 2 /nobreak > nul

echo [Step 2] Starting Client 1 (hostname: TCP-Client-ONE)...
start "TCP-Client 1" cmd /k python code\client\clientTCP.py TCP-Client-ONE
timeout /t 1 /nobreak > nul

echo [Step 3] Starting Client 2 (hostname: TCP-Client-TWO)...
start "TCP-Client 2" cmd /k python code\client\clientTCP.py TCP-Client-TWO
timeout /t 1 /nobreak > nul

echo [Step 4] Starting Client 3 (hostname: TCP-Client-THREE)...
start "TCP-Client 3" cmd /k python code\client\clientTCP.py TCP-Client-THREE
timeout /t 2 /nobreak > nul

echo.
echo [INFO] 3 agents should appear on the server dashboard.
echo [INFO] Avg CPU and RAM are computed across all active agents.
echo [INFO] Press Ctrl+C in each window to stop cleanly.
echo [INFO] Close this window when done.
pause
