#!/bin/bash
# Diagnostic script to check ECS Express Mode deployment readiness

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}ECS Express Mode Deployment Diagnostics${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check AWS CLI version
echo -e "${YELLOW}1. Checking AWS CLI version...${NC}"
AWS_VERSION=$(aws --version 2>&1)
echo "  $AWS_VERSION"

# Extract version number
CLI_VERSION=$(echo "$AWS_VERSION" | grep -oE 'aws-cli/[0-9]+\.[0-9]+\.[0-9]+' | cut -d'/' -f2)
MAJOR_VERSION=$(echo "$CLI_VERSION" | cut -d'.' -f1)
MINOR_VERSION=$(echo "$CLI_VERSION" | cut -d'.' -f2)

if [ "$MAJOR_VERSION" -lt 2 ] || ([ "$MAJOR_VERSION" -eq 2 ] && [ "$MINOR_VERSION" -lt 15 ]); then
    echo -e "${RED}  ❌ AWS CLI version too old (need >= 2.15.0)${NC}"
    echo -e "${YELLOW}  Update with: brew upgrade awscli (or your package manager)${NC}"
else
    echo -e "${GREEN}  ✓ AWS CLI version is sufficient${NC}"
fi
echo ""

# Check AWS credentials
echo -e "${YELLOW}2. Checking AWS credentials...${NC}"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "")
if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo -e "${RED}  ❌ AWS credentials not configured${NC}"
    echo -e "${YELLOW}  Run: aws configure${NC}"
    exit 1
else
    echo -e "${GREEN}  ✓ AWS credentials configured${NC}"
    echo "  Account ID: $AWS_ACCOUNT_ID"
fi
echo ""

# Check region
echo -e "${YELLOW}3. Checking AWS region...${NC}"
AWS_REGION="${AWS_REGION:-$(aws configure get region)}"
if [ -z "$AWS_REGION" ]; then
    AWS_REGION="us-east-1"
    echo -e "${YELLOW}  ⚠ No region set, using default: us-east-1${NC}"
else
    echo -e "${GREEN}  ✓ Region: $AWS_REGION${NC}"
fi
echo ""

# Check if ECS Express Mode is available
echo -e "${YELLOW}4. Checking ECS Express Mode availability...${NC}"
echo "  Testing: aws ecs create-express-gateway-service help"
if aws ecs create-express-gateway-service help &>/dev/null; then
    echo -e "${GREEN}  ✓ ECS Express Mode commands available${NC}"
else
    echo -e "${RED}  ❌ ECS Express Mode commands not available${NC}"
    echo -e "${YELLOW}  This could mean:${NC}"
    echo "    - AWS CLI version too old"
    echo "    - ECS Express Mode not available in your region"
    echo "    - AWS CLI not properly installed"
    exit 1
fi
echo ""

# Check IAM roles
echo -e "${YELLOW}5. Checking IAM roles...${NC}"

# Task Execution Role
if aws iam get-role --role-name ecsTaskExecutionRole &>/dev/null; then
    echo -e "${GREEN}  ✓ ecsTaskExecutionRole exists${NC}"
else
    echo -e "${RED}  ❌ ecsTaskExecutionRole not found${NC}"
    echo -e "${YELLOW}  The deployment script will create it${NC}"
fi

# Infrastructure Role
if aws iam get-role --role-name ecsInfrastructureRoleForExpressServices &>/dev/null; then
    echo -e "${GREEN}  ✓ ecsInfrastructureRoleForExpressServices exists${NC}"
else
    echo -e "${RED}  ❌ ecsInfrastructureRoleForExpressServices not found${NC}"
    echo -e "${YELLOW}  The deployment script will create it${NC}"
fi

# Task Role
if aws iam get-role --role-name badgeAppTaskRole &>/dev/null; then
    echo -e "${GREEN}  ✓ badgeAppTaskRole exists${NC}"
else
    echo -e "${RED}  ❌ badgeAppTaskRole not found${NC}"
    echo -e "${YELLOW}  The deployment script will create it${NC}"
fi
echo ""

