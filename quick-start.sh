#!/bin/bash

# WhatsApp AI Agent - Quick Start Script
# This script helps you get up and running quickly

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
PROJECT_NAME="WhatsApp AI Agent"
REQUIRED_DOCKER_VERSION="20.10"
REQUIRED_COMPOSE_VERSION="2.0"

# Functions
print_header() {
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    🤖 WhatsApp AI Agent                     ║"
    echo "║                     Quick Start Setup                       ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

ask_user() {
    local question="$1"
    local default="$2"
    local answer
    
    if [ -n "$default" ]; then
        read -p "$(echo -e ${CYAN}$question ${NC}[${default}]: )" answer
        answer=${answer:-$default}
    else
        read -p "$(echo -e ${CYAN}$question: ${NC})" answer
    fi
    
    echo "$answer"
}

check_command() {
    local cmd="$1"
    local name="$2"
    local install_url="$3"
    
    if command -v "$cmd" &> /dev/null; then
        log_success "$name is installed"
        return 0
    else
        log_error "$name is not installed"
        if [ -n "$install_url" ]; then
            echo "         Install from: $install_url"
        fi
        return 1
    fi
}

check_version() {
    local current="$1"
    local required="$2"
    local name="$3"
    
    if [ "$(printf '%s\n' "$required" "$current" | sort -V | head -n1)" = "$required" ]; then
        log_success "$name version $current is compatible (>= $required)"
        return 0
    else
        log_warning "$name version $current may be incompatible (required >= $required)"
        return 1
    fi
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    local all_good=true
    
    # Check Docker
    if check_command "docker" "Docker" "https://docs.docker.com/get-docker/"; then
        local docker_version=$(docker --version | grep -oE '[0-9]+\.[0-9]+' | head -1)
        check_version "$docker_version" "$REQUIRED_DOCKER_VERSION" "Docker" || all_good=false
    else
        all_good=false
    fi
    
    # Check Docker Compose
    if check_command "docker-compose" "Docker Compose" "https://docs.docker.com/compose/install/"; then
        local compose_version=$(docker-compose --version | grep -oE '[0-9]+\.[0-9]+' | head -1)
        check_version "$compose_version" "$REQUIRED_COMPOSE_VERSION" "Docker Compose" || all_good=false
    else
        all_good=false
    fi
    
    # Check Make (optional)
    check_command "make" "Make (optional)" "https://www.gnu.org/software/make/" || true
    
    if [ "$all_good" = false ]; then
        log_error "Some prerequisites are missing. Please install them and run this script again."
        exit 1
    fi
    
    log_success "All prerequisites are satisfied!"
}

setup_environment() {
    log_info "Setting up environment configuration..."
    
    # Check if .env already exists
    if [ -f ".env" ]; then
        local overwrite=$(ask_user "Environment file (.env) already exists. Overwrite?" "n")
        if [[ ! $overwrite =~ ^[Yy]$ ]]; then
            log_info "Using existing .env file"
            return
        fi
    fi
    
    # Copy from example
    if [ -f ".env.example" ]; then
        cp .env.example .env
        log_success "Created .env from template"
    else
        log_error ".env.example not found. Creating minimal configuration..."
        cat > .env << EOF
# WhatsApp AI Agent Configuration
GEMINI_API_KEY=your_gemini_api_key_here
BOT_NAME=AI Assistant
LOG_LEVEL=INFO
MCP_SERVER_URL=http://localhost:3334
EOF
    fi
    
    # Interactive configuration
    echo ""
    log_info "Let's configure your WhatsApp AI Agent:"
    
    # API Key
    local gemini_key
    while true; do
        gemini_key=$(ask_user "Enter your Google Gemini API key" "")
        if [ -n "$gemini_key" ] && [ "$gemini_key" != "your_gemini_api_key_here" ]; then
            break
        fi
        log_warning "Valid Gemini API key is required. Get one from: https://makersuite.google.com/app/apikey"
    done
    
    # Bot name
    local bot_name=$(ask_user "Bot name" "AI Assistant")
    
    # Bot triggers
    local bot_triggers=$(ask_user "Bot triggers (comma-separated)" "!ask,@bot,@ai,>")
    
    # Group chats
    local enable_groups=$(ask_user "Enable group chats? (y/n)" "y")
    enable_groups=$([ "$enable_groups" = "y" ] && echo "true" || echo "false")
    
    # Personal chats
    local enable_personal=$(ask_user "Enable personal chats? (y/n)" "y")
    enable_personal=$([ "$enable_personal" = "y" ] && echo "true" || echo "false")
    
    # Update .env file
    sed -i.bak "s/GEMINI_API_KEY=.*/GEMINI_API_KEY=$gemini_key/" .env
    sed -i.bak "s/BOT_NAME=.*/BOT_NAME=$bot_name/" .env
    sed -i.bak "s/BOT_TRIGGERS=.*/BOT_TRIGGERS=$bot_triggers/" .env
    sed -i.bak "s/ENABLE_GROUP_CHATS=.*/ENABLE_GROUP_CHATS=$enable_groups/" .env
    sed -i.bak "s/ENABLE_PERSONAL_CHATS=.*/ENABLE_PERSONAL_CHATS=$enable_personal/" .env
    rm -f .env.bak
    
    log_success "Environment configuration completed!"
}

create_directories() {
    log_info "Creating necessary directories..."
    
    mkdir -p data logs store scripts
    
    # Create scripts directory if it doesn't exist
    if [ ! -d "scripts" ]; then
        mkdir -p scripts
    fi
    
    log_success "Directories created!"
}

setup_permissions() {
    log_info "Setting up file permissions..."
    
    # Make scripts executable
    find scripts -name "*.sh" -exec chmod +x {} \; 2>/dev/null || true
    
    # Set .env permissions
    chmod 600 .env
    
    log_success "Permissions configured!"
}

show_deployment_options() {
    echo ""
    log_info "Choose your deployment option:"
    echo ""
    echo "1. Development (docker-compose)"
    echo "2. Production (single container)"
    echo "3. Build only (create Docker image)"
    echo "4. Skip deployment"
    echo ""
    
    local choice=$(ask_user "Select option (1-4)" "1")
    
    case $choice in
        1)
            deploy_development
            ;;
        2)
            deploy_production
            ;;
        3)
            build_only
            ;;
        4)
            log_info "Skipping deployment"
            ;;
        *)
            log_warning "Invalid choice. Defaulting to development deployment."
            deploy_development
            ;;
    esac
}

