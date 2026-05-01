@echo off
:: ============================================================
:: Scenario 5 — TCP client connecting to an inactive server
:: Tests: ConnectionRefusedError detection, clean exit message
:: ============================================================
title Socket Test - TCP Server Unreachable
echo.
echo [TEST] Scenario 5 (TCP): Client with no server running
echo ============================================================
echo.

cd /d "%~dp0.."

echo [INFO] No server will be started.
echo [INFO] The TCP client will attempt to connect and immediately
echo        receive ConnectionRefused, then exit cleanly.
echo.

echo [Step 1] Starting TCP client (no server)...
start "TCP-Client - No Server" cmd /k python code\client\clientTCP.py CLIENT-NO-SERVER
timeout /t 2 /nobreak > nul

echo.
echo [INFO] Observe the [ERROR] message in the client window:
echo        "Could not connect to 127.0.0.1:5000. Is the server running?"
echo [INFO] Close this window when done.
pause