# Check ECR repository
echo -e "${YELLOW}6. Checking ECR repository...${NC}"
if aws ecr describe-repositories --repository-names digital-badge-app --region $AWS_REGION &>/dev/null; then
    echo -e "${GREEN}  ✓ ECR repository exists${NC}"
    
    # Check if image exists
    IMAGE_COUNT=$(aws ecr list-images --repository-name digital-badge-app --region $AWS_REGION --query 'length(imageIds)' --output text 2>/dev/null || echo "0")
    if [ "$IMAGE_COUNT" -gt 0 ]; then
        echo -e "${GREEN}  ✓ Container images found: $IMAGE_COUNT${NC}"
    else
        echo -e "${YELLOW}  ⚠ No container images found${NC}"
        echo -e "${YELLOW}  The deployment script will build and push the image${NC}"
    fi
else
    echo -e "${YELLOW}  ⚠ ECR repository not found${NC}"
    echo -e "${YELLOW}  The deployment script will create it${NC}"
fi
echo ""

# Check Finch
echo -e "${YELLOW}7. Checking Finch...${NC}"
if command -v finch &> /dev/null; then
    FINCH_VERSION=$(finch version 2>&1 | head -1)
    echo -e "${GREEN}  ✓ Finch installed: $FINCH_VERSION${NC}"
else
    echo -e "${RED}  ❌ Finch not found${NC}"
    echo -e "${YELLOW}  Install from: https://github.com/runfinch/finch${NC}"
    exit 1
fi
echo ""

# Check Bedrock access
echo -e "${YELLOW}8. Checking Bedrock access...${NC}"
BEDROCK_REGION="${BEDROCK_REGION:-us-east-1}"
echo "  Testing Bedrock in region: $BEDROCK_REGION"

if aws bedrock list-foundation-models --region $BEDROCK_REGION &>/dev/null; then
    echo -e "${GREEN}  ✓ Bedrock API accessible${NC}"
    
    # Check if Nova Canvas is available
    NOVA_AVAILABLE=$(aws bedrock list-foundation-models --region $BEDROCK_REGION --query "modelSummaries[?contains(modelId, 'nova-canvas')].modelId" --output text 2>/dev/null || echo "")
    if [ -n "$NOVA_AVAILABLE" ]; then
        echo -e "${GREEN}  ✓ Nova Canvas model available${NC}"
    else
        echo -e "${RED}  ❌ Nova Canvas model not available${NC}"
        echo -e "${YELLOW}  Enable model access in Bedrock console:${NC}"
        echo "    https://console.aws.amazon.com/bedrock/home?region=$BEDROCK_REGION#/modelaccess"
    fi
else
    echo -e "${RED}  ❌ Cannot access Bedrock API${NC}"
    echo -e "${YELLOW}  Check IAM permissions for bedrock:ListFoundationModels${NC}"
fi
echo ""

# Check service quotas
echo -e "${YELLOW}9. Checking ECS service quotas...${NC}"
SERVICES_QUOTA=$(aws service-quotas get-service-quota \
    --service-code ecs \
    --quota-code L-9EF96962 \
    --region $AWS_REGION \
    --query 'Quota.Value' \
    --output text 2>/dev/null || echo "unknown")

if [ "$SERVICES_QUOTA" != "unknown" ]; then
    echo -e "${GREEN}  ✓ ECS services quota: $SERVICES_QUOTA${NC}"
else
    echo -e "${YELLOW}  ⚠ Could not check service quotas${NC}"
fi
echo ""

# Test ECS Express Mode command
echo -e "${YELLOW}10. Testing ECS Express Mode command availability...${NC}"
echo "  Checking if create-express-gateway-service command exists..."

if aws ecs create-express-gateway-service help &>/dev/null; then
    echo -e "${GREEN}  ✓ create-express-gateway-service command is available${NC}"
else
    echo -e "${RED}  ❌ create-express-gateway-service command not found${NC}"
    echo -e "${YELLOW}  This means:${NC}"
    echo "    - AWS CLI version is too old (need >= 2.15.0)"
    echo "    - Or ECS Express Mode not available in your region"
    exit 1
fi
echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Configuration:"
echo "  AWS Account: $AWS_ACCOUNT_ID"
echo "  ECS Region: $AWS_REGION"
echo "  Bedrock Region: $BEDROCK_REGION"
echo ""
echo "Next steps:"
echo "  1. If all checks passed, run: ./deploy-to-ecs-express.sh"
echo "  2. If checks failed, fix the issues above"
echo "  3. For detailed logs, run with: bash -x ./deploy-to-ecs-express.sh"
echo ""
