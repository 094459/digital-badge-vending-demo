#!/bin/bash
# Build and push container image to Amazon ECR
# This script only handles the build/push — no ECS deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
APP_NAME="digital-badge-app"
AWS_REGION="${AWS_REGION:-eu-west-1}"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "")

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Build & Push to ECR${NC}"
echo -e "${GREEN}Digital Badge Platform${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not found. Please install it first.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ AWS CLI installed${NC}"

if ! command -v finch &> /dev/null; then
    echo -e "${RED}❌ Finch not found. Please install it first.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Finch installed${NC}"

if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo -e "${RED}❌ Unable to get AWS account ID. Please configure AWS CLI.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ AWS credentials configured (Account: $AWS_ACCOUNT_ID)${NC}"

ECR_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$APP_NAME"

echo ""
echo -e "${YELLOW}Configuration:${NC}"
echo "  App Name:       $APP_NAME"
echo "  Region:         $AWS_REGION"
echo "  ECR Repository: $ECR_URI"
echo ""
# Step 1: Ensure ECR repository exists
echo -e "${YELLOW}Step 1: Checking ECR Repository...${NC}"

if aws ecr describe-repositories --repository-names $APP_NAME --region $AWS_REGION &>/dev/null; then
    echo -e "${GREEN}✓ ECR repository already exists${NC}"
else
    aws ecr create-repository --repository-name $APP_NAME --region $AWS_REGION &>/dev/null
    echo -e "${GREEN}✓ ECR repository created${NC}"
fi

# Step 2: Build container image
echo ""
echo -e "${YELLOW}Step 2: Building container image...${NC}"

finch build --platform linux/amd64 -t $APP_NAME:latest .
echo -e "${GREEN}✓ Image built${NC}"

# Step 3: Tag and push to ECR
echo ""
echo -e "${YELLOW}Step 3: Pushing image to ECR...${NC}"

finch tag $APP_NAME:latest $ECR_URI:latest

aws ecr get-login-password --region $AWS_REGION | finch login --username AWS --password-stdin $ECR_URI

finch push $ECR_URI:latest
echo -e "${GREEN}✓ Image pushed to ECR${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✓ Build & Push Complete${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Image URI: $ECR_URI:latest"
echo ""
