#!/bin/bash
# Deploy Digital Badge Platform to Amazon ECS Express Mode
# This script automates the deployment process

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="digital-badge-app"
AWS_REGION="${AWS_REGION:-eu-west-1}"
BEDROCK_REGION="${BEDROCK_REGION:-us-east-1}"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "")

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}ECS Express Mode Deployment Script${NC}"
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

echo ""
echo -e "${YELLOW}Configuration:${NC}"
echo "  App Name: $APP_NAME"
echo "  ECS Region: $AWS_REGION"
echo "  Bedrock Region: $BEDROCK_REGION"
echo "  AWS Account: $AWS_ACCOUNT_ID"
echo ""

# Ask for confirmation
read -p "Continue with deployment? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled."
    exit 0
fi

# Step 1: Create IAM Roles
echo ""
echo -e "${YELLOW}Step 1: Creating IAM Roles...${NC}"

# Task Execution Role
if aws iam get-role --role-name ecsTaskExecutionRole &>/dev/null; then
    echo -e "${GREEN}✓ Task Execution Role already exists${NC}"
    
    # Ensure ECR permissions are attached
    echo "  Verifying ECR permissions..."
    aws iam attach-role-policy --role-name ecsTaskExecutionRole \
        --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy 2>/dev/null || true
else
    echo "Creating Task Execution Role..."
    aws iam create-role --role-name ecsTaskExecutionRole \
        --assume-role-policy-document '{
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {"Service": "ecs-tasks.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }]
        }' &>/dev/null
    
    # Attach the managed policy
    aws iam attach-role-policy --role-name ecsTaskExecutionRole \
        --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
    
    # Add explicit ECR permissions inline policy for immediate effect
    aws iam put-role-policy --role-name ecsTaskExecutionRole \
        --policy-name ECRAccessPolicy \
        --policy-document '{
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "ecr:GetAuthorizationToken",
                        "ecr:BatchCheckLayerAvailability",
                        "ecr:GetDownloadUrlForLayer",
                        "ecr:BatchGetImage"
                    ],
                    "Resource": "*"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    "Resource": "*"
                }
            ]
        }'
    
    echo -e "${GREEN}✓ Task Execution Role created with ECR permissions${NC}"
    echo -e "${YELLOW}  Waiting 10 seconds for IAM policy propagation...${NC}"
    sleep 10
fi

# Infrastructure Role
if aws iam get-role --role-name ecsInfrastructureRoleForExpressServices &>/dev/null; then
    echo -e "${GREEN}✓ Infrastructure Role already exists${NC}"
else
    echo "Creating Infrastructure Role..."
    aws iam create-role --role-name ecsInfrastructureRoleForExpressServices \
        --assume-role-policy-document '{
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {"Service": "ecs.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }]
        }' &>/dev/null
    
    aws iam attach-role-policy --role-name ecsInfrastructureRoleForExpressServices \
        --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSInfrastructureRoleforExpressGatewayServices
    
    echo -e "${GREEN}✓ Infrastructure Role created${NC}"
fi

# Task Role (for Bedrock access)
if aws iam get-role --role-name badgeAppTaskRole &>/dev/null; then
    echo -e "${GREEN}✓ Task Role already exists${NC}"
else
    echo "Creating Task Role for Bedrock access..."
    aws iam create-role --role-name badgeAppTaskRole \
        --assume-role-policy-document '{
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {"Service": "ecs-tasks.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }]
        }' &>/dev/null
    
    aws iam put-role-policy --role-name badgeAppTaskRole \
        --policy-name BedrockAccess \
        --policy-document '{
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": ["bedrock:InvokeModel"],
                "Resource": ["arn:aws:bedrock:*::foundation-model/amazon.nova-canvas-v1:0"]
            }]
        }'
    
    echo -e "${GREEN}✓ Task Role created with Bedrock permissions${NC}"
fi

# Wait for roles to propagate
echo "Waiting for IAM roles to propagate..."
sleep 10

# Step 2: Create ECR Repository
echo ""
echo -e "${YELLOW}Step 2: Creating ECR Repository...${NC}"

