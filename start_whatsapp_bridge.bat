@echo off
echo 🚀 Starting WhatsApp Bridge for AI Assistant...
echo ==============================================

:: Check if Go is installed
go version >nul 2>&1
if errorlevel 1 (
    echo ❌ Go is not installed or not in PATH
    echo 💡 Download from: https://golang.org/dl/
    pause
    exit /b 1
)

echo ✅ Go found: 
go version

:: Navigate to whatsapp-bridge directory
set BRIDGE_DIR=whatsapp-mcp\whatsapp-bridge

if not exist "%BRIDGE_DIR%" (
    echo ❌ WhatsApp bridge directory not found: %BRIDGE_DIR%
    echo 💡 Make sure you're running this from the project root
    pause
    exit /b 1
)

cd "%BRIDGE_DIR%"

echo 🔄 Setting up environment for Windows...

:: Set CGO environment variables
set CGO_ENABLED=1
set CC=gcc
set CXX=g++

echo 🔄 Starting WhatsApp bridge...
echo 📱 On first run, scan the QR code with your WhatsApp app
echo 🌐 Bridge will run on http://localhost:3333
echo ==============================================

:: Try to run with error handling
go run main.go
if errorlevel 1 (
    echo.
    echo ❌ Failed to start WhatsApp bridge
    echo.
    echo 💡 Common fixes for Windows CGO errors:
    echo    1. Install TDM-GCC: https://jmeubank.github.io/tdm-gcc/
    echo    2. Install w64devkit: https://github.com/skeeto/w64devkit/releases
    echo    3. Install Visual Studio Build Tools
    echo    4. Use WSL2 ^(Windows Subsystem for Linux^):
    echo       - Run: wsl --install
    echo       - Inside WSL: sudo apt install golang-go
    echo    5. Try running: set CGO_ENABLED=0 ^& go run main.go
    echo.
    pause
    exit /b 1
)

pause 