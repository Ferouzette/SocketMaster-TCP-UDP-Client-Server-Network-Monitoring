@echo off
:: ============================================================
:: Scenario 7 — Single UDP client
:: Tests: HELLO retry, periodic REPORT (no ack guarantee), BYE
:: ============================================================
title Socket Test - UDP Single Client
echo.
echo [TEST] Scenario 7 (UDP): Single client
echo ============================================================
echo.

cd /d "%~dp0.."

echo [Step 1] Starting UDP server (GUI dashboard, port 5001)...
start "UDP-Server" cmd /k python code\server\serveurUDP.py
timeout /t 2 /nobreak > nul

echo [Step 2] Starting 1 UDP client (hostname: UDP-Client-ONE)...
start "UDP-Client 1" cmd /k python code\client\clientUDP.py UDP-Client-ONE
timeout /t 2 /nobreak > nul

echo.
echo [INFO] Watch the UDP server dashboard for agent stats.
echo [INFO] Unlike TCP, packet loss is possible — [WARNING] is normal.
echo [INFO] Press Ctrl+C in each window to stop cleanly (BYE sent).
echo [INFO] Close this window when done.
pause