if aws ecr describe-repositories --repository-names $APP_NAME --region $AWS_REGION &>/dev/null; then
    echo -e "${GREEN}✓ ECR repository already exists${NC}"
else
    aws ecr create-repository --repository-name $APP_NAME --region $AWS_REGION &>/dev/null
    echo -e "${GREEN}✓ ECR repository created${NC}"
fi

ECR_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$APP_NAME"
echo "  Repository URI: $ECR_URI"

# Step 3: Build and Push Docker Image
echo ""
echo -e "${YELLOW}Step 3: Building and Pushing Docker Image...${NC}"

echo "Building container image with Finch for x86_64 architecture..."
finch build --platform linux/amd64 -t $APP_NAME:latest .

echo "Tagging image..."
finch tag $APP_NAME:latest $ECR_URI:latest

echo "Logging in to ECR..."
aws ecr get-login-password --region $AWS_REGION | finch login --username AWS --password-stdin $ECR_URI

echo "Pushing image to ECR..."
finch push $ECR_URI:latest

echo -e "${GREEN}✓ Image pushed to ECR${NC}"

# Step 4: Get configuration
echo ""
echo -e "${YELLOW}Step 4: Configuration...${NC}"

read -p "Enter SECRET_KEY (or press Enter to generate): " SECRET_KEY
if [ -z "$SECRET_KEY" ]; then
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    echo "Generated SECRET_KEY: $SECRET_KEY"
fi

read -p "Enter ADMIN_PASSWORD: " ADMIN_PASSWORD
if [ -z "$ADMIN_PASSWORD" ]; then
    echo -e "${RED}❌ ADMIN_PASSWORD is required${NC}"
    exit 1
fi

# Step 5: Deploy to ECS Express Mode
echo ""
echo -e "${YELLOW}Step 5: Deploying to ECS Express Mode...${NC}"

SERVICE_NAME="$APP_NAME"

# Check if service already exists by trying to describe it directly
echo "Checking if service already exists..."
SERVICE_CHECK=$(aws ecs describe-services --services "$SERVICE_NAME" --region $AWS_REGION 2>/dev/null)
SERVICE_STATUS=$(echo "$SERVICE_CHECK" | grep -o '"status": *"[^"]*"' | head -1 | cut -d'"' -f4)

