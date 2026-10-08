@echo off
REM Liana Stop Script for Windows
REM This script stops all Liana processes

echo ========================================
echo Stopping Liana
echo ========================================
echo.

echo Stopping backend...
taskkill /FI /WI /T /FI "WINDOWTITLE eq Liana Backend*" >nul 2>&1

echo Stopping frontend...
taskkill /FI /WI /T /FI "WINDOWTITLE eq Liana Frontend*" >nul 2>&1

echo.
echo ========================================
echo Liana stopped.
echo ========================================
echo.
pause
