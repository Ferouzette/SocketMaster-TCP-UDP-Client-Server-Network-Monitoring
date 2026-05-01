@echo off
:: ============================================================
:: Scenario 10 — TCP vs UDP side-by-side comparison
:: Tests: both servers + both clients running simultaneously
:: TCP  → port 5000 | UDP → port 5001
:: ============================================================
title Socket Test - TCP vs UDP Comparison
echo.
echo [TEST] Scenario 10: TCP vs UDP side-by-side
echo ============================================================
echo.

cd /d "%~dp0.."

echo [Step 1] Starting TCP server (port 5000)...
start "TCP-Server" cmd /k python code\server\serveurTCP.py
timeout /t 2 /nobreak > nul

echo [Step 2] Starting UDP server (port 5001)...
start "UDP-Server" cmd /k python code\server\serveurUDP.py
timeout /t 2 /nobreak > nul

echo [Step 3] Starting TCP client...
start "TCP-Client" cmd /k python code\client\clientTCP.py TCP-CLIENT
timeout /t 1 /nobreak > nul

echo [Step 4] Starting UDP client...
start "UDP-Client" cmd /k python code\client\clientUDP.py UDP-CLIENT
timeout /t 2 /nobreak > nul

echo.
echo [INFO] Two dashboards should be open - one TCP, one UDP.
echo [INFO] Observe the differences in behavior:
echo        - TCP: connection-oriented, guaranteed delivery
echo        - UDP: connectionless, possible packet loss ([WARNING])
echo [INFO] Press Ctrl+C in client windows to send BYE and disconnect cleanly.
echo [INFO] Close this window when done.
pause
