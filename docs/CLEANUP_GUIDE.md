# Cleanup Guide

## Quick Cleanup

To delete all resources created by the deployment:

```bash
./cleanup-deployment.sh
```

## What Gets Deleted

The cleanup script removes:

### 1. ECS Express Mode Service
- The running ECS service
- **Automatically deleted by AWS:**
  - Application Load Balancer
  - Target Groups
  - Security Groups
  - Auto Scaling policies
  - ECS tasks

### 2. ECR Repository
- Container registry
- All container images

### 3. IAM Roles (Optional)
You'll be asked if you want to delete:
- `ecsTaskExecutionRole`
- `ecsInfrastructureRoleForExpressServices`
- `badgeAppTaskRole`

**⚠️ Warning:** Only delete IAM roles if no other ECS services are using them!

### 4. CloudWatch Logs (Optional)
- Application logs from `/aws/ecs/express/digital-badge-app`

## Usage

### Full Cleanup (Interactive)

```bash
./cleanup-deployment.sh
```

You'll be prompted to confirm:
1. Overall deletion (yes/no)
2. IAM role deletion (yes/no)
3. CloudWatch log deletion (yes/no)

### Cleanup Specific Region

```bash
AWS_REGION=eu-west-1 ./cleanup-deployment.sh
```

## What Happens

### Step 1: ECS Service Deletion
```
✓ Service deletion initiated
Note: Service deletion may take 5-10 minutes to complete
AWS will automatically delete: ALB, target groups, security groups
```

The service deletion is **asynchronous**. AWS will:
- Stop all running tasks
- Deregister targets from load balancer
- Delete the Application Load Balancer
- Delete target groups
- Delete security groups
- Delete auto-scaling policies

### Step 2: ECR Repository Deletion
```
✓ ECR repository deleted
```

This immediately deletes:
- The ECR repository
- All container images (cannot be recovered!)

### Step 3: IAM Roles (If Confirmed)
```
✓ badgeAppTaskRole deleted
✓ ecsTaskExecutionRole deleted
✓ ecsInfrastructureRoleForExpressServices deleted
```

Or if in use:
```
❌ Failed to delete ecsTaskExecutionRole (may be in use by other services)
```

### Step 4: CloudWatch Logs (If Confirmed)
```
✓ Log group deleted
```

## Verify Cleanup

### Check ECS Services
```bash
aws ecs list-express-gateway-services --region us-east-1
```

Should return empty or not include your service.

### Check ECR Repositories
```bash
aws ecr describe-repositories --region us-east-1
```

Should not include `digital-badge-app`.

### Check IAM Roles
```bash
aws iam get-role --role-name badgeAppTaskRole
```

Should return "NoSuchEntity" if deleted.

## Partial Cleanup

If you only want to delete specific resources:

### Delete Only ECS Service
```bash
aws ecs delete-express-gateway-service \
    --service-arn "arn:aws:ecs:us-east-1:ACCOUNT_ID:express-service/digital-badge-app" \
    --region us-east-1
```

### Delete Only ECR Repository
```bash
aws ecr delete-repository \
    --repository-name digital-badge-app \
    --force \
    --region us-east-1
```

### Delete Only IAM Role
```bash
# Delete inline policies first
aws iam delete-role-policy --role-name badgeAppTaskRole --policy-name BedrockAccess

# Delete role
aws iam delete-role --role-name badgeAppTaskRole
```

### Delete Only CloudWatch Logs
```bash
aws logs delete-log-group \
    --log-group-name /aws/ecs/express/digital-badge-app \
    --region us-east-1
```

## Cost Implications

After cleanup, you will **stop incurring charges** for:
- ✅ Fargate compute (tasks)
- ✅ Application Load Balancer
- ✅ Data transfer
- ✅ CloudWatch logs storage
- ✅ ECR storage

**Note:** Bedrock API calls are pay-per-use, so no ongoing charges.

## Troubleshooting

### Service Deletion Fails

**Error:** "Service is being deleted"

**Solution:** Wait a few minutes and check status:
```bash
aws ecs describe-express-gateway-service \
    --service-arn "arn:aws:ecs:us-east-1:ACCOUNT_ID:express-service/digital-badge-app" \
    --region us-east-1
```

### IAM Role Deletion Fails

**Error:** "Cannot delete entity, must detach all policies first"

**Solution:** Manually detach policies:
```bash
# List attached policies
aws iam list-attached-role-policies --role-name ecsTaskExecutionRole

# Detach each policy
aws iam detach-role-policy \
    --role-name ecsTaskExecutionRole \
    --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

# Delete role
aws iam delete-role --role-name ecsTaskExecutionRole
```

### ECR Repository Deletion Fails

**Error:** "RepositoryNotEmptyException"

**Solution:** Use `--force` flag (already in script):
```bash
aws ecr delete-repository \
    --repository-name digital-badge-app \
    --force \
    --region us-east-1
```

## Redeploy After Cleanup

After cleanup, you can redeploy anytime:

```bash
./deploy-to-ecs-express.sh
```

The deployment script will recreate all necessary resources.

## Keep IAM Roles for Future Deployments

If you plan to redeploy later, **keep the IAM roles**:
- Answer "no" when asked about IAM role deletion
- This saves time on future deployments
- Roles have no ongoing cost

## Complete Cleanup Checklist

- [ ] Run `./cleanup-deployment.sh`
- [ ] Confirm overall deletion
- [ ] Decide on IAM role deletion
- [ ] Decide on CloudWatch log deletion
- [ ] Wait 5-10 minutes for service deletion to complete
- [ ] Verify with `aws ecs list-express-gateway-services`
- [ ] Verify with `aws ecr describe-repositories`
- [ ] Check AWS Console for any remaining resources

## Emergency Cleanup

If the script fails, manually delete resources:

```bash
# 1. Delete service
aws ecs delete-express-gateway-service \
    --service-arn "$(aws ecs list-express-gateway-services --region us-east-1 --query 'serviceArns[0]' --output text)" \
    --region us-east-1

# 2. Delete ECR
aws ecr delete-repository --repository-name digital-badge-app --force --region us-east-1

# 3. Delete IAM roles (optional)
aws iam delete-role-policy --role-name badgeAppTaskRole --policy-name BedrockAccess
aws iam delete-role --role-name badgeAppTaskRole

aws iam detach-role-policy --role-name ecsTaskExecutionRole \
    --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
aws iam delete-role --role-name ecsTaskExecutionRole

aws iam detach-role-policy --role-name ecsInfrastructureRoleForExpressServices \
    --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSInfrastructureRoleforExpressGatewayServices
aws iam delete-role --role-name ecsInfrastructureRoleForExpressServices

# 4. Delete logs
aws logs delete-log-group --log-group-name /aws/ecs/express/digital-badge-app --region us-east-1
```

## Summary

**To delete everything:**
```bash
./cleanup-deployment.sh
```

**To redeploy:**
```bash
./deploy-to-ecs-express.sh
```

The cleanup script is safe, interactive, and gives you control over what gets deleted!
