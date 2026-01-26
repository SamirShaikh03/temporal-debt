#!/bin/bash
# Quick Deployment Script for TEMPORAL DEBT (Linux/Mac)
# This script helps you deploy the game quickly

echo "========================================"
echo "   TEMPORAL DEBT - Deployment Helper"
echo "========================================"
echo ""

echo "Choose deployment method:"
echo "[1] Build for Web (Pygbag - Recommended)"
echo "[2] Build Standalone Executable (PyInstaller)"
echo "[3] Install deployment tools only"
echo "[4] Exit"
echo ""

read -p "Enter choice (1-4): " choice

case $choice in
    1)
        echo ""
        echo "Building for web deployment..."
        echo ""
        
        # Check if pygbag is installed
        if ! pip show pygbag &> /dev/null; then
            echo "Pygbag not found. Installing..."
            pip install pygbag
        fi
        
        echo ""
        echo "NOTE: Before building, make sure you've modified src/core/game.py"
        echo "The run() method needs to be changed for web deployment."
        echo "See DEPLOYMENT_GUIDE.md Section 'Step 2: Modify Game Loop'"
        echo ""
        read -p "Press Enter to continue with build, or Ctrl+C to cancel..."
        
        echo ""
        echo "Building with Pygbag..."
        pygbag main_web.py
        
        echo ""
        echo "Build complete! Check the build/web directory."
        echo "To test locally, the server should have started automatically."
        echo "Open http://localhost:8000 in your browser."
        echo ""
        ;;
        
    2)
        echo ""
        echo "Building standalone executable..."
        echo ""
        
        # Check if pyinstaller is installed
        if ! pip show pyinstaller &> /dev/null; then
            echo "PyInstaller not found. Installing..."
            pip install pyinstaller
        fi
        
        echo ""
        echo "Building with PyInstaller..."
        pyinstaller temporal_debt.spec
        
        echo ""
        echo "Build complete! Check the dist/ directory."
        echo "You can distribute the entire dist folder."
        echo ""
        ;;
        
    3)
        echo ""
        echo "Installing deployment tools..."
        pip install pygbag pyinstaller
        echo ""
        echo "Tools installed! Run this script again to build."
        ;;
        
    4)
        echo "Goodbye!"
        exit 0
        ;;
        
    *)
        echo "Invalid choice!"
        ;;
esac

echo ""
echo "Goodbye!"