if [ "$SERVICE_STATUS" = "ACTIVE" ]; then
    echo -e "${YELLOW}Service already exists and is active. Updating existing service...${NC}"
    
    # Extract the service ARN
    SERVICE_ARN=$(echo "$SERVICE_CHECK" | grep -o '"serviceArn": *"[^"]*"' | head -1 | cut -d'"' -f4)
    echo "Service ARN: $SERVICE_ARN"
    
    # Update the existing service with new image and configuration
    aws ecs update-express-gateway-service \
        --service-arn "$SERVICE_ARN" \
        --region $AWS_REGION \
        --primary-container "{
            \"image\": \"$ECR_URI:latest\",
            \"containerPort\": 8080,
            \"environment\": [
                {\"name\": \"FLASK_ENV\", \"value\": \"production\"},
                {\"name\": \"AWS_REGION\", \"value\": \"$AWS_REGION\"},
                {\"name\": \"BEDROCK_REGION\", \"value\": \"$BEDROCK_REGION\"},
                {\"name\": \"SECRET_KEY\", \"value\": \"$SECRET_KEY\"},
                {\"name\": \"ADMIN_PASSWORD\", \"value\": \"$ADMIN_PASSWORD\"}
            ]
        }" \
        --cpu "1024" \
        --memory "2048" \
        --health-check-path "/health" \
        --scaling-target "{\"minTaskCount\": 1, \"maxTaskCount\": 1}"
    
    echo -e "${GREEN}✓ Service updated successfully${NC}"
    
    # Get the service URL
    SERVICE_DETAILS=$(aws ecs describe-express-gateway-service \
        --service-arn "$SERVICE_ARN" \
        --region $AWS_REGION 2>/dev/null)
    
    APP_URL=$(echo "$SERVICE_DETAILS" | grep -o 'https://[^"]*\.ecs\.[^"]*\.on\.aws' | head -1)
    
    if [ -z "$APP_URL" ]; then
        APP_URL="https://$SERVICE_NAME.ecs.$AWS_REGION.on.aws"
    fi
    
    # Update with BASE_URL
    echo ""
    echo -e "${YELLOW}Updating BASE_URL configuration...${NC}"
    
    aws ecs update-express-gateway-service \
        --service-arn "$SERVICE_ARN" \
        --region $AWS_REGION \
        --primary-container "{
            \"image\": \"$ECR_URI:latest\",
            \"containerPort\": 8080,
            \"environment\": [
                {\"name\": \"FLASK_ENV\", \"value\": \"production\"},
                {\"name\": \"AWS_REGION\", \"value\": \"$AWS_REGION\"},
                {\"name\": \"BEDROCK_REGION\", \"value\": \"$BEDROCK_REGION\"},
                {\"name\": \"SECRET_KEY\", \"value\": \"$SECRET_KEY\"},
                {\"name\": \"ADMIN_PASSWORD\", \"value\": \"$ADMIN_PASSWORD\"},
                {\"name\": \"BASE_URL\", \"value\": \"$APP_URL\"}
            ]
        }" \
        --cpu "1024" \
        --memory "2048" \
        --health-check-path "/health" \
        --scaling-target "{\"minTaskCount\": 1, \"maxTaskCount\": 1}"
    
    echo -e "${GREEN}✓ BASE_URL configured${NC}"
    
else
    echo "Creating new Express Mode service..."
    echo "This may take 5-10 minutes..."
    echo ""
    echo -e "${YELLOW}Note: BASE_URL will be set after we get the actual service URL${NC}"
    echo ""

    # Create service without BASE_URL first (will update after)
    echo "Running: aws ecs create-express-gateway-service..."
    DEPLOYMENT_OUTPUT=$(aws ecs create-express-gateway-service \
        --region $AWS_REGION \
        --execution-role-arn "arn:aws:iam::$AWS_ACCOUNT_ID:role/ecsTaskExecutionRole" \
        --infrastructure-role-arn "arn:aws:iam::$AWS_ACCOUNT_ID:role/ecsInfrastructureRoleForExpressServices" \
        --task-role-arn "arn:aws:iam::$AWS_ACCOUNT_ID:role/badgeAppTaskRole" \
        --primary-container "{
            \"image\": \"$ECR_URI:latest\",
            \"containerPort\": 8080,
            \"environment\": [
                {\"name\": \"FLASK_ENV\", \"value\": \"production\"},
                {\"name\": \"AWS_REGION\", \"value\": \"$AWS_REGION\"},
                {\"name\": \"BEDROCK_REGION\", \"value\": \"$BEDROCK_REGION\"},
                {\"name\": \"SECRET_KEY\", \"value\": \"$SECRET_KEY\"},
                {\"name\": \"ADMIN_PASSWORD\", \"value\": \"$ADMIN_PASSWORD\"}
            ]
        }" \
        --service-name "$SERVICE_NAME" \
        --cpu "1024" \
        --memory "2048" \
        --health-check-path "/health" \
        --scaling-target "{\"minTaskCount\": 1, \"maxTaskCount\": 1}" )
        
    DEPLOY_EXIT_CODE=$?
    #    
    # Show output for debugging
    echo ""
    echo "Deployment output:"
    echo "$DEPLOYMENT_OUTPUT"
    echo ""

    # Check if deployment failed
    if [ $DEPLOY_EXIT_CODE -ne 0 ]; then
        echo -e "${RED}❌ Deployment failed with exit code: $DEPLOY_EXIT_CODE${NC}"
        echo ""
        echo "Common issues:"
        echo "  1. ECS Express Mode not available in $AWS_REGION"
        echo "  2. IAM roles don't have correct permissions"
        echo "  3. Service quota exceeded"
        echo "  4. Invalid parameter values"
        echo ""
        echo "Full error output above. Please check and try again."
        exit 1
    fi

    # Extract service ARN from output
    SERVICE_ARN=$(echo "$DEPLOYMENT_OUTPUT" | grep -o 'arn:aws:ecs:[^"]*' | head -1)

    if [ -z "$SERVICE_ARN" ]; then
        echo -e "${RED}❌ Failed to create service - could not extract service ARN${NC}"
        echo ""
        echo "Deployment output:"
        echo "$DEPLOYMENT_OUTPUT"
        echo ""
        echo "This usually means:"
        echo "  1. The create-express-gateway-service command is not available"
        echo "  2. Your AWS CLI version is too old (need >= 2.15.0)"
        echo "  3. ECS Express Mode is not available in $AWS_REGION"
        echo ""
        echo "Check your AWS CLI version:"
        aws --version
        exit 1
    fi

    echo -e "${GREEN}✓ Service created: $SERVICE_ARN${NC}"

    # Wait a moment for service to initialize
    echo ""
    echo -e "${YELLOW}Retrieving service URL...${NC}"
    sleep 5

    # Get the service details to extract the URL
    SERVICE_DETAILS=$(aws ecs describe-express-gateway-service \
        --service-arn "$SERVICE_ARN" \
        --region $AWS_REGION 2>/dev/null)

    # Extract the application URL
    APP_URL=$(echo "$SERVICE_DETAILS" | grep -o 'https://[^"]*\.ecs\.[^"]*\.on\.aws' | head -1)

    if [ -z "$APP_URL" ]; then
        # Fallback: construct URL from service name
        APP_URL="https://$SERVICE_NAME.ecs.$AWS_REGION.on.aws"
        echo -e "${YELLOW}⚠ Could not extract URL from service, using default format${NC}"
    fi

    echo -e "${GREEN}✓ Application URL: $APP_URL${NC}"

    # Update the service with the correct BASE_URL
    echo ""
    echo -e "${YELLOW}Updating service with BASE_URL...${NC}"

    aws ecs update-express-gateway-service \
        --service-arn "$SERVICE_ARN" \
        --region $AWS_REGION \
        --primary-container "{
            \"image\": \"$ECR_URI:latest\",
            \"containerPort\": 8080,
            \"environment\": [
                {\"name\": \"FLASK_ENV\", \"value\": \"production\"},
                {\"name\": \"AWS_REGION\", \"value\": \"$AWS_REGION\"},
                {\"name\": \"BEDROCK_REGION\", \"value\": \"$BEDROCK_REGION\"},
                {\"name\": \"SECRET_KEY\", \"value\": \"$SECRET_KEY\"},
                {\"name\": \"ADMIN_PASSWORD\", \"value\": \"$ADMIN_PASSWORD\"},
                {\"name\": \"BASE_URL\", \"value\": \"$APP_URL\"}
            ]
        }" \
        --cpu "1024" \
        --memory "2048" \
        --health-check-path "/health" \
        --scaling-target "{\"minTaskCount\": 1, \"maxTaskCount\": 1}"

    echo -e "${GREEN}✓ BASE_URL configured${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✓ Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Your application is now available at:"
echo -e "${GREEN}$APP_URL${NC}"
echo ""
echo "Service ARN:"
echo "  $SERVICE_ARN"
echo ""
echo "Endpoints:"
echo "  Home:        $APP_URL/"
echo "  Health:      $APP_URL/health"
echo "  Admin:       $APP_URL/admin"
echo "  API:         $APP_URL/api/badges"
echo ""
echo "To monitor your service:"
echo "  aws ecs describe-express-gateway-service --service-arn $SERVICE_ARN --region $AWS_REGION"
echo ""
echo "To view logs:"
echo "  aws logs tail /aws/ecs/express/$SERVICE_NAME --follow --region $AWS_REGION"
echo ""
echo "Note: It may take a few minutes for the service to become fully available."
echo "      The initial deployment will restart once to apply the BASE_URL."
echo ""
