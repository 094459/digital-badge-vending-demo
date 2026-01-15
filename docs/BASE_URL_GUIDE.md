# BASE_URL Configuration Guide

## The Problem

When deploying to Amazon ECS Express Mode, you don't know the application URL until **after** the service is created. ECS Express Mode automatically generates a unique URL in the format:

```
https://<service-name>.ecs.<region>.on.aws
```

For example:
```
https://digital-badge-app.ecs.us-east-1.on.aws
```

This creates a chicken-and-egg problem: your application needs the BASE_URL to generate QR codes and badge links, but you don't know the URL until deployment completes.

## The Solution

We've implemented a **three-tier approach** that handles BASE_URL gracefully:

### 1. Dynamic URL Detection (Automatic)

The application now includes a `get_base_url()` utility function that automatically detects the correct URL from incoming requests:

**File:** `app/src/utils.py`

```python
def get_base_url():
    """
    Get the base URL for the application.
    
    Priority:
    1. BASE_URL environment variable (if set)
    2. Dynamically construct from request (for ECS Express Mode)
    3. Default to localhost for development
    """
    # First, check if BASE_URL is explicitly set
    base_url = os.getenv('BASE_URL')
    
    if base_url:
        return base_url.rstrip('/')
    
    # If not set, construct from the current request
    # This works in ECS Express Mode where the ALB provides the correct host
    if request:
        try:
            scheme = request.headers.get('X-Forwarded-Proto', request.scheme)
            host = request.headers.get('X-Forwarded-Host', request.host)
            return f"{scheme}://{host}"
        except RuntimeError:
            pass
    
    # Fallback to localhost for development
    return 'http://127.0.0.1:5001'
```

**How it works:**
- When a request comes through the ECS Express Mode ALB, it includes headers like `X-Forwarded-Proto` (https) and `X-Forwarded-Host` (your-app.ecs.region.on.aws)
- The function reads these headers and constructs the correct BASE_URL automatically
- No configuration needed!

### 2. Deployment Script Updates (Automatic)

The deployment script now handles BASE_URL in two phases:

**Phase 1: Initial Deployment (without BASE_URL)**
```bash
# Deploy service without BASE_URL
aws ecs create-express-gateway-service \
    --primary-container '{
        "environment": [
            {"name": "FLASK_ENV", "value": "production"},
            {"name": "AWS_REGION", "value": "us-east-1"},
            {"name": "SECRET_KEY", "value": "..."}
            # No BASE_URL yet!
        ]
    }'
```

**Phase 2: Update with Actual URL**
```bash
# Get the actual service URL
SERVICE_DETAILS=$(aws ecs describe-express-gateway-service --service-arn "$SERVICE_ARN")
APP_URL=$(extract_url_from_details)

# Update service with BASE_URL
aws ecs update-express-gateway-service \
    --primary-container '{
        "environment": [
            {"name": "BASE_URL", "value": "$APP_URL"}
        ]
    }'
```

The deployment script (`deploy-to-ecs-express.sh`) handles this automatically!

### 3. Fallback Behavior (Automatic)

Even without BASE_URL set, the application works:

- **During initial deployment:** Uses dynamic URL detection from request headers
- **For QR codes:** Generated with the dynamically detected URL
- **For badge links:** Constructed from the current request
- **For local development:** Falls back to `http://127.0.0.1:5001`

## How to Deploy

### Option 1: Automated Deployment (Recommended)

Simply run the deployment script:

```bash
./deploy-to-ecs-express.sh
```

The script will:
1. ✅ Deploy the service without BASE_URL
2. ✅ Wait for the service to be created
3. ✅ Extract the actual service URL
4. ✅ Update the service with the correct BASE_URL
5. ✅ Display the final URL

**No manual configuration needed!**

### Option 2: Manual Deployment

If deploying manually, you can:

**Step 1: Deploy without BASE_URL**
```bash
aws ecs create-express-gateway-service \
    --image "<your-image>" \
    --service-name "digital-badge-app" \
    # ... other parameters, no BASE_URL
```

**Step 2: Get the service URL**
```bash
aws ecs describe-express-gateway-service \
    --service-arn "<service-arn>" \
    --query 'service.serviceUrl' \
    --output text
```

**Step 3: Update with BASE_URL (Optional)**
```bash
aws ecs update-express-gateway-service \
    --service-arn "<service-arn>" \
    --primary-container '{
        "environment": [
            {"name": "BASE_URL", "value": "https://digital-badge-app.ecs.us-east-1.on.aws"}
        ]
    }'
```

**Note:** Step 3 is optional! The app works without it thanks to dynamic detection.

## Testing Locally

For local testing, you don't need to set BASE_URL:

```bash
# Run without BASE_URL - uses localhost automatically
finch run -p 8080:8080 \
    -e SECRET_KEY=test \
    -e AWS_REGION=us-east-1 \
    digital-badge-app

# Or set it explicitly
finch run -p 8080:8080 \
    -e SECRET_KEY=test \
    -e AWS_REGION=us-east-1 \
    -e BASE_URL=http://localhost:8080 \
    digital-badge-app
```

