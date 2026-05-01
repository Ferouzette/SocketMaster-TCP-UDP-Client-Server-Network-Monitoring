@echo off
:: ============================================================
:: TCP scenarios  : 1 – 6
:: UDP scenarios  : 7 – 10
:: ============================================================
title SocketMaster - Test Suite
color 0A

:menu
cls
echo.
echo  =====================================================
echo     SocketMaster - TCP + UDP Monitoring Test Suite
echo  =====================================================
echo.
echo   TCP (port 5000)
echo   [1]  Single TCP client
echo   [2]  3 simultaneous TCP clients
echo   [3]  Malformed / invalid messages  (customClient)
echo   [4]  Abrupt disconnect - inactivity detection
echo   [5]  TCP client with no server  (ConnectionRefused)
echo   [6]  Flood / rate-limit stress test

echo.
echo   UDP (port 5001) 
echo   [7]  Single UDP client
echo   [8]  3 simultaneous UDP clients
echo   [9]  UDP client with no server  (retry + exit)
echo   [10] TCP vs UDP side-by-side comparison
echo.
echo   [0]  Exit
echo.
set /p choice="  Select a test [0-10]: "

if "%choice%"=="1" call tests\test_1_single_client.bat        & goto menu
if "%choice%"=="2" call tests\test_2_three_clients.bat        & goto menu
if "%choice%"=="3" call tests\test_3_malformed_messages.bat   & goto menu
if "%choice%"=="4" call tests\test_4_abrupt_disconnect.bat    & goto menu
if "%choice%"=="5" call tests\test_5_tcp_no_server.bat        & goto menu
if "%choice%"=="6" call tests\test_6_flood.bat                & goto menu
if "%choice%"=="7" call tests\test_7_udp_single_client.bat    & goto menu
if "%choice%"=="8" call tests\test_8_udp_three_clients.bat    & goto menu
if "%choice%"=="9" call tests\test_9_udp_no_server.bat        & goto menu
if "%choice%"=="10" call tests\test_10_tcp_vs_udp.bat         & goto menu
if "%choice%"=="0" goto end

echo   [!] Invalid choice. Please enter a number between 0 and 10.
timeout /t 2 /nobreak > nul
goto menu

:end
echo.
echo  Goodbye!
exit /b
