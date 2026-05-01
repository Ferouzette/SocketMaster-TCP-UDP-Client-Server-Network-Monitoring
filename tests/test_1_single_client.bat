@echo off
:: ============================================================
:: Scenario 1 — Single client connected to the server
:: Tests: HELLO, periodic REPORT, BYE on Ctrl+C
:: ============================================================
title Socket Test - Single Client
echo.
echo [TEST] Scenario 1: Single client
echo ============================================================
echo.

cd /d "%~dp0.."

echo [Step 1] Starting TCP server (GUI dashboard)...
start "TCP Server" cmd /k python code\server\serveurTCP.py
timeout /t 2 /nobreak > nul

echo [Step 2] Starting 1 client (hostname: TCP-Client-ONE)...
start "TCP Client 1" cmd /k python code\client\clientTCP.py TCP-Client-ONE
timeout /t 2 /nobreak > nul

echo.
echo [INFO] Watch the server dashboard for agent stats.
echo [INFO] Press Ctrl+C in each window to stop cleanly (BYE sent).
echo [INFO] Close this window when done.
pause
