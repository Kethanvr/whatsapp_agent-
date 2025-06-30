# 📖 WhatsApp-MCP Usage & Integration Guide

> Companion notes for the **WhatsApp AI Assistant** project – how to talk to the bot directly from WhatsApp chats, how the modified `whatsapp-mcp` bridge exposes a REST surface, and where we can take this in an **Agent-to-Agent (A2A)** future.

---

## 1. Talking to the AI from WhatsApp

1. **Configure a trigger.** In your `.env` (or `config/settings.py`) set

   ```env
   BOT_TRIGGERS=/ask,@askai,!ai,>  # add as many comma-separated triggers as you like
   ```

2. **Send the message in WhatsApp.** Examples:

   ```
   /ask Summarise the latest AI news in 3 bullets
   @askai Translate "Hello" to French
   !ai What are MCP servers?
   > Give me a dad joke about Go programmers
   ```

3. **What happens under the hood?**
   - The bridge receives your chat message → persists it in SQLite.
   - `whatsapp_client.get_new_messages()` polls `/messages/{chat}` every few seconds.
   - `message_processor` checks the text; if it starts with any trigger it extracts the query and passes it to `ai_agent`.
   - The AI reply is posted back with `POST /api/send`.
   - The Streamlit dashboard simultaneously shows the new incoming message **and** the generated response (Recent Messages tab).

If the dashboard is **offline** the trigger still works – the CLI loop in `main.py` keeps polling and replying.

---

## 2. REST endpoints exposed by the modified bridge

| Method | Path                          | Purpose                                                   | Sample `curl`                                                                                          |
| ------ | ----------------------------- | --------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| GET    | `/health`                     | Liveness check                                            | `curl http://localhost:3334/health`                                                                    |
| GET    | `/chats`                      | List chats ordered by last message                        | `curl http://localhost:3334/chats`                                                                     |
| GET    | `/messages/{chatID}?limit=20` | Fetch last _n_ messages of a chat                         | `curl http://localhost:3334/messages/12345@s.whatsapp.net?limit=5`                                     |
| POST   | `/api/send`                   | Send text or media (`recipient`, `message`, `media_path`) | `curl -X POST -d '{"recipient":"12345@s.whatsapp.net","message":"Hi"}' http://localhost:3334/api/send` |
| POST   | `/send_message`               | Simpler alias (`chat_id`, `message`) – **text only**      | `curl -X POST -d '{"chat_id":"...","message":"..."}' http://localhost:3334/send_message`               |
| POST   | `/api/download`               | Download media: `message_id`, `chat_jid`                  | `curl -X POST -d '{"message_id":"ABCD","chat_jid":"..."}' http://localhost:3334/api/download`          |

> NOTE: The original upstream [`whatsapp-mcp`](https://github.com/lharries/whatsapp-mcp) also exposed `/status`, `/qr`, etc. We replaced them with a leaner set; feel free to add them back – the Go file is self-contained around lines 650-900.

---

## 3. Extending the workflow towards A2A (Agent-to-Agent) Protocol

| Layer            | Today                               | Tomorrow (A2A vision)                                                      |
| ---------------- | ----------------------------------- | -------------------------------------------------------------------------- |
| Transport        | HTTP REST on localhost 3334         | gRPC / WebSocket / NATS for full-duplex agent streams                      |
| Identity         | WhatsApp JID & phone number         | Decentralised DID + capability tokens                                      |
| Message Envelope | Plain JSON (`recipient`, `message`) | Signed/hashed envelope (e.g. JOSE, SDS) + metadata (trace ID, TTL, schema) |
| Orchestration    | Polling loop                        | Event-driven – agents subscribe to topics (`assistant.response`)           |
| Skills           | Single Gemini completion            | Tool-calling graph where agents negotiate and delegate tasks               |

### Recommended next steps

1. **Swap polling for webhooks.** The bridge already emits events via Whatsmeow; expose them as Server-Sent Events or WebSockets so agents receive pushes.
2. **Define a minimal _A2A JSON schema_.** Start with `{id, sender, recipient, content, metadata}` to future-proof.
3. **Add authentication.** A simple HMAC shared secret on `/api/send` is enough for dev boxes; later migrate to OAuth2-style bearer tokens.
4. **Version your endpoints.** Move everything under `/v1/` before external clients integrate.

---

## 4. Reference links

- WhatsApp MCP fork <https://github.com/lharries/whatsapp-mcp>
- Whatsmeow library <https://github.com/tulir/whatsmeow>
- Project repository <https://github.com/your-org/whatsapp-ai-assistant>

---

Happy hacking! For issues or ideas open a discussion in the repo.
