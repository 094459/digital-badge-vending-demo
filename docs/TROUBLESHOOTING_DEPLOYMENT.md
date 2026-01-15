# Deployment Troubleshooting Guide

## Script Stops After "Note: BASE_URL will be set after we get the actual service URL"

This means the `aws ecs create-express-gateway-service` command is failing silently. Let's diagnose and fix it.

## Quick Diagnosis

Run the diagnostic script:

```bash
./diagnose-deployment.sh
```

This will check:
1. AWS CLI version (need >= 2.15.0)
2. AWS credentials
3. ECS Express Mode availability
4. IAM roles
5. ECR repository
6. Finch installation
7. Bedrock access
8. Service quotas
9. Command syntax

## Common Issues and Solutions

### Issue 1: AWS CLI Too Old

**Symptom:** Script stops without error message

**Cause:** ECS Express Mode requires AWS CLI >= 2.15.0

**Check:**
```bash
aws --version
```

**Solution:**
```bash
# macOS with Homebrew
brew upgrade awscli

# Or download latest from AWS
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /
```

### Issue 2: ECS Express Mode Not Available in Region

**Symptom:** Command not recognized or fails

**Cause:** ECS Express Mode not available in your region

**Check:**
```bash
aws ecs create-express-gateway-service help
```

**Solution:**
Use a supported region:
```bash
export AWS_REGION=us-east-1
./deploy-to-ecs-express.sh
```

**Supported regions:**
- us-east-1 (N. Virginia)
- us-west-2 (Oregon)
- eu-west-1 (Ireland)
- ap-southeast-1 (Singapore)
- And more - check AWS documentation

### Issue 3: IAM Role Permissions

**Symptom:** "AccessDenied" or "User is not authorized"

**Cause:** Your AWS user doesn't have permissions to create IAM roles or ECS services

**Check:**
```bash
aws iam get-user
aws sts get-caller-identity
```

**Solution:**
Your AWS user needs these permissions:
- `iam:CreateRole`
- `iam:AttachRolePolicy`
- `iam:GetRole`
- `ecs:CreateExpressGatewayService`
- `ecs:DescribeExpressGatewayService`
- `ecr:CreateRepository`
- `ecr:GetAuthorizationToken`

Ask your AWS administrator to grant these permissions.

### Issue 4: Service Quota Exceeded

**Symptom:** "LimitExceededException"

**Cause:** You've reached the maximum number of ECS services

**Check:**
```bash
aws service-quotas get-service-quota \
    --service-code ecs \
    --quota-code L-9EF96962 \
    --region us-east-1
```

**Solution:**
- Delete unused ECS services
- Request quota increase in AWS Console

### Issue 5: Invalid JSON in Command

**Symptom:** "Invalid JSON" or "ParamValidationError"

**Cause:** JSON escaping issue in the deployment script

**Check:**
Run the script with debug mode:
```bash
bash -x ./deploy-to-ecs-express.sh 2>&1 | tee deployment.log
```

**Solution:**
The updated script has better error handling. If you still see this, check for special characters in your SECRET_KEY or ADMIN_PASSWORD.

### Issue 6: Image Not Found

**Symptom:** "ImageNotFoundException" or "CannotPullContainerError"

**Cause:** Container image wasn't pushed to ECR successfully

**Check:**
```bash
aws ecr list-images --repository-name digital-badge-app --region us-east-1
```

**Solution:**
```bash
# Rebuild and push manually
finch build -t digital-badge-app .
aws ecr get-login-password --region us-east-1 | \
    finch login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
finch tag digital-badge-app:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/digital-badge-app:latest
finch push <account-id>.dkr.ecr.us-east-1.amazonaws.com/digital-badge-app:latest
```

## Manual Deployment Steps

If the script continues to fail, deploy manually:

### Step 1: Create IAM Roles

```bash
# Task Execution Role
aws iam create-role --role-name ecsTaskExecutionRole \
    --assume-role-policy-document '{
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "ecs-tasks.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }'

aws iam attach-role-policy --role-name ecsTaskExecutionRole \
    --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

# Infrastructure Role
aws iam create-role --role-name ecsInfrastructureRoleForExpressServices \
    --assume-role-policy-document '{
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "ecs.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }'

aws iam attach-role-policy --role-name ecsInfrastructureRoleForExpressServices \
    --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSInfrastructureRoleforExpressGatewayServices

# Task Role (for Bedrock)
aws iam create-role --role-name badgeAppTaskRole \
    --assume-role-policy-document '{
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "ecs-tasks.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }'

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
```

