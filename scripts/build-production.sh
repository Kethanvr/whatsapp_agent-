#!/bin/bash

# WhatsApp AI Agent - Production Build Script
# This script builds optimized Docker images for production deployment

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script configuration
IMAGE_NAME="whatsapp-agent"
IMAGE_TAG="${1:-latest}"
BUILD_ARGS=""
PLATFORMS="linux/amd64,linux/arm64"
PUSH_TO_REGISTRY="${PUSH_TO_REGISTRY:-false}"
REGISTRY_URL="${REGISTRY_URL:-}"

# Functions
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

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    # Check Docker BuildKit
    if ! docker buildx version &> /dev/null; then
        log_error "Docker BuildKit is not available"
        exit 1
    fi
    
    # Check if .env exists
    if [ ! -f ".env" ]; then
        log_warning ".env file not found. Creating from .env.example..."
        if [ -f ".env.example" ]; then
            cp .env.example .env
            log_info "Please edit .env file with your configuration"
        else
            log_error ".env.example not found"
            exit 1
        fi
    fi
    
    log_success "Prerequisites check passed"
}

show_usage() {
    echo "Usage: $0 [IMAGE_TAG] [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  IMAGE_TAG          Docker image tag (default: latest)"
    echo "  --push             Push image to registry"
    echo "  --registry URL     Registry URL for pushing"
    echo "  --multi-platform   Build for multiple platforms"
    echo "  --no-cache         Build without cache"
    echo "  --help             Show this help message"
    echo ""
    echo "Environment variables:"
    echo "  PUSH_TO_REGISTRY   Set to 'true' to push to registry"
    echo "  REGISTRY_URL       Registry URL (e.g., ghcr.io/username)"
    echo ""
    echo "Examples:"
    echo "  $0                          # Build with 'latest' tag"
    echo "  $0 v1.0.0                   # Build with 'v1.0.0' tag"
    echo "  $0 latest --push            # Build and push to registry"
    echo "  $0 latest --multi-platform  # Build for multiple platforms"
}

parse_arguments() {
    while [[ $# -gt 1 ]]; do
        case $2 in
            --push)
                PUSH_TO_REGISTRY="true"
                shift
                ;;
            --registry)
                REGISTRY_URL="$3"
                shift 2
                ;;
            --multi-platform)
                BUILD_ARGS="$BUILD_ARGS --platform $PLATFORMS"
                shift
                ;;
            --no-cache)
                BUILD_ARGS="$BUILD_ARGS --no-cache"
                shift
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $2"
                show_usage
                exit 1
                ;;
        esac
    done
}

create_builder() {
    log_info "Setting up Docker buildx builder..."
    
    # Create builder if it doesn't exist
    if ! docker buildx inspect whatsapp-builder &> /dev/null; then
        docker buildx create --name whatsapp-builder --use
    else
        docker buildx use whatsapp-builder
    fi
    
    # Bootstrap the builder
    docker buildx inspect --bootstrap
    
    log_success "Builder ready"
}

build_image() {
    log_info "Building Docker image: ${IMAGE_NAME}:${IMAGE_TAG}"
    log_info "Build arguments: ${BUILD_ARGS}"
    
    # Determine full image name
    if [ -n "$REGISTRY_URL" ]; then
        FULL_IMAGE_NAME="${REGISTRY_URL}/${IMAGE_NAME}:${IMAGE_TAG}"
    else
        FULL_IMAGE_NAME="${IMAGE_NAME}:${IMAGE_TAG}"
    fi
    
    # Build command
    BUILD_CMD="docker buildx build"
    BUILD_CMD="$BUILD_CMD --tag $FULL_IMAGE_NAME"
    BUILD_CMD="$BUILD_CMD --target production"
    BUILD_CMD="$BUILD_CMD $BUILD_ARGS"
    
    if [ "$PUSH_TO_REGISTRY" = "true" ]; then
        BUILD_CMD="$BUILD_CMD --push"
    else
        BUILD_CMD="$BUILD_CMD --load"
    fi
    
    BUILD_CMD="$BUILD_CMD ."
    
    log_info "Executing: $BUILD_CMD"
    
    # Execute build
    eval $BUILD_CMD
    
    if [ $? -eq 0 ]; then
        log_success "Docker image built successfully: $FULL_IMAGE_NAME"
    else
        log_error "Docker build failed"
        exit 1
    fi
}

scan_image() {
    if [ "$PUSH_TO_REGISTRY" != "true" ]; then
        log_info "Scanning image for vulnerabilities..."
        
        # Try to use trivy if available
        if command -v trivy &> /dev/null; then
            trivy image "${IMAGE_NAME}:${IMAGE_TAG}" || log_warning "Vulnerability scan completed with issues"
        else
            log_warning "Trivy not found. Skipping vulnerability scan."
            log_info "Install trivy for security scanning: https://aquasecurity.github.io/trivy/"
        fi
    fi
}

show_image_info() {
    if [ "$PUSH_TO_REGISTRY" != "true" ]; then
        log_info "Image information:"
        docker images "${IMAGE_NAME}:${IMAGE_TAG}" --format "table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.CreatedAt}}\t{{.Size}}"
        
        log_info "Image layers:"
        docker history "${IMAGE_NAME}:${IMAGE_TAG}" --no-trunc
    fi
}

cleanup() {
    log_info "Cleaning up unused Docker resources..."
    docker system prune -f --filter "until=24h"
    log_success "Cleanup completed"
}

main() {
    echo ""
    log_info "🚀 WhatsApp AI Agent - Production Build"
    echo "=========================================="
    
    # Parse command line arguments
    parse_arguments "$@"
    
    # Run build process
    check_prerequisites
    create_builder
    build_image
    scan_image
    show_image_info
    
    log_success "✅ Build process completed!"
    echo ""
    
    # Show next steps
    log_info "📝 Next steps:"
    if [ "$PUSH_TO_REGISTRY" = "true" ]; then
        echo "   • Image pushed to registry: $FULL_IMAGE_NAME"
        echo "   • Deploy using: docker run -d --env-file .env -p 3333:3333 $FULL_IMAGE_NAME"
    else
        echo "   • Test locally: docker run -d --env-file .env -p 3333:3333 ${IMAGE_NAME}:${IMAGE_TAG}"
        echo "   • Push to registry: docker push ${IMAGE_NAME}:${IMAGE_TAG}"
    fi
    echo "   • Monitor logs: docker logs -f <container_name>"
    echo "   • Access dashboard: http://localhost:8501"
    echo ""
    
    # Optional cleanup
    read -p "Clean up unused Docker resources? [y/N]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cleanup
    fi
}

# Run main function
main "$@" 