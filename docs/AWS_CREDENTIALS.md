# AWS Credentials Configuration

This application uses Amazon Bedrock for AI-powered badge generation. AWS credentials are **NOT** stored in configuration files for security reasons.

## Credential Chain

The application uses boto3's default credential provider chain in this order:

1. **Environment Variables**
2. **AWS CLI Configuration**
3. **IAM Roles** (EC2, ECS, Lambda)
4. **Instance Metadata Service (IMDS)**

## Setup Methods

### Method 1: AWS CLI (Recommended for Local Development)

```bash
# Install AWS CLI
# macOS: brew install awscli
# Linux: pip install awscli
# Windows: Download from AWS website

# Configure credentials
aws configure

# You'll be prompted for:
# AWS Access Key ID: [your key]
# AWS Secret Access Key: [your secret]
# Default region name: us-east-1
# Default output format: json
```

Credentials are stored in `~/.aws/credentials`:
```ini
[default]
aws_access_key_id = YOUR_KEY
aws_secret_access_key = YOUR_SECRET
```

Region is stored in `~/.aws/config`:
```ini
[default]
region = us-east-1
```

### Method 2: Environment Variables

```bash
# Set for current session
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_REGION=us-east-1

# Or add to ~/.bashrc or ~/.zshrc for persistence
echo 'export AWS_ACCESS_KEY_ID=your_access_key' >> ~/.bashrc
echo 'export AWS_SECRET_ACCESS_KEY=your_secret_key' >> ~/.bashrc
echo 'export AWS_REGION=us-east-1' >> ~/.bashrc
source ~/.bashrc
```

### Method 3: IAM Roles (Recommended for Production)

#### For EC2 Instances

1. Create IAM role with Bedrock permissions:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": [
        "arn:aws:bedrock:*::foundation-model/amazon.nova-canvas-v1:0"
      ]
    }
  ]
}
```

2. Attach role to EC2 instance
3. No credentials needed in code or configuration

#### For ECS/Fargate

Set task role in task definition:
```json
{
  "taskRoleArn": "arn:aws:iam::123456789012:role/badge-app-task-role",
  "executionRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole"
}
```

#### For Lambda

Lambda execution role automatically provides credentials:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
```

### Method 4: AWS SSO

```bash
# Configure SSO
aws configure sso

# Login
aws sso login --profile your-profile

# Use profile
export AWS_PROFILE=your-profile
```

## Verification

Test your credentials:

```bash
# Check identity
aws sts get-caller-identity

# Test Bedrock access
aws bedrock list-foundation-models --region us-east-1

# Test from Python
python -c "import boto3; print(boto3.client('sts').get_caller_identity())"
```

## Required IAM Permissions

Minimum permissions needed:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "BedrockInvokeModel",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": [
        "arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-canvas-v1:0",
        "arn:aws:bedrock:us-west-2::foundation-model/amazon.nova-canvas-v1:0"
      ]
    }
  ]
}
```

## Security Best Practices

### ✅ DO

- Use IAM roles for production deployments
- Use AWS CLI configuration for local development
- Rotate credentials regularly
- Use least privilege permissions
- Enable MFA for IAM users
- Use AWS SSO for team access

### ❌ DON'T

- Store credentials in .env files
- Commit credentials to git
- Share credentials between team members
- Use root account credentials
- Hard-code credentials in source code
- Store credentials in Docker images

## Troubleshooting

### "Unable to locate credentials"

```bash
# Check if credentials are configured
aws configure list

# Check environment variables
env | grep AWS

# Check credential file
cat ~/.aws/credentials

# Test with explicit profile
AWS_PROFILE=default python run.py
```

### "Access Denied" Error

```bash
# Verify permissions
aws bedrock list-foundation-models --region us-east-1

# Check IAM policy
aws iam get-user-policy --user-name your-user --policy-name your-policy
```

### Region Issues

```bash
# Set region explicitly
export AWS_REGION=us-east-1

# Or in .env file
echo "AWS_REGION=us-east-1" >> .env
```

## Docker Deployment

### With AWS CLI Config

```bash
docker run -d \
  -v ~/.aws:/root/.aws:ro \
  -e AWS_REGION=us-east-1 \
  -p 8000:8000 \
  badge-app
```

### With Environment Variables

```bash
docker run -d \
  -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
  -e AWS_REGION=us-east-1 \
  -p 8000:8000 \
  badge-app
```

### With IAM Role (ECS)

```json
{
  "taskDefinition": {
    "taskRoleArn": "arn:aws:iam::account:role/badge-app-role",
    "containerDefinitions": [
      {
        "name": "badge-app",
        "image": "badge-app:latest",
        "environment": [
          {
            "name": "AWS_REGION",
            "value": "us-east-1"
          }
        ]
      }
    ]
  }
}
```

## Multiple AWS Accounts

Use profiles:

```bash
# Configure multiple profiles
aws configure --profile dev
aws configure --profile prod

# Use specific profile
export AWS_PROFILE=prod
python run.py

# Or in code (not recommended)
boto3.Session(profile_name='prod')
```

## References

- [AWS CLI Configuration](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html)
- [Boto3 Credentials](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html)
- [IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [Amazon Bedrock Security](https://docs.aws.amazon.com/bedrock/latest/userguide/security.html)
