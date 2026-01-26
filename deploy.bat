@echo off
REM Quick Deployment Script for TEMPORAL DEBT
REM This script helps you deploy the game quickly

echo ========================================
echo    TEMPORAL DEBT - Deployment Helper
echo ========================================
echo.

echo Choose deployment method:
echo [1] Build for Web (Pygbag - Recommended)
echo [2] Build Standalone Executable (PyInstaller)
echo [3] Install deployment tools only
echo [4] Exit
echo.

set /p choice="Enter choice (1-4): "

if "%choice%"=="1" goto web
if "%choice%"=="2" goto exe
if "%choice%"=="3" goto install
if "%choice%"=="4" goto end

echo Invalid choice!
goto end

:install
echo.
echo Installing deployment tools...
pip install pygbag pyinstaller
echo.
echo Tools installed! Run this script again to build.
pause
goto end

:web
echo.
echo Building for web deployment...
echo.

REM Check if pygbag is installed
pip show pygbag >nul 2>&1
if errorlevel 1 (
    echo Pygbag not found. Installing...
    pip install pygbag
)

echo.
echo NOTE: Before building, make sure you've modified src/core/game.py
echo The run() method needs to be changed for web deployment.
echo See DEPLOYMENT_GUIDE.md Section "Step 2: Modify Game Loop"
echo.
set /p continue="Press Enter to continue with build, or Ctrl+C to cancel..."

echo.
echo Building with Pygbag...
pygbag main_web.py

echo.
echo Build complete! Check the build/web directory.
echo To test locally, the server should have started automatically.
echo Open http://localhost:8000 in your browser.
echo.
pause
goto end

:exe
echo.
echo Building standalone executable...
echo.

REM Check if pyinstaller is installed
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
)

echo.
echo Building with PyInstaller...
pyinstaller temporal_debt.spec

echo.
echo Build complete! Check the dist/TemporalDebt.exe file.
echo You can distribute the entire dist folder.
echo.
pause
goto end

:end
echo.
echo Goodbye!
