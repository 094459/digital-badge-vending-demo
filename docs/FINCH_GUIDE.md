# Finch Guide for Digital Badge Platform

This guide covers using Finch (AWS's open-source container development tool) with the Digital Badge Platform.

## What is Finch?

Finch is an open-source container development tool by AWS that provides a simple CLI for building, running, and publishing containers. It's compatible with Docker commands and integrates well with AWS services.

## Quick Start

### Test Locally

```bash
# Run the automated test script
./test-local-finch.sh
```

This script will:
- Build the container image
- Start the application on port 8080
- Run health checks
- Test badge creation API
- Show you how to access the application

### Manual Commands

#### Build the Image
```bash
finch build -t digital-badge-app .
```

#### Run Locally
```bash
finch run -d \
    --name digital-badge-app \
    -p 8080:8080 \
    -e SECRET_KEY=your-secret-key \
    -e ADMIN_PASSWORD=admin123 \
    -e AWS_REGION=us-east-1 \
    -e BASE_URL=http://localhost:8080 \
    digital-badge-app
```

#### View Logs
```bash
# Follow logs in real-time
finch logs -f digital-badge-app

# View last 50 lines
finch logs --tail 50 digital-badge-app
```

#### Stop Container
```bash
finch stop digital-badge-app
```

#### Remove Container
```bash
finch rm digital-badge-app
```

#### List Running Containers
```bash
finch ps
```

#### List All Containers
```bash
finch ps -a
```

## Deploy to AWS ECS Express Mode

### Automated Deployment

```bash
# Run the deployment script
./deploy-to-ecs-express.sh
```

This script handles everything:
- Creates IAM roles
- Sets up ECR repository
- Builds and pushes image
- Deploys to ECS Express Mode

### Manual Deployment Steps

#### 1. Build and Tag
```bash
finch build -t digital-badge-app .
finch tag digital-badge-app:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/digital-badge-app:latest
```

#### 2. Login to ECR
```bash
aws ecr get-login-password --region us-east-1 | \
    finch login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
```

#### 3. Push to ECR
```bash
finch push <account-id>.dkr.ecr.us-east-1.amazonaws.com/digital-badge-app:latest
```

#### 4. Create ECS Service
```bash
aws ecs create-express-gateway-service \
    --image "<account-id>.dkr.ecr.us-east-1.amazonaws.com/digital-badge-app:latest" \
    --execution-role-arn arn:aws:iam::<account-id>:role/ecsTaskExecutionRole \
    --infrastructure-role-arn arn:aws:iam::<account-id>:role/ecsInfrastructureRoleForExpressServices \
    --task-role-arn arn:aws:iam::<account-id>:role/badgeAppTaskRole \
    --service-name "digital-badge-app" \
    --health-check-path "/health" \
    --monitor-resources
```

## Common Tasks

### Rebuild After Code Changes
```bash
# Stop and remove old container
finch stop digital-badge-app && finch rm digital-badge-app

# Rebuild image
finch build -t digital-badge-app .

# Run new container
finch run -d --name digital-badge-app -p 8080:8080 \
    -e SECRET_KEY=test -e AWS_REGION=us-east-1 \
    -e BASE_URL=http://localhost:8080 \
    digital-badge-app
```

### Debug Container Issues
```bash
# View logs
finch logs digital-badge-app

# Execute shell in running container
finch exec -it digital-badge-app /bin/bash

# Inspect container
finch inspect digital-badge-app
```

### Clean Up
```bash
# Stop all containers
finch stop $(finch ps -q)

# Remove all stopped containers
finch container prune

# Remove unused images
finch image prune

# Remove everything (containers, images, volumes)
finch system prune -a
```

## Testing Checklist

Before deploying to AWS, test locally:

- [ ] Build succeeds: `finch build -t digital-badge-app .`
- [ ] Container starts: `finch run -d -p 8080:8080 digital-badge-app`
- [ ] Health check passes: `curl http://localhost:8080/health`
- [ ] Home page loads: `curl http://localhost:8080/`
- [ ] Badge creation works: `curl -X POST http://localhost:8080/api/badges -H "Content-Type: application/json" -d '{"recipient_name": "Test"}'`
- [ ] No errors in logs: `finch logs digital-badge-app`

## Finch vs Docker

Finch commands are compatible with Docker:

| Task | Finch | Docker |
|------|-------|--------|
| Build | `finch build` | `docker build` |
| Run | `finch run` | `docker run` |
| Push | `finch push` | `docker push` |
| Logs | `finch logs` | `docker logs` |
| Exec | `finch exec` | `docker exec` |

Simply replace `finch` with `docker` if you prefer Docker.

## Troubleshooting

### Finch Not Found
```bash
# Check if Finch is installed
finch version

# If not installed, visit: https://github.com/runfinch/finch
```

### Port Already in Use
```bash
# Find process using port 8080
lsof -i :8080

# Use a different port
finch run -p 8081:8080 digital-badge-app
```

### Container Won't Start
```bash
# Check logs
finch logs digital-badge-app

# Run in foreground to see errors
finch run --rm -p 8080:8080 digital-badge-app
```

### AWS Credentials Not Working
```bash
# Mount AWS credentials into container
finch run -v ~/.aws:/root/.aws:ro -p 8080:8080 digital-badge-app

# Or pass as environment variables
finch run -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
    -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
    -p 8080:8080 digital-badge-app
```

### Image Push Fails
```bash
# Re-authenticate to ECR
aws ecr get-login-password --region us-east-1 | \
    finch login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Verify image exists
finch images | grep digital-badge-app

# Check ECR repository exists
aws ecr describe-repositories --repository-names digital-badge-app
```

## Performance Tips

### Multi-stage Builds
The current Dockerfile is optimized for size. To further optimize:

```dockerfile
# Use build cache
finch build --cache-from digital-badge-app:latest -t digital-badge-app .
```

### Faster Rebuilds
```bash
# Only rebuild if dependencies changed
finch build --target production -t digital-badge-app .
```

## Resources

- [Finch Documentation](https://github.com/runfinch/finch)
- [Finch vs Docker](https://aws.amazon.com/blogs/opensource/introducing-finch/)
- [ECS Express Mode Guide](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/express-service-overview.html)

---

**Quick Commands Reference:**

```bash
# Test locally
./test-local-finch.sh

# Deploy to AWS
./deploy-to-ecs-express.sh

# View logs
finch logs -f digital-badge-app

# Stop container
finch stop digital-badge-app
```
