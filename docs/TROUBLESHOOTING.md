# í´§ Troubleshooting Guide

## Quick Diagnostics

### System Health Check
```bash
# Check if all services are running
curl http://localhost:3334/health  # WhatsApp Bridge
curl http://localhost:8503         # Dashboard (if running)

# Check Python dependencies
python -c "from agents.orchestrator import AgentOrchestrator; print('âœ… Orchestrator OK')"
python -c "from core.ai_agent import ai_agent; print('âœ… AI Agent OK')"
```

## Common Issues & Solutions

### 1. WhatsApp Bridge Issues

**Issue**: `Cannot connect to WhatsApp MCP server`
```bash
# Solution: Start the bridge
./start_whatsapp_bridge.sh

# Check if running
curl http://localhost:3334/health

# Should return: {"status": "ok"}
```

**Issue**: `QR code not showing`
```bash
# Kill existing bridge process
pkill -f "whatsapp-bridge"

# Restart bridge
cd whatsapp-mcp/whatsapp-bridge
go run main.go
```

### 2. AI Agent Issues

**Issue**: `Unknown field for Part: thought`
- **Cause**: Gemini 2.0+ models have thinking mode enabled
- **Solution**: Already fixed in our code with direct GenAI API

**Issue**: `Simple response generation failed`
```bash
# Check environment variable
echo $AGENT_MODEL

# Should be: gemini-2.0-flash
# If not, run:
export AGENT_MODEL=gemini-2.0-flash
```

### 3. Trigger Issues

**Issue**: Bot not responding to triggers
```bash
# Check triggers in .env
grep BOT_TRIGGERS .env

# Should show: BOT_TRIGGERS=!ask,@bot,@ai,>
# Test with: !ask Hello
```

**Issue**: Authorization errors
```bash
# Allow all numbers (for testing)
# In .env file:
AUTHORIZED_NUMBERS=

# Or add your number:
AUTHORIZED_NUMBERS=+1234567890
```

### 4. Dashboard Issues

**Issue**: Dashboard won't start
```bash
# Install Streamlit
pip install streamlit

# Start dashboard
python run_dashboard.py

# Should show: http://localhost:8503
```

**Issue**: Dashboard shows "Bridge Offline"
```bash
# Ensure bridge is running first
./start_whatsapp_bridge.sh

# Wait for: "âœ“ Connected to WhatsApp!"
# Then start dashboard
```

### 5. Message Processing Issues

**Issue**: Messages not being processed
```bash
# Check logs
tail -f logs/whatsapp_ai_*.log

# Look for polling messages:
# "í³¨ Found X new message(s)"
```

**Issue**: Agent confidence errors
```bash
# Test orchestrator
python -c "
from agents.orchestrator import AgentOrchestrator
orch = AgentOrchestrator()
agent, conf = orch._select_best_agent('test')
print(f'Agent: {agent}, Confidence: {conf}')
"
```

## Environment Issues

### Python Environment
```bash
# Check Python version
python --version  # Should be 3.10+

# Check virtual environment
which python     # Should show venv path

# Reinstall dependencies
pip install -r requirements.txt
```

### Go Environment
```bash
# Check Go version
go version       # Should be 1.19+

# Clean Go modules (if issues)
cd whatsapp-mcp/whatsapp-bridge
go mod tidy
go clean -cache
```

## Port Conflicts

### Check Port Usage
```bash
# Check if ports are in use
netstat -ano | findstr :3334  # Windows
lsof -i :3334                 # Linux/Mac

# Kill process if needed
taskkill /PID [PID] /F        # Windows
kill -9 [PID]                 # Linux/Mac
```

### Default Ports
- **WhatsApp Bridge**: 3334
- **Streamlit Dashboard**: 8503
- **External Agents**: 8081, 8082, 8083+

## Configuration Issues

### Check Environment Variables
```bash
# Essential variables
echo $GEMINI_API_KEY     # Should have your API key
echo $AGENT_MODEL        # Should be gemini-2.0-flash
echo $MCP_SERVER_URL     # Should be http://localhost:3334
```

### Validate Configuration
```bash
python -c "
from config.settings import settings
print(f'Model: {settings.agent_model}')
print(f'Triggers: {settings.trigger_list}')
print(f'Server: {settings.mcp_server_url}')
"
```

## Performance Issues

### Memory Usage
```bash
# Check system resources
ps aux | grep python         # Python processes
ps aux | grep whatsapp       # Go bridge process

# Restart if memory issues
pkill -f "python main.py"
python main.py
```

### Response Time
```bash
# Test direct agent response
python -c "
import asyncio
from agents.qna_agent import QnAAgent
from agents.base_agent import AgentRequest

async def test():
    config = {'id': 'test', 'name': 'Test'}
    agent = QnAAgent(config)
    req = AgentRequest(message='Hello', session_id='test')
    resp = await agent.process(req)
    print(f'Success: {resp.success}')

asyncio.run(test())
"
```

## Reset Instructions

### Complete System Reset
```bash
# Stop all processes
pkill -f "python main.py"
pkill -f "streamlit"
pkill -f "whatsapp-bridge"

# Clear logs
rm -f logs/*.log

# Restart services
./start_whatsapp_bridge.sh &
sleep 5
python main.py
```

### Agent Registry Reset
```bash
# Backup current registry
cp agents/registry.json agents/registry.json.backup

# Reset to default Q&A agent only
# Edit agents/registry.json to remove problematic agents
```

## Getting Help

### Debug Information
```bash
# Collect debug info
echo "=== System Info ==="
python --version
go version
echo $AGENT_MODEL

echo "=== Service Status ==="
curl -s http://localhost:3334/health || echo "Bridge offline"
curl -s http://localhost:8503 >/dev/null && echo "Dashboard online" || echo "Dashboard offline"

echo "=== Recent Logs ==="
tail -20 logs/whatsapp_ai_*.log
```

### Log Locations
- **Main logs**: `logs/whatsapp_ai_YYYY-MM-DD.log`
- **Console output**: Terminal where you ran `python main.py`
- **Bridge logs**: Terminal where you ran `./start_whatsapp_bridge.sh`

### Common Success Indicators
- âœ… `Connected to WhatsApp MCP server`
- âœ… `Multi-agent orchestrator initialized`
- âœ… `í³¨ Found X new message(s)`
- âœ… `âœ… Response sent successfully`

If none of these solutions work, check the detailed logs and ensure all prerequisites are installed correctly.
