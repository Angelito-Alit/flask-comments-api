#!/bin/bash

# Production Deployment Script for Flask Comments API
# This script handles production deployment with validation and rollback capabilities

set -e

# Configuration
SERVICE_NAME="flask-comments-api"
REGION="us-central1"
PROJECT_ID="${GCP_PROJECT_ID}"
IMAGE_TAG="${GITHUB_SHA:-latest}"
REGISTRY_URL="us-central1-docker.pkg.dev"
REPOSITORY="uteq-repositorio"

# Logging functions
log_info() {
    echo "[INFO $(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log_error() {
    echo "[ERROR $(date '+%Y-%m-%d %H:%M:%S')] $1" >&2
}

log_warning() {
    echo "[WARNING $(date '+%Y-%m-%d %H:%M:%S')] $1" >&2
}

# Validation functions
validate_environment() {
    log_info "Validating deployment environment"
    
    if [ -z "$PROJECT_ID" ]; then
        log_error "GCP_PROJECT_ID environment variable is not set"
        exit 1
    fi
    
    if [ -z "$GITHUB_SHA" ]; then
        log_warning "GITHUB_SHA not set, using 'latest' tag"
    fi
    
    log_info "Environment validation completed"
}

# Pre-deployment checks
pre_deployment_checks() {
    log_info "Running pre-deployment checks"
    
    # Check if gcloud is authenticated
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        log_error "No active gcloud authentication found"
        exit 1
    fi
    
    # Verify project exists
    if ! gcloud projects describe "$PROJECT_ID" &>/dev/null; then
        log_error "Project $PROJECT_ID not found or not accessible"
        exit 1
    fi
    
    # Check if Cloud Run service exists
    if gcloud run services describe "$SERVICE_NAME" --region="$REGION" --project="$PROJECT_ID" &>/dev/null; then
        log_info "Existing service found, preparing for update"
    else
        log_info "New service deployment detected"
    fi
    
    log_info "Pre-deployment checks completed successfully"
}

# Deploy to Cloud Run
deploy_service() {
    log_info "Starting deployment to Cloud Run"
    
    local image_url="$REGISTRY_URL/$PROJECT_ID/$REPOSITORY/$SERVICE_NAME:$IMAGE_TAG"
    
    gcloud run deploy "$SERVICE_NAME" \
        --image "$image_url" \
        --platform managed \
        --region "$REGION" \
        --project "$PROJECT_ID" \
        --allow-unauthenticated \
        --port 8080 \
        --memory 512Mi \
        --cpu 1 \
        --timeout 300 \
        --max-instances 10 \
        --min-instances 0 \
        --concurrency 80 \
        --set-env-vars "FLASK_ENV=production,LOG_LEVEL=INFO" \
        --quiet
    
    log_info "Service deployment completed"
}

# Post-deployment validation
post_deployment_validation() {
    log_info "Running post-deployment validation"
    
    # Get service URL
    local service_url
    service_url=$(gcloud run services describe "$SERVICE_NAME" \
        --region="$REGION" \
        --project="$PROJECT_ID" \
        --format="value(status.url)")
    
    if [ -z "$service_url" ]; then
        log_error "Failed to retrieve service URL"
        exit 1
    fi
    
    log_info "Service deployed at: $service_url"
    
    # Wait for service to be ready
    log_info "Waiting for service to become ready"
    sleep 30
    
    # Health check validation
    local health_check_url="$service_url/health"
    local max_attempts=5
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        log_info "Health check attempt $attempt/$max_attempts"
        
        if curl -f -s "$health_check_url" > /dev/null; then
            log_info "Health check passed successfully"
            break
        else
            if [ $attempt -eq $max_attempts ]; then
                log_error "Health check failed after $max_attempts attempts"
                exit 1
            fi
            log_warning "Health check failed, retrying in 10 seconds"
            sleep 10
        fi
        
        attempt=$((attempt + 1))
    done
    
    # API endpoint validation
    local api_response
    api_response=$(curl -s "$service_url" | grep -o '"status":"running"' || echo "")
    
    if [ -n "$api_response" ]; then
        log_info "API endpoint validation successful"
    else
        log_error "API endpoint validation failed"
        exit 1
    fi
    
    log_info "Post-deployment validation completed successfully"
    echo "SERVICE_URL=$service_url" >> "$GITHUB_OUTPUT" 2>/dev/null || true
}

# Rollback function
rollback_deployment() {
    log_error "Deployment failed, initiating rollback"
    
    # Get previous revision
    local previous_revision
    previous_revision=$(gcloud run revisions list \
        --service="$SERVICE_NAME" \
        --region="$REGION" \
        --project="$PROJECT_ID" \
        --filter="status.conditions.type:Ready AND status.conditions.status:True" \
        --sort-by="~metadata.creationTimestamp" \
        --limit=2 \
        --format="value(metadata.name)" | tail -1)
    
    if [ -n "$previous_revision" ]; then
        log_info "Rolling back to revision: $previous_revision"
        gcloud run services update-traffic "$SERVICE_NAME" \
            --to-revisions="$previous_revision=100" \
            --region="$REGION" \
            --project="$PROJECT_ID" \
            --quiet
        log_info "Rollback completed"
    else
        log_warning "No previous revision found for rollback"
    fi
}

# Main deployment workflow
main() {
    log_info "Starting production deployment workflow"
    
    validate_environment
    pre_deployment_checks
    
    # Deploy with error handling
    if deploy_service; then
        post_deployment_validation
        log_info "Production deployment completed successfully"
    else
        rollback_deployment
        exit 1
    fi
}

# Execute main function if script is run directly
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi