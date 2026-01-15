#!/bin/bash
# Cleanup script to delete all resources created by deploy-to-ecs-express.sh
# This script removes ECS services, ECR repositories, and optionally IAM roles

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="digital-badge-app"
AWS_REGION="${AWS_REGION:-eu-west-1}"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "")

echo -e "${RED}========================================${NC}"
echo -e "${RED}ECS Express Mode Cleanup Script${NC}"
echo -e "${RED}Digital Badge Platform${NC}"
echo -e "${RED}========================================${NC}"
echo ""
echo -e "${YELLOW}⚠️  WARNING: This will delete all deployed resources!${NC}"
echo ""

# Check prerequisites
if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo -e "${RED}❌ AWS credentials not configured${NC}"
    exit 1
fi

echo "Configuration:"
echo "  App Name: $APP_NAME"
echo "  AWS Region: $AWS_REGION"
echo "  AWS Account: $AWS_ACCOUNT_ID"
echo ""

# Ask for confirmation
echo -e "${YELLOW}This will delete:${NC}"
echo "  1. ECS Express Mode service (if exists)"
echo "  2. ECR repository and all container images"
echo "  3. Optionally: IAM roles (you'll be asked)"
echo ""
read -p "Are you sure you want to continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Cleanup cancelled."
    exit 0
fi

echo ""

# Step 1: Find and delete ECS Express Mode service
echo -e "${YELLOW}Step 1: Checking for ECS Express Mode service...${NC}"

# List all express services
SERVICES=$(aws ecs list-express-gateway-services --region $AWS_REGION --query 'serviceArns[]' --output text 2>/dev/null || echo "")

if [ -z "$SERVICES" ]; then
    echo -e "${YELLOW}  ⚠ No Express Mode services found${NC}"
else
    # Look for our service
    SERVICE_ARN=""
    for arn in $SERVICES; do
        SERVICE_NAME=$(aws ecs describe-express-gateway-service --service-arn "$arn" --region $AWS_REGION --query 'service.serviceName' --output text 2>/dev/null || echo "")
        if [ "$SERVICE_NAME" = "$APP_NAME" ]; then
            SERVICE_ARN="$arn"
            break
        fi
    done
    
    if [ -n "$SERVICE_ARN" ]; then
        echo "  Found service: $SERVICE_ARN"
        echo "  Deleting ECS Express Mode service..."
        
        aws ecs delete-express-gateway-service \
            --service-arn "$SERVICE_ARN" \
            --region $AWS_REGION 2>&1
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}  ✓ Service deletion initiated${NC}"
            echo -e "${YELLOW}  Note: Service deletion may take 5-10 minutes to complete${NC}"
            echo -e "${YELLOW}  AWS will automatically delete: ALB, target groups, security groups${NC}"
        else
            echo -e "${RED}  ❌ Failed to delete service${NC}"
        fi
    else
        echo -e "${YELLOW}  ⚠ Service '$APP_NAME' not found${NC}"
    fi
fi
echo ""

# Step 2: Delete ECR repository
echo -e "${YELLOW}Step 2: Checking for ECR repository...${NC}"

if aws ecr describe-repositories --repository-names $APP_NAME --region $AWS_REGION &>/dev/null; then
    echo "  Found ECR repository: $APP_NAME"
    
    # Count images
    IMAGE_COUNT=$(aws ecr list-images --repository-name $APP_NAME --region $AWS_REGION --query 'length(imageIds)' --output text 2>/dev/null || echo "0")
    echo "  Repository contains $IMAGE_COUNT image(s)"
    
    echo "  Deleting ECR repository and all images..."
    aws ecr delete-repository \
        --repository-name $APP_NAME \
        --region $AWS_REGION \
        --force 2>&1
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}  ✓ ECR repository deleted${NC}"
    else
        echo -e "${RED}  ❌ Failed to delete ECR repository${NC}"
    fi
else
    echo -e "${YELLOW}  ⚠ ECR repository not found${NC}"
fi
echo ""

# Step 3: Ask about IAM roles
echo -e "${YELLOW}Step 3: IAM Roles...${NC}"
echo ""
echo "The following IAM roles were created (or may have existed before):"
echo "  - ecsTaskExecutionRole"
echo "  - ecsInfrastructureRoleForExpressServices"
echo "  - badgeAppTaskRole"
echo ""
echo -e "${YELLOW}⚠️  WARNING: These roles may be used by other ECS services!${NC}"
echo "Only delete them if you're sure no other services are using them."
echo ""
read -p "Do you want to delete IAM roles? (yes/no): " DELETE_ROLES

if [ "$DELETE_ROLES" = "yes" ]; then
    echo ""
    
    # Delete badgeAppTaskRole
    echo "Deleting badgeAppTaskRole..."
    if aws iam get-role --role-name badgeAppTaskRole &>/dev/null; then
        # Delete inline policies first
        aws iam delete-role-policy --role-name badgeAppTaskRole --policy-name BedrockAccess 2>/dev/null || true
        
        # Delete role
        aws iam delete-role --role-name badgeAppTaskRole 2>&1
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}  ✓ badgeAppTaskRole deleted${NC}"
        else
            echo -e "${RED}  ❌ Failed to delete badgeAppTaskRole${NC}"
        fi
    else
        echo -e "${YELLOW}  ⚠ badgeAppTaskRole not found${NC}"
    fi
    
    # Delete ecsTaskExecutionRole
    echo "Deleting ecsTaskExecutionRole..."
    if aws iam get-role --role-name ecsTaskExecutionRole &>/dev/null; then
        # Detach managed policies
        aws iam detach-role-policy \
            --role-name ecsTaskExecutionRole \
            --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy 2>/dev/null || true
        
        # Delete role
        aws iam delete-role --role-name ecsTaskExecutionRole 2>&1
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}  ✓ ecsTaskExecutionRole deleted${NC}"
        else
            echo -e "${RED}  ❌ Failed to delete ecsTaskExecutionRole (may be in use by other services)${NC}"
        fi
    else
        echo -e "${YELLOW}  ⚠ ecsTaskExecutionRole not found${NC}"
    fi
    
    # Delete ecsInfrastructureRoleForExpressServices
    echo "Deleting ecsInfrastructureRoleForExpressServices..."
    if aws iam get-role --role-name ecsInfrastructureRoleForExpressServices &>/dev/null; then
        # Detach managed policies
        aws iam detach-role-policy \
            --role-name ecsInfrastructureRoleForExpressServices \
            --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSInfrastructureRoleforExpressGatewayServices 2>/dev/null || true
        
        # Delete role
        aws iam delete-role --role-name ecsInfrastructureRoleForExpressServices 2>&1
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}  ✓ ecsInfrastructureRoleForExpressServices deleted${NC}"
        else
            echo -e "${RED}  ❌ Failed to delete ecsInfrastructureRoleForExpressServices (may be in use)${NC}"
        fi
    else
        echo -e "${YELLOW}  ⚠ ecsInfrastructureRoleForExpressServices not found${NC}"
    fi
else
    echo -e "${YELLOW}  ⚠ Skipping IAM role deletion${NC}"
    echo "  Roles will remain for future deployments"
fi
echo ""

# Step 4: Check for CloudWatch Log Groups
echo -e "${YELLOW}Step 4: Checking for CloudWatch Log Groups...${NC}"

LOG_GROUP="/aws/ecs/express/$APP_NAME"
if aws logs describe-log-groups --log-group-name-prefix "$LOG_GROUP" --region $AWS_REGION --query 'logGroups[0]' --output text &>/dev/null; then
    echo "  Found log group: $LOG_GROUP"
    read -p "  Delete CloudWatch logs? (yes/no): " DELETE_LOGS
    
    if [ "$DELETE_LOGS" = "yes" ]; then
        aws logs delete-log-group --log-group-name "$LOG_GROUP" --region $AWS_REGION 2>&1
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}  ✓ Log group deleted${NC}"
        else
            echo -e "${RED}  ❌ Failed to delete log group${NC}"
        fi
    else
        echo -e "${YELLOW}  ⚠ Skipping log group deletion${NC}"
    fi
else
    echo -e "${YELLOW}  ⚠ No log groups found${NC}"
fi
echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Cleanup Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Resources processed:"
echo "  ✓ ECS Express Mode service - checked and deleted if found"
echo "  ✓ ECR repository - deleted with all images"
if [ "$DELETE_ROLES" = "yes" ]; then
    echo "  ✓ IAM roles - deletion attempted"
else
    echo "  ⚠ IAM roles - skipped (still exist)"
fi
if [ "$DELETE_LOGS" = "yes" ]; then
    echo "  ✓ CloudWatch logs - deleted"
else
    echo "  ⚠ CloudWatch logs - skipped or not found"
fi
echo ""
echo -e "${YELLOW}Note: ECS service deletion is asynchronous and may take several minutes.${NC}"
echo "AWS will automatically clean up associated resources:"
echo "  - Application Load Balancer"
echo "  - Target Groups"
echo "  - Security Groups"
echo "  - Auto Scaling policies"
echo ""
echo "To verify deletion is complete:"
echo "  aws ecs list-express-gateway-services --region $AWS_REGION"
echo ""
echo -e "${GREEN}Cleanup script completed!${NC}"
echo ""
