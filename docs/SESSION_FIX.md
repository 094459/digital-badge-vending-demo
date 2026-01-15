# Session Cookie Fix for ECS Deployment

## Problem
Admin login wasn't working on ECS but worked locally. This was caused by Flask session cookies not being configured properly for HTTPS behind a load balancer.

## Root Cause
When running behind AWS Application Load Balancer (ALB):
1. ALB terminates SSL/TLS (HTTPS)
2. ALB forwards requests to containers over HTTP
3. Flask doesn't know the original request was HTTPS
4. Flask sets session cookies without the `Secure` flag
5. Browser rejects cookies or doesn't send them back over HTTPS

## Solution Applied

### 1. Session Cookie Security Settings
Added production-specific session configuration in `app/__init__.py`:
- `SESSION_COOKIE_SECURE = True` - Only send cookies over HTTPS
- `SESSION_COOKIE_HTTPONLY = True` - Prevent JavaScript access (XSS protection)
- `SESSION_COOKIE_SAMESITE = 'Lax'` - CSRF protection
- `PERMANENT_SESSION_LIFETIME = 3600` - 1 hour session timeout

### 2. Proxy Headers Trust
Added `ProxyFix` middleware to trust ALB proxy headers:
- Reads `X-Forwarded-Proto` to detect HTTPS
- Reads `X-Forwarded-For` for client IP
- Reads `X-Forwarded-Host` for original host
- This allows Flask to correctly identify HTTPS requests

## How to Deploy the Fix

1. Rebuild the container image:
```bash
finch build --platform linux/amd64 -t digital-badge-app:latest .
```

2. Redeploy using the deployment script:
```bash
./deploy-to-ecs-express.sh
```

Or manually:
```bash
# Tag and push
ECR_URI="<your-account-id>.dkr.ecr.eu-west-1.amazonaws.com/digital-badge-app"
finch tag digital-badge-app:latest $ECR_URI:latest
aws ecr get-login-password --region eu-west-1 | finch login --username AWS --password-stdin $ECR_URI
finch push $ECR_URI:latest

# Update the service (it will pull the new image)
aws ecs update-express-gateway-service \
    --service-arn <your-service-arn> \
    --region eu-west-1 \
    --primary-container file://container-config.json
```

## Testing
After deployment:
1. Navigate to `https://<your-app-url>/admin`
2. You should be redirected to `/login`
3. Enter your ADMIN_PASSWORD
4. You should be logged in and redirected to the admin dashboard
5. Session should persist across page refreshes

## Why This Only Affected ECS
- **Local**: Running directly on HTTP (no load balancer), so no HTTPS/proxy issues
- **ECS**: Running behind ALB with HTTPS termination, requires proxy awareness

## Related Files
- `app/__init__.py` - Flask app factory with session and proxy configuration
- `app/src/routes/auth.py` - Login/logout routes
- `app/src/routes/admin.py` - Admin routes requiring authentication
