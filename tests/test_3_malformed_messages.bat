@echo off
:: ============================================================
:: Scenario 3 — Malformed / invalid messages
:: Tests: server robustness, ERROR responses, MAX_TRIES logic
:: ============================================================
title Socket Test - Malformed Messages
echo.
echo [TEST] Scenario 3: Malformed messages via customClient
echo ============================================================
echo.

cd /d "%~dp0.."

echo [Step 1] Starting TCP server (GUI dashboard)...
start "TCP-Server" cmd /k python code\server\serveurTCP.py
timeout /t 2 /nobreak > nul

echo [Step 2] Starting a normal client (hostname: Client-ONE)...
start "TCP-Client 1" cmd /k python code\client\clientTCP.py TCP-Client-ONE
timeout /t 1 /nobreak > nul

echo [Step 3] Launching customClient — enter an INVALID message when prompted.
echo          Examples of bad messages:  BONJOUR agent1 / REPORT / HELLO / XYZ
echo.
start "Custom Client" cmd /k python code\client\customClient.py
timeout /t 2 /nobreak > nul

echo.
echo [INFO] The server should reply ERROR InvalidMessageFormat for unknown commands.
echo [INFO] customClient will abort after %MAX_TRIES% consecutive rejections.
echo [INFO] The normal client should continue running unaffected.
echo [INFO] Close this window when done.
pause