deploy_development() {
    log_info "Starting development deployment..."
    
    if command -v make &> /dev/null; then
        make dev
    else
        docker-compose up -d
    fi
    
    show_urls
}

deploy_production() {
    log_info "Starting production deployment..."
    
    # Build first
    if command -v make &> /dev/null; then
        make build
        make prod
    else
        docker build -t whatsapp-agent .
        docker run -d \
            --name whatsapp-agent-prod \
            --env-file .env \
            -p 3333:3333 \
            -p 3334:3334 \
            -p 8501:8501 \
            -v $(pwd)/data:/app/data \
            -v $(pwd)/logs:/app/logs \
            -v $(pwd)/store:/app/store \
            --restart unless-stopped \
            whatsapp-agent:latest
    fi
    
    show_urls
}

build_only() {
    log_info "Building Docker image..."
    
    if command -v make &> /dev/null; then
        make build
    else
        docker build -t whatsapp-agent .
    fi
    
    log_success "Docker image built successfully!"
    echo "Run with: docker run -d --env-file .env -p 3333:3333 whatsapp-agent"
}

show_urls() {
    echo ""
    log_success "Deployment completed! 🎉"
    echo ""
    echo -e "${CYAN}Access Points:${NC}"
    echo "• WhatsApp Bridge: http://localhost:3333"
    echo "• MCP Server: http://localhost:3334"
    echo "• Dashboard: http://localhost:8501"
    echo ""
    echo -e "${CYAN}Useful Commands:${NC}"
    if command -v make &> /dev/null; then
        echo "• View logs: make logs"
        echo "• Check health: make health"
        echo "• Stop services: make stop"
        echo "• Show all commands: make help"
    else
        echo "• View logs: docker-compose logs -f"
        echo "• Stop services: docker-compose down"
        echo "• Check status: docker ps"
    fi
    echo ""
    echo -e "${YELLOW}Important Notes:${NC}"
    echo "1. Scan the QR code when prompted to connect WhatsApp"
    echo "2. Check logs if services don't start properly"
    echo "3. Ensure your Gemini API key is valid"
    echo "4. See docs/PRODUCTION_DEPLOYMENT_GUIDE.md for advanced setup"
}

show_help() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --dev      Start development environment only"
    echo "  --prod     Start production environment only"
    echo "  --build    Build Docker image only"
    echo "  --help     Show this help message"
    echo ""
    echo "Interactive mode will run if no options are provided."
}

# Main execution
main() {
    # Parse command line arguments
    case "${1:-}" in
        --dev)
            check_prerequisites
            setup_environment
            create_directories
            setup_permissions
            deploy_development
            ;;
        --prod)
            check_prerequisites
            setup_environment
            create_directories
            setup_permissions
            deploy_production
            ;;
        --build)
            check_prerequisites
            build_only
            ;;
        --help)
            show_help
            exit 0
            ;;
        "")
            # Interactive mode
            print_header
            check_prerequisites
            setup_environment
            create_directories
            setup_permissions
            show_deployment_options
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@" 