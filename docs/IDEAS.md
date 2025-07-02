# 💡 Ideas & Improvements – GitHub MCP Integration

> This page is a scratch-pad for enhancements around the **GitHub MCP Agent** and memory services. Feel free to extend, cross-out, or add new ideas!

---

## 1. Zero-Setup GitHub MCP Server (Docker)

Below is a _one-liner_ that launches the official GitHub MCP server container. It only needs your **GitHub Personal Access Token (PAT)**.

```bash
# .env (do **NOT** commit this!)
GITHUB_PAT=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Run container
docker run -it --rm \
  -e GITHUB_PERSONAL_ACCESS_TOKEN=${GITHUB_PAT} \
  -p 8085:8080 \
  ghcr.io/github/github-mcp-server
```

Notes:

1. We map container port `8080` to host `8085` (matches `mcp_url` in `agents/registry.json`).
2. Use an **environment variable** – never hard-code or commit the token.
3. Token needs `repo`, `workflow`, `issues`, `pull_requests` scopes.

### Optional: Docker Compose

```yaml
services:
  github-mcp:
    image: ghcr.io/github/github-mcp-server:latest
    environment:
      - GITHUB_PERSONAL_ACCESS_TOKEN=${GITHUB_PAT}
    ports:
      - "8085:8080"
    restart: unless-stopped
```

Run with `docker compose up -d github-mcp`.

---

## 2. Auto-Launch from Python (helper script)

Add a helper that checks if the server is reachable and, if not, spawns the container programmatically:

```python
import os, subprocess, httpx

def ensure_github_mcp():
    try:
        httpx.get("http://localhost:8085/health", timeout=3)
        return True  # Already running
    except Exception:
        token = os.getenv("GITHUB_PAT")
        if not token:
            raise RuntimeError("`GITHUB_PAT` env var not set")
        cmd = [
            "docker", "run", "-d", "--rm",
            "-e", f"GITHUB_PERSONAL_ACCESS_TOKEN={token}",
            "-p", "8085:8080",
            "ghcr.io/github/github-mcp-server:latest",
        ]
        subprocess.check_call(cmd)
        return False  # Started new instance
```

Call this at startup **before** the orchestrator initialises agents.

---

## 3. Expanding the GitHub MCP Agent

| Feature           | Idea                                                  | Notes                                |
| ----------------- | ----------------------------------------------------- | ------------------------------------ |
| Repository search | Expose `search.repos` tool                            | Allow `!ask search repo lang:python` |
| Issue summariser  | Use memory agent to store summaries                   | Cache triage context                 |
| Workflow trigger  | Map `deploy`, `build` keywords to `workflow.dispatch` | GitHub Actions integration           |
| PR reviewer       | Chain Q&A agent for review comments                   | Requires diff retrieval              |

---

## 4. Memory Server Ideas

1. **TTL Memories** – allow transient memories with expiry (e.g. 24 h).
2. **Vector Embeddings** – add semantic search using embeddings for recall.
3. **Memory Categories** – personal, project, global – route accordingly.

---

## 5. Security Best-Practices

- Store PAT in `.env` or Docker secrets.
- Rotate tokens regularly.
- Restrict scopes to minimal required.

---

## 6. Open Questions

1. Should we fallback to GitHub REST API if MCP server down?
2. Rate-limit GitHub operations to avoid PAT abuse?
3. UI component in Streamlit dashboard for GitHub actions?

---

Add your thoughts below! ✍️
