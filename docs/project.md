# 🤖 WhatsApp AI Assistant – Powered by Gemini + LangGraph + WhatsApp-MCP

## 📌 Overview

This project is a custom AI-powered assistant that connects your personal WhatsApp (via [whatsapp-mcp](https://github.com/lharries/whatsapp-mcp)) with a local LangGraph + LangChain agent running on Gemini. The agent reads WhatsApp messages, sends them to Gemini for smart QnA responses, and replies back on WhatsApp — all without needing the official WhatsApp Business API.

---

## 🧱 Tech Stack

| Layer            | Tool/Framework                                           | Purpose                                       |
| ---------------- | -------------------------------------------------------- | --------------------------------------------- |
| Messaging Bridge | [whatsapp-mcp](https://github.com/lharries/whatsapp-mcp) | Exposes WhatsApp Web interface via local API  |
| LLM Agent        | LangChain + LangGraph                                    | Processes incoming text and generates replies |
| LLM Backend      | Gemini (via API Key)                                     | Handles question-answering via Google's LLM   |
| Server           | Python 3.10+, FastAPI (optional)                         | Runs polling and message routing loop         |

---

## ✅ Features

* 🔁 Polls WhatsApp chats for incoming messages
* 🧠 Sends user messages to Gemini LLM via LangChain
* 💬 Sends generated response back via WhatsApp-MCP
* 🧾 Lightweight memory + context handling
* 🔒 Fully local — no cloud WhatsApp API needed

---

## 🚀 Setup Guide

### 1. 📦 Clone the Repos

```bash
git clone https://github.com/lharries/whatsapp-mcp.git
cd whatsapp-mcp
```

### 2. ▶️ Run WhatsApp-MCP Server

```bash
go run .
```

Scan the QR code from your mobile WhatsApp. You’re now linked.

---

### 3. 🧠 Set Up Your AI Agent (Python)

```bash
mkdir whatsapp-ai-agent
cd whatsapp-ai-agent
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
```

Install dependencies:

```bash
pip install langchain langgraph langchain-google-genai requests python-dotenv
```

Create `.env`:

```env
GEMINI_API_KEY=your-google-api-key
MCP_SERVER=http://localhost:3333
```

---

### 4. 🧩 Agent Logic (main.py)

```python
import os, time, requests
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()
MCP = os.getenv("MCP_SERVER")
llm = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=os.getenv("GEMINI_API_KEY"))

def get_last_message():
    res = requests.get(f"{MCP}/chats")
    chat_id = res.json()[0]['id']
    msg = requests.get(f"{MCP}/messages/{chat_id}").json()[-1]
    return chat_id, msg['text']

def send_reply(chat_id, text):
    requests.post(f"{MCP}/send_message", json={"chat_id": chat_id, "message": text})

while True:
    try:
        chat_id, msg = get_last_message()
        response = llm.invoke(msg)
        send_reply(chat_id, response)
    except Exception as e:
        print("[!] Error:", e)
    time.sleep(5)
```

---

## 🛠️ Improvements (Next Steps)

* 🗣️ Add Whisper/ElevenLabs for voice note transcription + TTS
* 🧠 Integrate LangChain memory for conversation flow
* 📁 Use Pinecone/Chroma for custom knowledge base
* 🔌 Add LangGraph-style modular flows (intent, route, respond)
* ⚙️ Replace polling with webhook if future support added

---

## 📄 MCP Endpoints Used

* `GET /chats`
* `GET /messages/{chat_id}`
* `POST /send_message`
* (Optional) `POST /send_audio`, `GET /download_media`

---

## 🤝 Credits

* [Luke Harries](https://github.com/lharries) – for whatsapp-mcp
* Google Gemini team – LLM API
* LangChain + LangGraph – agent frameworks

---

## 💬 Final Words

This is the cleanest way to run your own WhatsApp AI agent using **your personal number** without Meta’s limitations. It’s modular, scalable, and fully under your control. Let’s ship it 🚀
