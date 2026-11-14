# WhatsApp AI Assistant

A Python service that connects a WhatsApp bridge to an AI message workflow built with Gemini, LangChain, and LangGraph. The repository also includes a Streamlit dashboard and deployment files.

## Components

- `main.py` — starts the assistant process.
- `core/` and `agents/` — message processing and agent workflow.
- `whatsapp-mcp/` and the bridge scripts — WhatsApp connectivity.
- `dashboard/` and `run_dashboard.py` — monitoring and dashboard entry points.
- `docs/` — setup, workflow, troubleshooting, and deployment guides.

## Requirements

- Python and the packages listed in `requirements.txt`
- Docker and Docker Compose for the containerized setup
- WhatsApp bridge access and the provider configuration required by your deployment

## Local setup

Create a virtual environment and install the dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

On Windows, activate the environment with `.venv\Scripts\activate`.

Create a local configuration file from the example and add credentials there:

```bash
cp .env.example .env
```

Set the required values, including `GEMINI_API_KEY`, in `.env`. Keep this file private and do not commit it.

Start the WhatsApp bridge using `./start_whatsapp_bridge.sh` (Windows: `start_whatsapp_bridge.bat`), then start the assistant:

```bash
python main.py
```

To start the dashboard separately:

```bash
python run_dashboard.py
```

For Docker, review the environment and volume settings, then use:

```bash
docker compose up --build
```

## Further documentation

- [Setup guide](docs/SETUP_GUIDE.md)
- [Workflow](docs/WORKFLOW.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Production deployment](docs/PRODUCTION_DEPLOYMENT_GUIDE.md)
