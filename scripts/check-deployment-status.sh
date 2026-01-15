#!/bin/bash
# Check the status of ECS Express Mode deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

APP_NAME="digital-badge-app"
AWS_REGION="${AWS_REGION:-us-east-1}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}ECS Deployment Status Check${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check for Express Mode services
echo -e "${YELLOW}1. Checking for Express Mode services...${NC}"
SERVICES=$(aws ecs list-express-gateway-services --region $AWS_REGION --query 'serviceArns[]' --output text 2>&1)

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to list services${NC}"
    echo "$SERVICES"
    exit 1
fi

if [ -z "$SERVICES" ]; then
    echo -e "${YELLOW}  ⚠ No Express Mode services found${NC}"
    echo ""
    echo "This means the service was not created. Possible reasons:"
    echo "  1. The create-express-gateway-service command failed"
    echo "  2. Service was created in a different region"
    echo "  3. Service was deleted"
    echo ""
    echo "Check the deployment script output for errors."
    exit 1
fi

echo -e "${GREEN}  ✓ Found Express Mode services:${NC}"
for arn in $SERVICES; do
    echo "    - $arn"
done
echo ""

# Find our service
echo -e "${YELLOW}2. Looking for service: $APP_NAME${NC}"
SERVICE_ARN=""
for arn in $SERVICES; do
    SERVICE_NAME=$(aws ecs describe-express-gateway-service --service-arn "$arn" --region $AWS_REGION --query 'service.serviceName' --output text 2>/dev/null || echo "")
    if [ "$SERVICE_NAME" = "$APP_NAME" ]; then
        SERVICE_ARN="$arn"
        break
    fi
done

if [ -z "$SERVICE_ARN" ]; then
    echo -e "${RED}  ❌ Service '$APP_NAME' not found${NC}"
    echo ""
    echo "Available services:"
    for arn in $SERVICES; do
        NAME=$(aws ecs describe-express-gateway-service --service-arn "$arn" --region $AWS_REGION --query 'service.serviceName' --output text 2>/dev/null || echo "unknown")
        echo "  - $NAME"
    done
    exit 1
fi

echo -e "${GREEN}  ✓ Found service: $SERVICE_ARN${NC}"
echo ""

# Get service details
echo -e "${YELLOW}3. Getting service details...${NC}"
SERVICE_DETAILS=$(aws ecs describe-express-gateway-service --service-arn "$SERVICE_ARN" --region $AWS_REGION 2>&1)

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to get service details${NC}"
    echo "$SERVICE_DETAILS"
    exit 1
fi

# Parse service details
STATUS=$(echo "$SERVICE_DETAILS" | grep -o '"statusCode": "[^"]*"' | head -1 | cut -d'"' -f4)
CREATED_AT=$(echo "$SERVICE_DETAILS" | grep -o '"createdAt": [0-9]*' | head -1 | awk '{print $2}')
CLUSTER=$(echo "$SERVICE_DETAILS" | grep -o '"cluster": "[^"]*"' | head -1 | cut -d'"' -f4)

echo "  Service Name: $APP_NAME"
echo "  Status: $STATUS"
echo "  Cluster: $CLUSTER"
if [ -n "$CREATED_AT" ]; then
    echo "  Created: $(date -r $CREATED_AT 2>/dev/null || echo $CREATED_AT)"
fi
echo ""

# Check for service URL
echo -e "${YELLOW}4. Checking for service URL...${NC}"
SERVICE_URL=$(echo "$SERVICE_DETAILS" | grep -o 'https://[^"]*\.ecs\.[^"]*\.on\.aws' | head -1)

if [ -n "$SERVICE_URL" ]; then
    echo -e "${GREEN}  ✓ Service URL: $SERVICE_URL${NC}"
else
    echo -e "${YELLOW}  ⚠ Service URL not yet available${NC}"
    echo "  The service may still be provisioning infrastructure."
fi
echo ""

# Check tasks
echo -e "${YELLOW}5. Checking tasks...${NC}"
CLUSTER_NAME=$(basename "$CLUSTER")
TASKS=$(aws ecs list-tasks --cluster "$CLUSTER_NAME" --region $AWS_REGION --query 'taskArns[]' --output text 2>/dev/null || echo "")

if [ -z "$TASKS" ]; then
    echo -e "${YELLOW}  ⚠ No tasks found${NC}"
    echo "  Tasks may still be starting or there's an issue."
else
    echo -e "${GREEN}  ✓ Found tasks:${NC}"
    for task in $TASKS; do
        TASK_STATUS=$(aws ecs describe-tasks --cluster "$CLUSTER_NAME" --tasks "$task" --region $AWS_REGION --query 'tasks[0].lastStatus' --output text 2>/dev/null || echo "UNKNOWN")
        TASK_HEALTH=$(aws ecs describe-tasks --cluster "$CLUSTER_NAME" --tasks "$task" --region $AWS_REGION --query 'tasks[0].healthStatus' --output text 2>/dev/null || echo "UNKNOWN")
        echo "    Task: $(basename $task)"
        echo "      Status: $TASK_STATUS"
        echo "      Health: $TASK_HEALTH"
    done
fi
echo ""

# Check service events
echo -e "${YELLOW}6. Recent service events...${NC}"
echo "$SERVICE_DETAILS" | grep -A 2 '"message"' | head -20 || echo "  No events found"
echo ""

# Check CloudWatch logs
echo -e "${YELLOW}7. Checking CloudWatch logs...${NC}"
LOG_GROUP="/aws/ecs/express/$APP_NAME"
if aws logs describe-log-groups --log-group-name-prefix "$LOG_GROUP" --region $AWS_REGION --query 'logGroups[0]' --output text &>/dev/null; then
    echo -e "${GREEN}  ✓ Log group exists: $LOG_GROUP${NC}"
    echo ""
    echo "  Recent logs:"
    aws logs tail "$LOG_GROUP" --region $AWS_REGION --since 10m 2>/dev/null | head -30 || echo "  No recent logs"
else
    echo -e "${YELLOW}  ⚠ No log group found yet${NC}"
fi
echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

if [ "$STATUS" = "ACTIVE" ]; then
    echo -e "${GREEN}✓ Service is ACTIVE${NC}"
    if [ -n "$SERVICE_URL" ]; then
        echo -e "${GREEN}✓ Service URL available${NC}"
        echo ""
        echo "Access your application at:"
        echo "  $SERVICE_URL"
        echo ""
        echo "Test endpoints:"
        echo "  curl $SERVICE_URL/health"
        echo "  curl $SERVICE_URL/"
    else
        echo -e "${YELLOW}⚠ Service URL not yet available${NC}"
        echo "Wait a few more minutes for infrastructure provisioning."
    fi
elif [ "$STATUS" = "CREATING" ]; then
    echo -e "${YELLOW}⚠ Service is still CREATING${NC}"
    echo "This can take 5-10 minutes. Check back soon."
    echo ""
    echo "Monitor progress:"
    echo "  watch -n 10 './check-deployment-status.sh'"
else
    echo -e "${RED}❌ Service status: $STATUS${NC}"
    echo "Check the service events above for details."
fi
echo ""

# Helpful commands
echo "Useful commands:"
echo "  # View full service details"
echo "  aws ecs describe-express-gateway-service --service-arn $SERVICE_ARN --region $AWS_REGION"
echo ""
echo "  # View logs"
echo "  aws logs tail $LOG_GROUP --follow --region $AWS_REGION"
echo ""
echo "  # Force new deployment"
echo "  aws ecs update-express-gateway-service --service-arn $SERVICE_ARN --force-new-deployment --region $AWS_REGION"
echo ""
