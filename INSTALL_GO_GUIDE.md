# 🚀 Go Installation Guide for WhatsApp AI Assistant

## Quick Installation Steps

### Method 1: Download Official Installer (Easiest)

1. **Download Go for Windows:**

   - Visit: https://golang.org/dl/
   - Download: `go1.24.4.windows-amd64.msi` (latest stable)

2. **Install:**

   - Run the `.msi` file as Administrator
   - Follow the installation wizard
   - Default install location: `C:\Program Files\Go`

3. **Verify Installation:**
   ```bash
   # Close and reopen your terminal, then run:
   go version
   ```

### Method 2: Using Chocolatey (Admin Required)

```powershell
# Open PowerShell as Administrator and run:
choco install golang -y
```

### Method 3: Manual ZIP Installation (No Admin)

1. Download: `go1.24.4.windows-amd64.zip`
2. Extract to: `C:\go` (or any folder you prefer)
3. Add to PATH:
   - Open System Properties → Environment Variables
   - Add `C:\go\bin` to your PATH variable

## After Installing Go

1. **Verify Go is working:**

   ```bash
   go version
   # Should show: go version go1.24.4 windows/amd64
   ```

2. **Start the WhatsApp Bridge:**

   ```bash
   # In your project directory:
   ./start_whatsapp_bridge.sh
   ```

3. **Start the AI Assistant:**
   ```bash
   # In a new terminal:
   python main.py
   ```

## Testing the Complete Setup

```bash
# Test 1: Check Go
go version

# Test 2: Start WhatsApp Bridge (Terminal 1)
./start_whatsapp_bridge.sh

# Test 3: Start AI Assistant (Terminal 2)
python main.py

# Test 4: Launch Dashboard (Terminal 3)
python run_dashboard.py
```

## Troubleshooting

- **"go: command not found"** → Restart terminal after installation
- **Port 3333 busy** → Kill existing processes: `netstat -ano | findstr 3333`
- **Permission denied** → Run terminal as Administrator
