@echo off
:: ============================================================
:: Scenario 9 — UDP client connecting to an inactive server
:: Tests: HELLO retry mechanism (MAX_RETRIES x 2s), clean exit
:: ============================================================
title Socket Test - UDP Server Unreachable
echo.
echo [TEST] Scenario 9 (UDP): Client with no server running
echo ============================================================
echo.

cd /d "%~dp0.."

echo [INFO] No server will be started.
echo [INFO] The UDP client will attempt HELLO up to 5 times (2s each),
echo        then exit cleanly with [ERROR].
echo.

echo [Step 1] Starting UDP client (no server)...
start "UDP-Client - No Server" cmd /k python code\client\clientUDP.py CLIENT-NO-SERVER
timeout /t 2 /nobreak > nul

echo.
echo [INFO] Observe the retry messages and final error in the client window.
echo [INFO] Close this window when done.
pause
