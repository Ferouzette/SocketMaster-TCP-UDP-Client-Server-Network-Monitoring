@echo off
:: ============================================================
:: Scenario 4 — Abrupt client disconnect (no BYE)
:: Tests: inactivity detection (3xT seconds), ALERT on server
:: ============================================================
title Socket Test - Abrupt Disconnect
echo.
echo [TEST] Scenario 4: Abrupt disconnect (no BYE)
echo ============================================================
echo.

cd /d "%~dp0.."

echo [Step 1] Starting TCP server (GUI dashboard)...
start "TCP-Server" cmd /k python code\server\serveurTCP.py
timeout /t 2 /nobreak > nul

echo [Step 2] Starting 2 clients...
start "TCP-Client 1" cmd /k python code\client\clientTCP.py TCP-Client-ONE
timeout /t 1 /nobreak > nul
start "TCP-Client 2" cmd /k python code\client\clientTCP.py TCP-Client-TWO
timeout /t 2 /nobreak > nul

echo.
echo [INFO] Let the clients run for ~10 seconds.
echo [INFO] Then CLOSE one client window WITHOUT pressing Ctrl+C (no BYE sent).
echo [INFO] The server should detect inactivity after 3xT seconds and show [ALERT].
echo [INFO] The remaining client should continue unaffected.
echo [INFO] Close this window when done.
pause
