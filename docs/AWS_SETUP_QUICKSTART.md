# AWS Setup Quick Start

## 1. Install AWS CLI

**macOS:**
```bash
brew install awscli
```

**Linux:**
```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

**Windows:**
Download from: https://aws.amazon.com/cli/

## 2. Configure AWS Credentials

```bash
aws configure
```

You'll be prompted for:
```
AWS Access Key ID [None]: YOUR_ACCESS_KEY
AWS Secret Access Key [None]: YOUR_SECRET_KEY
Default region name [None]: us-east-1
Default output format [None]: json
```

## 3. Verify Configuration

```bash
# Check identity
aws sts get-caller-identity

# Expected output:
# {
#     "UserId": "AIDAI...",
#     "Account": "123456789012",
#     "Arn": "arn:aws:iam::123456789012:user/your-user"
# }
```

## 4. Test Bedrock Access

```bash
# List available models
aws bedrock list-foundation-models --region us-east-1

# Check for Nova Canvas
aws bedrock list-foundation-models \
  --region us-east-1 \
  --query 'modelSummaries[?contains(modelId, `nova-canvas`)]'
```

## 5. Enable Bedrock Model Access

1. Go to AWS Console → Bedrock
2. Click "Model access" in left sidebar
3. Click "Manage model access"
4. Enable "Amazon Nova Canvas"
5. Click "Save changes"

## 6. Test from Python

```bash
python3 << EOF
import boto3

# Test credentials
sts = boto3.client('sts')
identity = sts.get_caller_identity()
print(f"✓ AWS Account: {identity['Account']}")

# Test Bedrock access
bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
print("✓ Bedrock client created successfully")
EOF
```

## 7. Run the Application

```bash
# Start the server
uv run python run.py

# Visit http://127.0.0.1:5001
```

## Troubleshooting

### "Unable to locate credentials"

```bash
# Check configuration
aws configure list

# Check credential file
cat ~/.aws/credentials

# Re-configure
aws configure
```

### "Access Denied" for Bedrock

```bash
# Check IAM permissions
aws iam get-user-policy --user-name YOUR_USER --policy-name YOUR_POLICY

# Or attach managed policy
aws iam attach-user-policy \
  --user-name YOUR_USER \
  --policy-arn arn:aws:iam::aws:policy/AmazonBedrockFullAccess
```

### Wrong Region

```bash
# Set region
export AWS_REGION=us-east-1

# Or in .env file
echo "AWS_REGION=us-east-1" >> .env
```

## IAM Policy for Bedrock

Minimum required permissions:

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
        "arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-canvas-v1:0",
        "arn:aws:bedrock:us-west-2::foundation-model/amazon.nova-canvas-v1:0"
      ]
    }
  ]
}
```

To create and attach:

```bash
# Create policy
aws iam create-policy \
  --policy-name BedrockNovaCanvasAccess \
  --policy-document file://bedrock-policy.json

# Attach to user
aws iam attach-user-policy \
  --user-name YOUR_USER \
  --policy-arn arn:aws:iam::ACCOUNT_ID:policy/BedrockNovaCanvasAccess
```

## Alternative: Use IAM Role (Production)

For EC2 instances:

```bash
# Create role
aws iam create-role \
  --role-name badge-app-role \
  --assume-role-policy-document file://trust-policy.json

# Attach policy
aws iam attach-role-policy \
  --role-name badge-app-role \
  --policy-arn arn:aws:iam::ACCOUNT_ID:policy/BedrockNovaCanvasAccess

# Attach to EC2 instance
aws ec2 associate-iam-instance-profile \
  --instance-id i-1234567890abcdef0 \
  --iam-instance-profile Name=badge-app-role
```

## Security Reminders

✅ **DO:**
- Use AWS CLI configuration for local development
- Use IAM roles for production (EC2/ECS/Lambda)
- Rotate credentials regularly
- Use least privilege permissions

❌ **DON'T:**
- Store credentials in .env files
- Commit credentials to git
- Share credentials between team members
- Use root account credentials

## Quick Reference

| Method | Use Case | Setup |
|--------|----------|-------|
| AWS CLI | Local development | `aws configure` |
| IAM Role | Production (EC2/ECS) | Attach role to instance |
| Environment Variables | CI/CD, temporary | `export AWS_ACCESS_KEY_ID=...` |
| AWS SSO | Team access | `aws configure sso` |

## Next Steps

1. ✅ Configure AWS credentials
2. ✅ Enable Bedrock model access
3. ✅ Test connection
4. ✅ Run application
5. ✅ Create first badge

For detailed information, see [AWS_CREDENTIALS.md](AWS_CREDENTIALS.md)
