# 🚀 WhatsApp AI Agent - Production Deployment Guide

This guide provides step-by-step instructions for deploying the WhatsApp AI Agent in production environments, with special focus on containerized deployments and cloud platforms like Render.

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Environment Configuration](#environment-configuration)
4. [Docker Deployment](#docker-deployment)
5. [Render.com Deployment](#rendercom-deployment)
6. [Other Cloud Platforms](#other-cloud-platforms)
7. [Production Optimization](#production-optimization)
8. [Monitoring & Maintenance](#monitoring--maintenance)
9. [Troubleshooting](#troubleshooting)

## 🏗️ Architecture Overview

The WhatsApp AI Agent consists of three main components:

```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   WhatsApp Bridge   │    │    MCP Server       │    │   Main AI Agent     │
│   (Go Application)  │◄──►│  (Python FastMCP)   │◄──►│  (Python LangChain) │
│   Port: 3333        │    │   Port: 3334        │    │   Core Logic        │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────────┐
                                              │  Streamlit Dashboard│
                                              │    (Optional)       │
                                              │    Port: 8501       │
                                              └─────────────────────┘
```

### Component Details:

- **WhatsApp Bridge**: Go-based service handling WhatsApp Web connection
- **MCP Server**: Python FastMCP server providing WhatsApp tools/functions
- **Main AI Agent**: Core Python application with LangChain and Gemini integration
- **Dashboard**: Optional Streamlit web interface for monitoring

## ✅ Prerequisites

### Required Software:

- Docker (version 20.10+)
- Docker Compose (version 2.0+)
- Git

### Required API Keys:

- **Google Gemini API Key**: Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
- **SerpAPI Key** (optional): For web search functionality

### System Requirements:

- **Minimum**: 1 CPU, 1GB RAM, 2GB disk space
- **Recommended**: 2 CPU, 2GB RAM, 5GB disk space
- **Ports**: 3333, 3334, 8501 (configurable)

## ⚙️ Environment Configuration

### 1. Create Environment File

```bash
# Copy the example environment file
cp .env.example .env

# Edit with your configuration
nano .env
```

### 2. Required Environment Variables

```env
# ==========================================
# CORE API CONFIGURATION
# ==========================================
GEMINI_API_KEY=your_actual_gemini_api_key_here
SERPAPI_API_KEY=your_serpapi_key_here_optional

# ==========================================
# WHATSAPP MCP CONFIGURATION
# ==========================================
MCP_SERVER_URL=http://localhost:3334
MCP_POLL_INTERVAL=3

# ==========================================
# BOT BEHAVIOR
# ==========================================
BOT_NAME=AI Assistant
BOT_TRIGGERS=!ask,@bot,@ai,>
AUTHORIZED_NUMBERS=
ENABLE_GROUP_CHATS=true
ENABLE_PERSONAL_CHATS=true

# ==========================================
# AGENT SETTINGS
# ==========================================
MAX_RESPONSE_LENGTH=500
AGENT_TEMPERATURE=0.7
AGENT_MODEL=gemini-pro

# ==========================================
# LOGGING
# ==========================================
LOG_LEVEL=INFO
ENABLE_CONSOLE_LOGS=true
ENABLE_FILE_LOGS=true

# ==========================================
# DASHBOARD
# ==========================================
DASHBOARD_PORT=8501
DASHBOARD_HOST=0.0.0.0
```

### 3. Security Considerations

```bash
# Set secure file permissions
chmod 600 .env

# For production, consider using Docker secrets or encrypted environment variables
```

## 🐳 Docker Deployment

### Option 1: Single Container (Recommended for most users)

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd whatsapp-agent

# 2. Create environment file
cp .env.example .env
# Edit .env with your configuration

# 3. Build and run
docker build -t whatsapp-agent .
docker run -d \
  --name whatsapp-agent \
  --env-file .env \
  -p 3333:3333 \
  -p 3334:3334 \
  -p 8501:8501 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/store:/app/store \
  --restart unless-stopped \
  whatsapp-agent
```

### Option 2: Docker Compose (Recommended for development)

```bash
# 1. Start all services
docker-compose up -d

# 2. View logs
docker-compose logs -f

# 3. Stop services
docker-compose down

# 4. Rebuild after code changes
docker-compose build
docker-compose up -d
```

### Option 3: Production Docker Compose

```bash
# Use production configuration
docker-compose -f docker-compose.yml up -d
```

## 🌐 Render.com Deployment

Render is perfect for hosting containerized applications. Here's how to deploy:

### 1. Prepare for Render

Create a `render.yaml` file:

```yaml
services:
  - type: web
    name: whatsapp-ai-agent
    env: docker
    dockerfilePath: ./Dockerfile
    plan: starter # or professional for better performance

    # Environment variables
    envVars:
      - key: GEMINI_API_KEY
        value: your_gemini_api_key
      - key: BOT_NAME
        value: WhatsApp AI Assistant
      - key: LOG_LEVEL
        value: INFO
      - key: MCP_SERVER_URL
        value: http://localhost:3334
      - key: ENABLE_GROUP_CHATS
        value: true
      - key: ENABLE_PERSONAL_CHATS
        value: true

    # Disk for persistent storage
    disk:
      name: whatsapp-data
      mountPath: /app/data
      sizeGB: 1

    # Health check
    healthCheckPath: /health
```

### 2. Deploy to Render

#### Method A: GitHub Integration (Recommended)

1. Push your code to GitHub
2. Connect your GitHub repo to Render
3. Render will automatically build and deploy
4. Set environment variables in Render dashboard

#### Method B: Manual Deployment

```bash
# 1. Install Render CLI
npm install -g @render/cli

# 2. Login to Render
render login

# 3. Deploy
render deploy
```

### 3. Configure Render Environment

In your Render dashboard:

1. Go to your service
2. Navigate to "Environment" tab
3. Add all required environment variables
4. Ensure the following ports are configured:
   - **Primary Port**: 3333 (WhatsApp Bridge)
   - **Internal Services**: 3334 (MCP), 8501 (Dashboard)

### 4. Custom Domains (Optional)

```bash
# Add custom domain in Render dashboard
# Configure DNS to point to your Render service
```

## ☁️ Other Cloud Platforms

### AWS (Elastic Container Service)

```bash
# 1. Build and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
docker tag whatsapp-agent:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/whatsapp-agent:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/whatsapp-agent:latest

# 2. Create ECS task definition
# 3. Create ECS service
# 4. Configure load balancer
```

### Google Cloud (Cloud Run)

```bash
# 1. Build and push to GCR
gcloud builds submit --tag gcr.io/PROJECT-ID/whatsapp-agent

# 2. Deploy to Cloud Run
gcloud run deploy whatsapp-agent \
  --image gcr.io/PROJECT-ID/whatsapp-agent \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 3333 \
  --memory 1Gi \
  --cpu 1
```

### DigitalOcean (App Platform)

```yaml
# .do/app.yaml
name: whatsapp-agent
services:
  - name: web
    source_dir: /
    docker:
      dockerfile_path: Dockerfile
    instance_count: 1
    instance_size_slug: basic-xxs
    envs:
      - key: GEMINI_API_KEY
        value: your_api_key
      - key: LOG_LEVEL
        value: INFO
    health_check:
      http_path: /health
```

## 🚀 Production Optimization

### 1. Container Optimization

```dockerfile
# Multi-stage builds (already implemented)
# Use specific version tags
# Minimize layers
# Use .dockerignore
```

### 2. Resource Management

```yaml
# docker-compose.yml
deploy:
  resources:
    limits:
      memory: 1G
      cpus: "0.5"
    reservations:
      memory: 512M
      cpus: "0.25"
```

### 3. Logging Configuration

```env
# Production logging
LOG_LEVEL=INFO
ENABLE_CONSOLE_LOGS=false
ENABLE_FILE_LOGS=true
```

### 4. Security Hardening

```bash
# Use non-root user (already implemented)
# Scan for vulnerabilities
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image whatsapp-agent:latest

# Update base images regularly
# Use secrets management
```

### 5. Performance Tuning

```env
# Optimize polling intervals
MCP_POLL_INTERVAL=5

# Adjust response limits
MAX_RESPONSE_LENGTH=300

# Fine-tune model parameters
AGENT_TEMPERATURE=0.7
```

## 📊 Monitoring & Maintenance

### 1. Health Checks

```bash
# Check service health
curl http://localhost:3333/health
curl http://localhost:3334/health

# Docker health status
docker ps --format "table {{.Names}}\t{{.Status}}"
```

### 2. Log Management

```bash
# View logs
docker logs whatsapp-agent

# Follow logs
docker logs -f whatsapp-agent

# Container resource usage
docker stats whatsapp-agent
```

### 3. Backup Strategy

```bash
# Backup data directory
tar -czf backup-$(date +%Y%m%d).tar.gz data/ logs/ store/

# Database backup (if using external DB)
# Automated backup scripts
```

### 4. Updates and Maintenance

```bash
# Update the application
git pull origin main
docker-compose build
docker-compose up -d

# Clean up old images
docker image prune -a

# Monitor disk usage
df -h
```

## 🛠️ Troubleshooting

### Common Issues

#### 1. WhatsApp Bridge Connection Failed

```bash
# Check logs
docker logs whatsapp-agent | grep "WhatsApp Bridge"

# Verify QR code scanning
# Check network connectivity
# Ensure proper permissions
```

#### 2. MCP Server Not Starting

```bash
# Check port conflicts
netstat -tulpn | grep :3334

# Verify Python dependencies
# Check environment variables
```

#### 3. Gemini API Issues

```bash
# Verify API key
curl -H "x-goog-api-key: YOUR_API_KEY" \
  https://generativelanguage.googleapis.com/v1/models

# Check quota limits
# Verify model availability
```

#### 4. Resource Issues

```bash
# Check memory usage
free -h

# Check disk space
df -h

# Monitor container resources
docker stats
```

### Debugging Commands

```bash
# Enter container for debugging
docker exec -it whatsapp-agent /bin/bash

# Check process status
docker exec whatsapp-agent ps aux

# Network debugging
docker exec whatsapp-agent netstat -tulpn

# Environment variables
docker exec whatsapp-agent env
```

### Performance Issues

```bash
# Monitor resource usage
docker stats whatsapp-agent

# Analyze logs for bottlenecks
docker logs whatsapp-agent | grep "ERROR\|WARN"

# Database optimization (if applicable)
# Network latency checks
```

## 📞 Support & Documentation

### Additional Resources

- [WhatsApp Web API Documentation](https://github.com/go-whatsapp/whatsmeow)
- [LangChain Documentation](https://python.langchain.com/)
- [Google Gemini API Documentation](https://ai.google.dev/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

### Getting Help

1. Check the logs first
2. Review this deployment guide
3. Check the main README.md
4. Open an issue on GitHub

### Production Checklist

- [ ] Environment variables configured
- [ ] API keys tested and valid
- [ ] Docker images built successfully
- [ ] Health checks passing
- [ ] Logs accessible and monitored
- [ ] Backup strategy implemented
- [ ] Security measures in place
- [ ] Performance optimization applied
- [ ] Documentation updated

---

**🎉 Congratulations!** Your WhatsApp AI Agent should now be running in production. Monitor the logs and health checks to ensure everything is working correctly.
