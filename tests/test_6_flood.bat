@echo off
:: ============================================================
:: Scenario 6 — Flood / Rate-limit stress test
:: Tests: MAX_AGENTS cap, RATE_LIMIT_S blocking, server stability
:: Requires: flood.py (50 threads x 1000 REPORT each)
:: ============================================================
title Socket Test - Flood Attack
echo.
echo [TEST] Scenario 6: Flood / rate-limit stress test
echo ============================================================
echo.

cd /d "%~dp0.."

echo [Step 1] Starting TCP server (GUI dashboard)...
start "TCP-Server" cmd /k python code\server\serveurTCP.py
timeout /t 2 /nobreak > nul

echo [Step 2] Launching flood simulation (50 threads x 1000 REPORT)...
echo          Only the first %MAX_AGENTS% agents will be registered (MAX_AGENTS cap).
echo          Excess REPORT messages are blocked by rate limiting.
echo.
start "Flood Attack" cmd /k python code\flood.py
timeout /t 2 /nobreak > nul

echo.
echo [INFO] Watch the server console for [BLOCK] and [RATE LIMIT] summaries.
echo [INFO] The server should remain stable and not crash.
echo [INFO] Close this window when done.
pause
