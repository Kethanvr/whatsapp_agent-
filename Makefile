# WhatsApp AI Agent - Makefile
# Simplified commands for development and deployment

.PHONY: help build run stop logs clean dev prod deploy health test

# Default target
help: ## Show this help message
	@echo "WhatsApp AI Agent - Available Commands"
	@echo "======================================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

# Development commands
dev: ## Start development environment
	@echo "🚀 Starting development environment..."
	@if [ ! -f .env ]; then cp .env.example .env; echo "⚠️  Please edit .env file with your configuration"; fi
	docker-compose up -d
	@echo "✅ Development environment started"
	@echo "📱 WhatsApp Bridge: http://localhost:3333"
	@echo "🔧 MCP Server: http://localhost:3334"
	@echo "📊 Dashboard: http://localhost:8501"

dev-logs: ## Follow development logs
	docker-compose logs -f

dev-stop: ## Stop development environment
	docker-compose down

dev-restart: ## Restart development environment
	docker-compose restart

# Production build commands
build: ## Build production Docker image
	@echo "🔨 Building production image..."
	@chmod +x scripts/build-production.sh
	@./scripts/build-production.sh

build-no-cache: ## Build production image without cache
	@echo "🔨 Building production image (no cache)..."
	@chmod +x scripts/build-production.sh
	@./scripts/build-production.sh latest --no-cache

build-multi: ## Build for multiple platforms
	@echo "🔨 Building multi-platform image..."
	@chmod +x scripts/build-production.sh
	@./scripts/build-production.sh latest --multi-platform

# Production deployment
prod: ## Run production container locally
	@echo "🚀 Starting production environment..."
	@if [ ! -f .env ]; then cp .env.example .env; echo "⚠️  Please edit .env file with your configuration"; exit 1; fi
	docker run -d \
		--name whatsapp-agent-prod \
		--env-file .env \
		-p 3333:3333 \
		-p 3334:3334 \
		-p 8501:8501 \
		-v $(PWD)/data:/app/data \
		-v $(PWD)/logs:/app/logs \
		-v $(PWD)/store:/app/store \
		--restart unless-stopped \
		whatsapp-agent:latest
	@echo "✅ Production container started"

prod-stop: ## Stop production container
	docker stop whatsapp-agent-prod || true
	docker rm whatsapp-agent-prod || true

prod-logs: ## View production logs
	docker logs -f whatsapp-agent-prod

# Docker management
run: build ## Build and run production container
	$(MAKE) prod

stop: ## Stop all containers
	docker-compose down || true
	$(MAKE) prod-stop

logs: ## Show logs from running containers
	@if docker ps | grep -q whatsapp-agent-prod; then \
		echo "📋 Production logs:"; \
		docker logs --tail=50 whatsapp-agent-prod; \
	elif docker-compose ps | grep -q whatsapp; then \
		echo "📋 Development logs:"; \
		docker-compose logs --tail=50; \
	else \
		echo "❌ No running containers found"; \
	fi

# Health and monitoring
health: ## Check service health
	@echo "🔍 Checking service health..."
	@echo "WhatsApp Bridge:"
	@curl -s http://localhost:3333/health || echo "❌ WhatsApp Bridge not responding"
	@echo "\nMCP Server:"
	@curl -s http://localhost:3334/health || echo "❌ MCP Server not responding"
	@echo "\nDashboard:"
	@curl -s http://localhost:8501/health || echo "❌ Dashboard not responding"

status: ## Show container status
	@echo "📊 Container Status:"
	@docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(whatsapp|NAME)"

stats: ## Show resource usage
	@echo "📈 Resource Usage:"
	@docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"

# Testing and validation
test: ## Run basic tests
	@echo "🧪 Running basic tests..."
	@if [ ! -f .env ]; then echo "❌ .env file required for tests"; exit 1; fi
	@echo "✅ Environment file exists"
	@docker run --rm --env-file .env whatsapp-agent:latest python -c "import config.settings; print('✅ Configuration valid')"

validate-env: ## Validate environment configuration
	@echo "🔍 Validating environment..."
	@if [ ! -f .env ]; then echo "❌ .env file not found"; exit 1; fi
	@grep -q "GEMINI_API_KEY" .env && echo "✅ GEMINI_API_KEY found" || echo "❌ GEMINI_API_KEY missing"
	@grep -q "BOT_NAME" .env && echo "✅ BOT_NAME found" || echo "❌ BOT_NAME missing"

# Cleanup commands
clean: ## Clean up Docker resources
	@echo "🧹 Cleaning up Docker resources..."
	docker system prune -f
	docker volume prune -f
	@echo "✅ Cleanup completed"

clean-all: ## Remove all containers, images, and volumes
	@echo "🗑️  Removing all containers and images..."
	docker-compose down -v --rmi all || true
	docker stop whatsapp-agent-prod || true
	docker rm whatsapp-agent-prod || true
	docker rmi whatsapp-agent:latest || true
	$(MAKE) clean

# Deployment helpers
deploy-render: ## Deploy to Render.com
	@echo "🌐 Deploying to Render..."
	@if [ ! -f render.yaml ]; then echo "❌ render.yaml not found"; exit 1; fi
	@echo "✅ render.yaml found"
	@echo "📝 Push your code to GitHub and connect to Render"
	@echo "🔗 https://render.com"

push-registry: ## Push image to registry
	@echo "📤 Pushing to registry..."
	@chmod +x scripts/build-production.sh
	@./scripts/build-production.sh latest --push

# Quick setup
setup: ## Initial setup for new installations
	@echo "🛠️  Setting up WhatsApp AI Agent..."
	@if [ ! -f .env ]; then cp .env.example .env; echo "📝 Created .env from template"; fi
	@mkdir -p data logs store
	@echo "📁 Created data directories"
	@echo "✅ Setup completed!"
	@echo ""
	@echo "📋 Next steps:"
	@echo "   1. Edit .env file with your Gemini API key"
	@echo "   2. Run 'make dev' to start development environment"
	@echo "   3. Run 'make build' to build production image"

# Environment file management
env-example: ## Show example environment configuration
	@if [ -f .env.example ]; then \
		echo "📄 Example environment configuration:"; \
		cat .env.example; \
	else \
		echo "❌ .env.example not found"; \
	fi

# Documentation
docs: ## Open documentation
	@echo "📚 Documentation available at:"
	@echo "   • Production Deployment: docs/PRODUCTION_DEPLOYMENT_GUIDE.md"
	@echo "   • Architecture: docs/ARCHITECTURE.md"
	@echo "   • Setup Guide: docs/SETUP_GUIDE.md"

# Advanced commands
shell: ## Open shell in running container
	@if docker ps | grep -q whatsapp-agent-prod; then \
		docker exec -it whatsapp-agent-prod /bin/bash; \
	elif docker-compose ps | grep -q whatsapp; then \
		docker-compose exec whatsapp-agent /bin/bash; \
	else \
		echo "❌ No running containers found"; \
	fi

backup: ## Backup data and configuration
	@echo "💾 Creating backup..."
	@tar -czf backup-$(shell date +%Y%m%d-%H%M%S).tar.gz data/ logs/ store/ .env
	@echo "✅ Backup created: backup-$(shell date +%Y%m%d-%H%M%S).tar.gz"

restore: ## Restore from backup (specify BACKUP_FILE)
	@if [ -z "$(BACKUP_FILE)" ]; then echo "❌ Usage: make restore BACKUP_FILE=backup-file.tar.gz"; exit 1; fi
	@echo "📦 Restoring from $(BACKUP_FILE)..."
	@tar -xzf $(BACKUP_FILE)
	@echo "✅ Restore completed" 