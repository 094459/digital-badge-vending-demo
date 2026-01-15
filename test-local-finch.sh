#!/bin/bash
# Test Digital Badge Platform locally with Finch
# This script builds and runs the container locally for testing

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

APP_NAME="digital-badge-app"
PORT=8080

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Local Finch Test Script${NC}"
echo -e "${GREEN}Digital Badge Platform${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if Finch is installed
if ! command -v finch &> /dev/null; then
    echo -e "${RED}❌ Finch not found. Please install it first.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Finch installed${NC}"

# Stop and remove existing container if running
echo ""
echo -e "${YELLOW}Cleaning up existing containers...${NC}"
finch stop $APP_NAME 2>/dev/null || true
finch rm $APP_NAME 2>/dev/null || true
echo -e "${GREEN}✓ Cleanup complete${NC}"

# Build the image
echo ""
echo -e "${YELLOW}Building container image for x86_64 architecture...${NC}"
finch build --platform linux/amd64 -t $APP_NAME:latest .
echo -e "${GREEN}✓ Image built successfully${NC}"

# Run the container
echo ""
echo -e "${YELLOW}Starting container...${NC}"

# Check if AWS credentials are available
if [ -z "$AWS_ACCESS_KEY_ID" ] && [ ! -f ~/.aws/credentials ]; then
    echo -e "${YELLOW}⚠️  Warning: No AWS credentials found in environment or ~/.aws/credentials${NC}"
    echo -e "${YELLOW}   The container will start but AWS Bedrock calls will fail.${NC}"
    echo ""
fi

# Prepare AWS credential arguments
AWS_CRED_ARGS=""
if [ -n "$AWS_ACCESS_KEY_ID" ]; then
    echo -e "${GREEN}✓ Using AWS credentials from environment variables${NC}"
    AWS_CRED_ARGS="-e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY"
    if [ -n "$AWS_SESSION_TOKEN" ]; then
        AWS_CRED_ARGS="$AWS_CRED_ARGS -e AWS_SESSION_TOKEN=$AWS_SESSION_TOKEN"
    fi
elif [ -f ~/.aws/credentials ]; then
    echo -e "${GREEN}✓ Mounting AWS credentials from ~/.aws${NC}"
    AWS_CRED_ARGS="-v $HOME/.aws:/root/.aws:ro"
fi

finch run -d \
    --name $APP_NAME \
    -p $PORT:8080 \
    -e SECRET_KEY=test-secret-key \
    -e ADMIN_PASSWORD=admin123 \
    -e AWS_REGION=us-east-1 \
    -e BEDROCK_REGION=us-east-1 \
    -e BASE_URL=http://localhost:$PORT \
    -e FLASK_ENV=development \
    $AWS_CRED_ARGS \
    $APP_NAME:latest

echo -e "${GREEN}✓ Container started${NC}"

# Wait for application to start
echo ""
echo -e "${YELLOW}Waiting for application to start...${NC}"
sleep 5

# Test health endpoint
echo ""
echo -e "${YELLOW}Testing health endpoint...${NC}"
HEALTH_RESPONSE=$(curl -s http://localhost:$PORT/health)
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo -e "${GREEN}✓ Health check passed${NC}"
    echo "Response: $HEALTH_RESPONSE"
else
    echo -e "${RED}❌ Health check failed${NC}"
    echo "Response: $HEALTH_RESPONSE"
    echo ""
    echo "Container logs:"
    finch logs $APP_NAME
    exit 1
fi

# Test home page
echo ""
echo -e "${YELLOW}Testing home page...${NC}"
HOME_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$PORT/)
if [ "$HOME_STATUS" = "200" ]; then
    echo -e "${GREEN}✓ Home page accessible (HTTP $HOME_STATUS)${NC}"
else
    echo -e "${RED}❌ Home page failed (HTTP $HOME_STATUS)${NC}"
fi

# Test badge creation
echo ""
echo -e "${YELLOW}Testing badge creation API...${NC}"
BADGE_RESPONSE=$(curl -s -X POST http://localhost:$PORT/api/badges \
    -H "Content-Type: application/json" \
    -d '{"recipient_name": "Test User", "recipient_email": "test@example.com"}')

if echo "$BADGE_RESPONSE" | grep -q "uuid"; then
    echo -e "${GREEN}✓ Badge creation successful${NC}"
    echo "Response: $BADGE_RESPONSE"
else
    echo -e "${RED}❌ Badge creation failed${NC}"
    echo "Response: $BADGE_RESPONSE"
fi

# Show container logs
echo ""
echo -e "${YELLOW}Recent container logs:${NC}"
finch logs --tail 20 $APP_NAME

# Summary
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✓ Local Testing Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Application is running at:"
echo -e "${GREEN}http://localhost:$PORT${NC}"
echo ""
echo "Endpoints:"
echo "  Home:        http://localhost:$PORT/"
echo "  Health:      http://localhost:$PORT/health"
echo "  Admin:       http://localhost:$PORT/admin"
echo "  API Docs:    http://localhost:$PORT/api/badges"
echo ""
echo "To view logs:"
echo "  finch logs -f $APP_NAME"
echo ""
echo "To stop the container:"
echo "  finch stop $APP_NAME"
echo ""
echo "To remove the container:"
echo "  finch rm $APP_NAME"
echo ""