### Step 2: Build and Push Image

```bash
# Get your account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=us-east-1

# Create ECR repository
aws ecr create-repository --repository-name digital-badge-app --region $REGION

# Build image
finch build -t digital-badge-app .

# Login to ECR
aws ecr get-login-password --region $REGION | \
    finch login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

# Tag and push
finch tag digital-badge-app:latest $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/digital-badge-app:latest
finch push $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/digital-badge-app:latest
```

### Step 3: Create ECS Service

```bash
# Set your secrets
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
ADMIN_PASSWORD="your-password-here"

# Create service
aws ecs create-express-gateway-service \
    --region $REGION \
    --execution-role-arn "arn:aws:iam::$ACCOUNT_ID:role/ecsTaskExecutionRole" \
    --infrastructure-role-arn "arn:aws:iam::$ACCOUNT_ID:role/ecsInfrastructureRoleForExpressServices" \
    --task-role-arn "arn:aws:iam::$ACCOUNT_ID:role/badgeAppTaskRole" \
    --primary-container "{
        \"image\": \"$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/digital-badge-app:latest\",
        \"containerPort\": 8080,
        \"environment\": [
            {\"name\": \"FLASK_ENV\", \"value\": \"production\"},
            {\"name\": \"AWS_REGION\", \"value\": \"$REGION\"},
            {\"name\": \"BEDROCK_REGION\", \"value\": \"us-east-1\"},
            {\"name\": \"SECRET_KEY\", \"value\": \"$SECRET_KEY\"},
            {\"name\": \"ADMIN_PASSWORD\", \"value\": \"$ADMIN_PASSWORD\"}
        ]
    }" \
    --service-name "digital-badge-app" \
    --cpu 1 \
    --memory 2 \
    --health-check-path "/health" \
    --scaling-target "{\"minTaskCount\": 2, \"maxTaskCount\": 10}"
```

### Step 4: Get Service URL

```bash
# Wait a few minutes for deployment
sleep 60

# Get service details
aws ecs describe-express-gateway-service \
    --service-arn "arn:aws:ecs:$REGION:$ACCOUNT_ID:express-service/digital-badge-app" \
    --region $REGION
```

Look for the `serviceUrl` in the output.

## Debug Mode

Run the deployment script with full debugging:

```bash
bash -x ./deploy-to-ecs-express.sh 2>&1 | tee deployment-debug.log
```

This will:
- Show every command being executed
- Display all output
- Save everything to `deployment-debug.log`

## Check Deployment Status

If the service was created but you're not sure of the status:

```bash
# List all ECS services
aws ecs list-express-gateway-services --region us-east-1

# Get specific service details
aws ecs describe-express-gateway-service \
    --service-arn "arn:aws:ecs:us-east-1:ACCOUNT_ID:express-service/digital-badge-app" \
    --region us-east-1
```

## View Logs

If the service is running but not working:

```bash
# View CloudWatch logs
aws logs tail /aws/ecs/express/digital-badge-app --follow --region us-east-1
```

## Clean Up Failed Deployment

If you need to start over:

```bash
# Delete service (if created)
aws ecs delete-express-gateway-service \
    --service-arn "arn:aws:ecs:us-east-1:ACCOUNT_ID:express-service/digital-badge-app" \
    --region us-east-1

# Delete ECR repository
aws ecr delete-repository \
    --repository-name digital-badge-app \
    --force \
    --region us-east-1

# IAM roles can be reused, no need to delete
```

## Get Help

If you're still stuck:

1. **Run diagnostics:**
   ```bash
   ./diagnose-deployment.sh
   ```

2. **Check AWS CLI version:**
   ```bash
   aws --version
   ```

3. **Verify credentials:**
   ```bash
   aws sts get-caller-identity
   ```

4. **Test ECS Express Mode:**
   ```bash
   aws ecs create-express-gateway-service help
   ```

5. **Check the updated deployment script:**
   The script now has better error handling and will show you exactly what's failing.

## Success Indicators

You'll know deployment succeeded when you see:

```
✓ Service created: arn:aws:ecs:...
✓ Application URL: https://digital-badge-app.ecs.us-east-1.on.aws
✓ BASE_URL configured
✓ Deployment Complete!
```

Then you can access your app at the displayed URL!
