# í·ª Tests Directory

This directory contains test scripts for the WhatsApp AI Assistant system.

## Test Scripts

### `test_orchestrator.py`
Tests the multi-agent orchestrator system:
- Agent initialization
- Confidence scoring
- Message routing
- Response generation

**Usage:**
```bash
python tests/test_orchestrator.py
```

### `quick_test_send.py`
Tests the complete WhatsApp integration:
- Bridge connection
- WhatsApp authentication
- Contact retrieval  
- AI agent functionality
- Message sending

**Usage:**
```bash
python tests/quick_test_send.py
```

## Running All Tests

```bash
# Test orchestrator
python tests/test_orchestrator.py

# Test WhatsApp integration
python tests/quick_test_send.py

# Test individual components
python -c "from agents.qna_agent import QnAAgent; print('âœ… QnA Agent OK')"
python -c "from core.ai_agent import ai_agent; print('âœ… AI Agent OK')"
```

## Health Checks

```bash
# Check bridge
curl http://localhost:3334/health

# Check dashboard  
curl http://localhost:8503
```
