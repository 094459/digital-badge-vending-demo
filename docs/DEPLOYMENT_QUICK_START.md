# Quick Start: Deploy to ECS Express Mode

## TL;DR

```bash
# Test locally
./test-local-finch.sh

# Deploy to AWS
./deploy-to-ecs-express.sh
```

That's it! The script handles everything, including the BASE_URL configuration.

---

## What You Need

- ✅ AWS CLI configured
- ✅ Finch installed
- ✅ AWS account with Bedrock access

## What the Script Does

### Automated Deployment Script (`deploy-to-ecs-express.sh`)

1. **Creates IAM Roles** (if they don't exist)
   - Task Execution Role
   - Infrastructure Role  
   - Task Role (for Bedrock access)

2. **Sets Up ECR**
   - Creates repository
   - Logs in to ECR

3. **Builds & Pushes Image**
   - Builds with Finch
   - Tags for ECR
   - Pushes to registry

4. **Deploys to ECS Express Mode**
   - Creates service without BASE_URL
   - Waits for service creation
   - Extracts actual service URL
   - Updates service with correct BASE_URL

5. **Shows You the URL**
   - Displays the live application URL
   - Shows health check, admin, and API endpoints

## BASE_URL - No Configuration Needed!

**The Problem:** You don't know the ECS URL until after deployment.

**The Solution:** The application automatically detects its URL from incoming requests!

### How It Works

The app uses a smart `get_base_url()` function that:

1. **First:** Checks if `BASE_URL` environment variable is set
2. **Then:** Reads `X-Forwarded-Proto` and `X-Forwarded-Host` headers from the ALB
3. **Finally:** Falls back to localhost for development

**Result:** QR codes and badge links work correctly without any manual configuration!

### Deployment Flow

```
Deploy Service (no BASE_URL)
    ↓
Service Gets URL: https://digital-badge-app.ecs.us-east-1.on.aws
    ↓
Script Extracts URL
    ↓
Script Updates Service with BASE_URL
    ↓
Done! Application fully configured
```

## Step-by-Step

### 1. Test Locally (Optional but Recommended)

```bash
./test-local-finch.sh
```

This will:
- Build the container
- Run it on port 8080
- Test health endpoint
- Test badge creation
- Show you the logs

### 2. Deploy to AWS

```bash
./deploy-to-ecs-express.sh
```

You'll be prompted for:
- **SECRET_KEY** (press Enter to auto-generate)
- **ADMIN_PASSWORD** (required)

The script will:
- Create all necessary AWS resources
- Build and push your container
- Deploy to ECS Express Mode
- Configure BASE_URL automatically
- Show you the live URL

**Time:** ~10-15 minutes

### 3. Access Your Application

After deployment completes, you'll see:

```
Your application is now available at:
https://digital-badge-app.ecs.us-east-1.on.aws

Endpoints:
  Home:        https://digital-badge-app.ecs.us-east-1.on.aws/
  Health:      https://digital-badge-app.ecs.us-east-1.on.aws/health
  Admin:       https://digital-badge-app.ecs.us-east-1.on.aws/admin
  API:         https://digital-badge-app.ecs.us-east-1.on.aws/api/badges
```

## Verify Deployment

### Test Health Endpoint
```bash
curl https://digital-badge-app.ecs.us-east-1.on.aws/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "digital-badge-platform",
  "database": "connected"
}
```

### Test Badge Creation
```bash
curl -X POST https://digital-badge-app.ecs.us-east-1.on.aws/api/badges \
  -H "Content-Type: application/json" \
  -d '{"recipient_name": "Test User"}'
```

### View Logs
```bash
aws logs tail /aws/ecs/express/digital-badge-app --follow
```

## What Gets Created

### AWS Resources
- **ECS Express Mode Service** - Your application
- **Application Load Balancer** - Automatic HTTPS/TLS
- **Auto Scaling** - 2-10 tasks based on CPU
- **CloudWatch Logs** - Application logs
- **ECR Repository** - Container images
- **IAM Roles** - Permissions for ECS and Bedrock

### Cost Estimate
- **~$76/month** for 2 tasks running 24/7
- Includes: Fargate compute, ALB, CloudWatch logs
- Excludes: Data transfer, Bedrock API calls

## Common Questions

### Q: Do I need to configure BASE_URL?
**A:** No! The application detects it automatically from request headers.

### Q: What if I want a custom domain?
**A:** Set BASE_URL explicitly after deployment:
```bash
aws ecs update-express-gateway-service \
  --service-arn <arn> \
  --primary-container '{"environment": [{"name": "BASE_URL", "value": "https://badges.yourdomain.com"}]}'
```

### Q: How do I update the application?
**A:** Rebuild and push the image, then update the service:
```bash
finch build -t digital-badge-app .
finch tag digital-badge-app:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/digital-badge-app:latest
finch push <account-id>.dkr.ecr.us-east-1.amazonaws.com/digital-badge-app:latest

aws ecs update-express-gateway-service --service-arn <arn> --force-new-deployment
```

### Q: How do I delete everything?
**A:** Delete the ECS service and ECR repository:
```bash
aws ecs delete-express-gateway-service --service-arn <arn>
aws ecr delete-repository --repository-name digital-badge-app --force
```

## Troubleshooting

### Deployment Fails
```bash
# Check IAM roles exist
aws iam get-role --role-name ecsTaskExecutionRole
aws iam get-role --role-name ecsInfrastructureRoleForExpressServices
aws iam get-role --role-name badgeAppTaskRole

# Check ECR repository
aws ecr describe-repositories --repository-names digital-badge-app
```

### Health Check Fails
```bash
# View logs
aws logs tail /aws/ecs/express/digital-badge-app --follow

# Check service status
aws ecs describe-express-gateway-service --service-arn <arn>
```

### QR Codes Show Wrong URL
```bash
# Check BASE_URL setting
aws ecs describe-express-gateway-service --service-arn <arn> | grep BASE_URL

# The app should work even without BASE_URL set
# It will detect the URL from request headers
```

## Next Steps

After successful deployment:

1. **Set Up Database** - Consider RDS PostgreSQL for production
2. **Configure File Storage** - Use S3 for uploads and generated badges
3. **Add Secrets Manager** - Move SECRET_KEY and ADMIN_PASSWORD
4. **Set Up Monitoring** - Configure CloudWatch alarms
5. **Custom Domain** - Point your domain to the ALB

## Documentation

- **BASE_URL_GUIDE.md** - Detailed BASE_URL explanation
- **ECS_EXPRESS_READINESS_REPORT.md** - Complete readiness assessment
- **FINCH_GUIDE.md** - Finch commands and troubleshooting
- **ECS_DEPLOYMENT_SUMMARY.md** - Summary of all changes

## Support

If you encounter issues:

1. Check the deployment script output
2. Review CloudWatch logs
3. Verify IAM roles and permissions
4. Test locally with `./test-local-finch.sh`
5. Review the troubleshooting section in `ECS_EXPRESS_READINESS_REPORT.md`

---

**Ready to deploy?**

```bash
./deploy-to-ecs-express.sh
```

Your application will be live in ~15 minutes! 🚀
