#!/bin/bash
# Quick fix script to rebuild and redeploy with correct architecture

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

APP_NAME="digital-badge-app"
AWS_REGION="${AWS_REGION:-us-east-1}"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "")

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Architecture Fix Script${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""
echo "This script will:"
echo "  1. Rebuild your image for x86_64 (AMD64)"
echo "  2. Push to ECR"
echo "  3. Force ECS to redeploy with new image"
echo ""

if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo -e "${RED}❌ AWS credentials not configured${NC}"
    exit 1
fi

ECR_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$APP_NAME"

echo "Configuration:"
echo "  App Name: $APP_NAME"
echo "  AWS Region: $AWS_REGION"
echo "  ECR URI: $ECR_URI"
echo ""

read -p "Continue? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Cancelled."
    exit 0
fi

# Step 1: Rebuild for x86_64
echo ""
echo -e "${YELLOW}Step 1: Rebuilding image for x86_64 architecture...${NC}"
finch build --platform linux/amd64 -t $APP_NAME:latest .
echo -e "${GREEN}✓ Image built for x86_64${NC}"

# Step 2: Tag and push
echo ""
echo -e "${YELLOW}Step 2: Pushing to ECR...${NC}"

echo "Tagging image..."
finch tag $APP_NAME:latest $ECR_URI:latest

echo "Logging in to ECR..."
aws ecr get-login-password --region $AWS_REGION | \
    finch login --username AWS --password-stdin $ECR_URI

echo "Pushing image..."
finch push $ECR_URI:latest
echo -e "${GREEN}✓ Image pushed to ECR${NC}"

# Step 3: Find and update service
echo ""
echo -e "${YELLOW}Step 3: Updating ECS service...${NC}"

# Find the service
SERVICE_ARN=$(aws ecs list-express-gateway-services --region $AWS_REGION --query 'serviceArns[0]' --output text 2>/dev/null || echo "")

if [ -z "$SERVICE_ARN" ] || [ "$SERVICE_ARN" = "None" ]; then
    echo -e "${RED}❌ No ECS Express Mode service found${NC}"
    echo "The image has been rebuilt and pushed to ECR."
    echo "You can now deploy with: ./deploy-to-ecs-express.sh"
    exit 1
fi

echo "Found service: $SERVICE_ARN"
echo "Forcing new deployment..."

aws ecs update-express-gateway-service \
    --service-arn "$SERVICE_ARN" \
    --region $AWS_REGION \
    --force-new-deployment > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Service update initiated${NC}"
else
    echo -e "${RED}❌ Failed to update service${NC}"
    echo "Try manually with:"
    echo "  aws ecs update-express-gateway-service --service-arn $SERVICE_ARN --force-new-deployment"
    exit 1
fi

# Step 4: Monitor deployment
echo ""
echo -e "${YELLOW}Step 4: Monitoring deployment...${NC}"
echo "Waiting for new tasks to start (this may take 2-3 minutes)..."
echo ""

sleep 30

# Check task status
CLUSTER="default"
TASKS=$(aws ecs list-tasks --cluster $CLUSTER --region $AWS_REGION --query 'taskArns' --output text 2>/dev/null || echo "")

if [ -n "$TASKS" ]; then
    echo "Current tasks:"
    for task in $TASKS; do
        TASK_STATUS=$(aws ecs describe-tasks --cluster $CLUSTER --tasks $task --region $AWS_REGION --query 'tasks[0].lastStatus' --output text 2>/dev/null || echo "UNKNOWN")
        echo "  Task: $(basename $task) - Status: $TASK_STATUS"
    done
else
    echo "  No tasks found yet..."
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Architecture Fix Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next steps:"
echo "  1. Wait 2-3 minutes for new tasks to start"
echo "  2. Check service status:"
echo "     aws ecs describe-express-gateway-service --service-arn $SERVICE_ARN --region $AWS_REGION"
echo ""
echo "  3. View logs:"
echo "     aws logs tail /aws/ecs/express/$APP_NAME --follow --region $AWS_REGION"
echo ""
echo "  4. Test your application:"
echo "     Get the URL from the service description above"
echo ""
echo "If you still see errors, the old tasks may still be running."
echo "Wait a few more minutes for them to be replaced."
echo ""