Use the test script:
```bash
./test-local-finch.sh
```

## How It Works in Production

### Scenario 1: BASE_URL is Set (Optimal)

```
User Request → ALB → ECS Task
                      ↓
                get_base_url() checks env var
                      ↓
                Returns: https://digital-badge-app.ecs.us-east-1.on.aws
                      ↓
                QR codes and links use this URL
```

### Scenario 2: BASE_URL Not Set (Still Works!)

```
User Request → ALB (adds X-Forwarded-* headers) → ECS Task
                                                      ↓
                                            get_base_url() reads headers
                                                      ↓
                                            X-Forwarded-Proto: https
                                            X-Forwarded-Host: digital-badge-app.ecs.us-east-1.on.aws
                                                      ↓
                                            Constructs: https://digital-badge-app.ecs.us-east-1.on.aws
                                                      ↓
                                            QR codes and links use this URL
```

## Benefits of This Approach

### 1. Zero Configuration Required
- Deploy without knowing the URL in advance
- Application figures it out automatically
- No manual updates needed

### 2. Works in All Environments
- ✅ Local development (localhost)
- ✅ ECS Express Mode (dynamic detection)
- ✅ Custom domains (set BASE_URL explicitly)
- ✅ Behind reverse proxies (reads X-Forwarded headers)

### 3. Graceful Degradation
- If BASE_URL is set → uses it
- If not set → detects from request
- If no request context → falls back to localhost

### 4. No Deployment Delays
- Don't need to wait for URL before deploying
- Can deploy immediately
- URL is detected on first request

## Custom Domain Setup (Optional)

If you want to use a custom domain instead of the ECS-generated URL:

### Step 1: Set up your domain
```bash
# Point your domain to the ALB
# Get ALB DNS name from ECS service details
aws ecs describe-express-gateway-service --service-arn <arn>
```

### Step 2: Update BASE_URL
```bash
aws ecs update-express-gateway-service \
    --service-arn "<service-arn>" \
    --primary-container '{
        "environment": [
            {"name": "BASE_URL", "value": "https://badges.yourdomain.com"}
        ]
    }'
```

### Step 3: Restart tasks
```bash
# Tasks will restart automatically with the new BASE_URL
```

## Troubleshooting

### QR Codes Show Wrong URL

**Symptom:** QR codes point to localhost or wrong domain

**Solution:**
```bash
# Check current BASE_URL
aws ecs describe-express-gateway-service --service-arn <arn> | grep BASE_URL

# Update if needed
aws ecs update-express-gateway-service \
    --service-arn "<service-arn>" \
    --primary-container '{"environment": [{"name": "BASE_URL", "value": "https://your-actual-url"}]}'
```

### Links Don't Work

**Symptom:** Badge links return 404 or wrong domain

**Cause:** Usually happens if BASE_URL is set incorrectly

**Solution:**
```bash
# Remove BASE_URL to use dynamic detection
aws ecs update-express-gateway-service \
    --service-arn "<service-arn>" \
    --primary-container '{"environment": []}'

# Or set it correctly
aws ecs update-express-gateway-service \
    --service-arn "<service-arn>" \
    --primary-container '{"environment": [{"name": "BASE_URL", "value": "https://correct-url"}]}'
```

### Local Testing Shows Production URL

**Symptom:** Running locally but QR codes show production URL

**Cause:** BASE_URL environment variable is set

**Solution:**
```bash
# Don't set BASE_URL for local testing
unset BASE_URL

# Or set it to localhost
export BASE_URL=http://localhost:8080
```

## Code Changes Summary

The following files were updated to support dynamic BASE_URL:

### New Files
- ✅ `app/src/utils.py` - Dynamic URL detection utility

### Updated Files
- ✅ `app/src/routes/public.py` - Uses `get_base_url()`
- ✅ `app/src/routes/badge.py` - Uses `get_base_url()`
- ✅ `app/src/services/badge_generator.py` - Uses `get_base_url()`
- ✅ `deploy-to-ecs-express.sh` - Two-phase deployment

### No Changes Needed
- ✅ `app/src/models/badge.py` - Already accepts base_url parameter
- ✅ `app/__init__.py` - No BASE_URL dependency
- ✅ `Dockerfile` - No BASE_URL hardcoded

## Summary

**You don't need to configure BASE_URL!**

The application now:
1. ✅ Works without BASE_URL set
2. ✅ Automatically detects the correct URL from requests
3. ✅ Handles ECS Express Mode's dynamic URLs
4. ✅ Falls back gracefully in all environments
5. ✅ Supports custom domains when needed

**Just run the deployment script and you're done:**

```bash
./deploy-to-ecs-express.sh
```

The script handles everything automatically, including extracting and configuring the actual service URL after deployment.

---

**Questions?**

- Check the deployment script output for the actual URL
- Test locally with `./test-local-finch.sh`
- Review `ECS_EXPRESS_READINESS_REPORT.md` for more details
