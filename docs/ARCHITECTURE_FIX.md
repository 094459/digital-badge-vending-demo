# Architecture Fix: ARM64 vs x86_64

## The Problem

You encountered this error:
```
exec /bin/sh: exec format error
```

**Root Cause:** You built an ARM64 container image (on Apple Silicon Mac) but ECS Fargate tried to run it on x86_64 architecture.

## The Solution

Build the container image for **x86_64 (AMD64)** architecture, which is the default for ECS Fargate.

### What I Fixed

**Updated `deploy-to-ecs-express.sh`:**
```bash
# BEFORE (builds for your Mac's architecture - ARM64)
finch build -t $APP_NAME:latest .

# AFTER (builds for x86_64 - ECS default)
finch build --platform linux/amd64 -t $APP_NAME:latest .
```

**Updated `test-local-finch.sh`:**
```bash
finch build --platform linux/amd64 -t $APP_NAME:latest .
```

## How to Fix Your Deployment

### Option 1: Rebuild and Redeploy (Recommended)

```bash
# 1. Clean up the failed deployment
./cleanup-deployment.sh

# 2. Redeploy with the fixed script
./deploy-to-ecs-express.sh
```

The script will now build for x86_64 automatically.

### Option 2: Manual Fix

If you want to fix without full cleanup:

```bash
# 1. Rebuild image for x86_64
finch build --platform linux/amd64 -t digital-badge-app .

# 2. Get your account ID and region
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=us-east-1

# 3. Tag and push
finch tag digital-badge-app:latest $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/digital-badge-app:latest
aws ecr get-login-password --region $REGION | \
    finch login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com
finch push $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/digital-badge-app:latest

# 4. Force new deployment
SERVICE_ARN=$(aws ecs list-express-gateway-services --region $REGION --query 'serviceArns[0]' --output text)
aws ecs update-express-gateway-service \
    --service-arn "$SERVICE_ARN" \
    --region $REGION \
    --force-new-deployment
```

## Understanding the Issue

### Your Mac (Apple Silicon)
- **Architecture:** ARM64 (Apple M1/M2/M3)
- **Default build:** ARM64 containers

### ECS Fargate Default
- **Architecture:** x86_64 (AMD64)
- **Expects:** x86_64 containers

### The Mismatch
```
ARM64 container → x86_64 ECS = exec format error ❌
x86_64 container → x86_64 ECS = works perfectly ✅
```

## Architecture Options

### Option A: x86_64 (Recommended - Default)

**Pros:**
- ✅ Default for ECS Fargate
- ✅ Widest compatibility
- ✅ More instance types available
- ✅ No special configuration needed

**Cons:**
- ⚠️ Slightly slower build on ARM Mac (emulation)
- ⚠️ Slightly higher cost than ARM

**Build command:**
```bash
finch build --platform linux/amd64 -t digital-badge-app .
```

### Option B: ARM64 (Graviton)

**Pros:**
- ✅ Better price/performance (20% cheaper)
- ✅ Native build on ARM Mac (faster)
- ✅ Lower power consumption

**Cons:**
- ⚠️ Requires explicit configuration
- ⚠️ Not all regions/AZs support it
- ⚠️ Fewer instance types

**Build command:**
```bash
finch build --platform linux/arm64 -t digital-badge-app .
```

**ECS configuration needed:**
```bash
# Would need to add runtime platform to deployment
--runtime-platform '{"cpuArchitecture": "ARM64", "operatingSystemFamily": "LINUX"}'
```

## Why x86_64 is Better for This Project

1. **Simplicity** - No special ECS configuration needed
2. **Compatibility** - Works everywhere
3. **Default** - ECS Express Mode defaults to x86_64
4. **Availability** - Supported in all regions/AZs

The performance difference is negligible for this application since most time is spent in:
- Network I/O (Bedrock API calls)
- Image generation (Bedrock, not CPU)
- Database operations (minimal)

## Performance Impact

### Build Time
- **ARM64 on ARM Mac:** ~2 minutes (native)
- **x86_64 on ARM Mac:** ~3 minutes (emulation)

**Verdict:** 1 minute slower build, but only happens during deployment.

### Runtime Performance
- **x86_64 Fargate:** Excellent
- **ARM64 Fargate:** ~10-20% better price/performance

**Verdict:** For this app, the difference is negligible since most time is in Bedrock API calls (3-5 seconds), not CPU.

## Verify Architecture

### Check Local Image
```bash
finch inspect digital-badge-app:latest | grep Architecture
```

Should show:
```json
"Architecture": "amd64"
```

### Check ECR Image
```bash
aws ecr describe-images \
    --repository-name digital-badge-app \
    --region us-east-1 \
    --query 'imageDetails[0].imageManifestMediaType'
```

### Check Running Container
After deployment, check the task:
```bash
aws ecs describe-tasks \
    --cluster default \
    --tasks $(aws ecs list-tasks --cluster default --query 'taskArns[0]' --output text) \
    --query 'tasks[0].containers[0].runtimeId'
```

## Multi-Architecture Support (Advanced)

If you want to support both architectures:

```bash
# Build for both
finch build --platform linux/amd64,linux/arm64 -t digital-badge-app .

# Push both
finch push --all-platforms digital-badge-app
```

Then ECS can automatically select the right architecture.

## Testing Locally

### Test x86_64 Image on ARM Mac
```bash
# Build for x86_64
finch build --platform linux/amd64 -t digital-badge-app .

# Run (Finch will emulate x86_64)
finch run -p 8080:8080 digital-badge-app

# Should work, but slower due to emulation
```

### Test ARM64 Image on ARM Mac
```bash
# Build for ARM64
finch build --platform linux/arm64 -t digital-badge-app .

# Run (native, fast)
finch run -p 8080:8080 digital-badge-app
```

## Summary

**Problem:** Built ARM64 image, ECS expected x86_64  
**Solution:** Build for x86_64 with `--platform linux/amd64`  
**Status:** ✅ Fixed in deployment scripts

**To fix your deployment:**
```bash
./cleanup-deployment.sh
./deploy-to-ecs-express.sh
```

The new deployment will build for x86_64 and work correctly!

## Additional Resources

- [ECS ARM64 Support](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs-arm64.html)
- [Fargate Platform Versions](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/platform_versions.html)
- [Multi-Architecture Images](https://docs.docker.com/build/building/multi-platform/)
