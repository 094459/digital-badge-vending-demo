# Amazon ECS Express Mode Readiness Report
## Digital Badge Platform

**Date:** January 14, 2026  
**Application:** Digital Badge Platform (Flask)  
**Target Deployment:** Amazon ECS Express Mode

---

## Executive Summary

✅ **READY FOR DEPLOYMENT** with minor recommendations

Your Flask application is well-structured and nearly ready for ECS Express Mode deployment. The application follows best practices with proper containerization, environment-based configuration, and production-ready setup with Gunicorn.

**Readiness Score: 8.5/10**

---

## ✅ What's Already Great

### 1. Container Ready
- ✅ **Dockerfile exists** and follows best practices
- ✅ Uses Python 3.11 slim base image
- ✅ Properly configured with Gunicorn (4 workers)
- ✅ Exposes port 8000
- ✅ Database initialization included
- ✅ Uses `uv` for dependency management

### 2. Production Configuration
- ✅ **WSGI entry point** (`wsgi.py`) properly configured
- ✅ Environment variable-based configuration
- ✅ Gunicorn production server configured
- ✅ Proper application factory pattern
- ✅ Static file handling configured

### 3. AWS Integration
- ✅ **Boto3 configured** for AWS Bedrock integration
- ✅ Supports IAM role-based authentication (ideal for ECS)
- ✅ AWS region configuration via environment variables
- ✅ No hardcoded credentials

### 4. Database
- ✅ **SQLAlchemy ORM** with SQLite default
- ✅ Database initialization script (`init_db.py`)
- ✅ Automatic table creation on startup
- ✅ Configurable via `DATABASE_URL` environment variable

### 5. File Storage
- ✅ Organized static file structure
- ✅ Separate folders for uploads and generated badges
- ✅ Automatic directory creation

---

## ⚠️ Required Changes for ECS Express Mode

### 1. **CRITICAL: Add Health Check Endpoint**

ECS Express Mode requires a health check endpoint. Your application currently lacks one.

**Impact:** Without this, ECS cannot determine if your application is healthy, which may cause deployment issues.

**Solution:** Add a `/health` endpoint to `app/src/routes/public.py`

```python
@bp.route('/health')
def health():
    """Health check endpoint for ECS"""
    try:
        # Check database connectivity
        from app.src.models import Template
        Template.query.first()
        return jsonify({
            'status': 'healthy',
            'service': 'digital-badge-platform',
            'database': 'connected'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503
```

### 2. **IMPORTANT: Update Dockerfile for ECS**

Current Dockerfile needs adjustments for ECS Express Mode:

**Issues:**
- Database initialization runs at build time (should be runtime)
- No support for persistent storage
- Port binding needs to be flexible

**Recommended Dockerfile:**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml uv.lock ./
COPY app ./app
COPY wsgi.py init_db.py ./

# Install dependencies
RUN uv sync --frozen

# Create directories for runtime
RUN mkdir -p /app/instance /app/app/src/static/uploads /app/app/src/static/badges

# Expose port (ECS Express Mode uses 8080 by default)
EXPOSE 8080

# Initialize database and start server
CMD uv run python init_db.py && \
    uv run gunicorn -w 4 -b 0.0.0.0:8080 --timeout 120 wsgi:app
```

### 3. **RECOMMENDED: Update Port Configuration**

ECS Express Mode defaults to port 8080 for container traffic.

**Changes needed:**
- Update Dockerfile to expose port 8080
- Update Gunicorn to bind to port 8080
- Or specify `--primary-container containerPort=8000` when creating the service

---

## 📋 ECS Express Mode Prerequisites Checklist

### AWS Account Setup

- [ ] **AWS Account** with appropriate permissions
- [ ] **AWS CLI** installed and configured
- [ ] **Container image** pushed to Amazon ECR

### IAM Roles (Required)

#### Task Execution Role
```bash
# Create role
aws iam create-role --role-name ecsTaskExecutionRole \
    --assume-role-policy-document '{
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "ecs-tasks.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }'

# Attach policy
aws iam attach-role-policy --role-name ecsTaskExecutionRole \
    --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
```

#### Infrastructure Role
```bash
# Create role
aws iam create-role --role-name ecsInfrastructureRoleForExpressServices \
    --assume-role-policy-document '{
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "ecs.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }'

# Attach policy
aws iam attach-role-policy --role-name ecsInfrastructureRoleForExpressServices \
    --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSInfrastructureRoleforExpressGatewayServices
```

#### Task Role (for Bedrock Access)
```bash
# Create role
aws iam create-role --role-name badgeAppTaskRole \
    --assume-role-policy-document '{
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "ecs-tasks.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }'

# Create and attach Bedrock policy
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

---

## 🚀 Deployment Steps

### Step 1: Build and Push Container Image

```bash
# Build the image with Finch
finch build -t digital-badge-app .

# Create ECR repository
aws ecr create-repository --repository-name digital-badge-app --region us-east-1

# Tag for ECR
finch tag digital-badge-app:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/digital-badge-app:latest

# Login to ECR
aws ecr get-login-password --region us-east-1 | finch login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Push to ECR
finch push <account-id>.dkr.ecr.us-east-1.amazonaws.com/digital-badge-app:latest
```

**Note:** This guide uses Finch (AWS's open-source container tool). If you're using Docker, simply replace `finch` with `docker` in all commands.

### Step 2: Create Express Mode Service

**Basic Deployment:**
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

**Production Deployment with Custom Settings:**
```bash
aws ecs create-express-gateway-service \
    --execution-role-arn arn:aws:iam::<account-id>:role/ecsTaskExecutionRole \
    --infrastructure-role-arn arn:aws:iam::<account-id>:role/ecsInfrastructureRoleForExpressServices \
    --task-role-arn arn:aws:iam::<account-id>:role/badgeAppTaskRole \
    --primary-container '{
        "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/digital-badge-app:latest",
        "containerPort": 8080,
        "environment": [
            {"name": "FLASK_ENV", "value": "production"},
            {"name": "AWS_REGION", "value": "us-east-1"},
            {"name": "SECRET_KEY", "value": "<your-secret-key>"},
            {"name": "BASE_URL", "value": "https://digital-badge-app.ecs.us-east-1.on.aws"}
        ]
    }' \
    --service-name "digital-badge-app" \
    --cpu 1 \
    --memory 2 \
    --health-check-path "/health" \
    --scaling-target '{"minTaskCount": 2, "maxTaskCount": 10}' \
    --monitor-resources
```

### Step 3: Access Your Application

Once deployed, your application will be available at:
```
https://digital-badge-app.ecs.us-east-1.on.aws/
```

---

## ⚠️ Important Considerations

### 1. **Database Persistence**

**Current Issue:** SQLite database is stored in the container filesystem, which is ephemeral.

**Impact:** Data will be lost when containers restart or scale.

**Solutions:**

**Option A: Use Amazon RDS (Recommended for Production)**
```bash
# Create RDS PostgreSQL instance
# Update DATABASE_URL environment variable:
DATABASE_URL=postgresql://user:pass@rds-endpoint:5432/badges
```

**Option B: Use EFS for SQLite (Development/Testing)**
```bash
# Create EFS filesystem
# Mount to /app/instance in ECS task definition
# SQLite file persists across container restarts
```

**Option C: Use Amazon Aurora Serverless (Cost-Effective)**
```bash
# Aurora Serverless v2 with PostgreSQL
# Scales automatically with your application
```

### 2. **File Storage (Uploads & Generated Badges)**

**Current Issue:** Files stored in container filesystem are ephemeral.

**Impact:** Uploaded resources and generated badges will be lost on container restart.

**Solutions:**

**Option A: Amazon S3 (Recommended)**
- Store uploads in S3 bucket
- Serve via CloudFront CDN
- Update `image_service.py` and `badge_generator.py` to use S3

**Option B: Amazon EFS**
- Mount EFS to `/app/app/src/static`
- Files persist across containers
- Shared across all tasks

### 3. **Environment Variables & Secrets**

**Current Setup:** Environment variables passed directly in task definition.

**Recommendation:** Use AWS Secrets Manager for sensitive data:

```bash
# Store secret key
aws secretsmanager create-secret \
    --name badge-app/secret-key \
    --secret-string "your-secret-key"

# Reference in ECS task definition
"secrets": [
    {
        "name": "SECRET_KEY",
        "valueFrom": "arn:aws:secretsmanager:region:account:secret:badge-app/secret-key"
    }
]
```

### 4. **Logging**

ECS Express Mode automatically configures CloudWatch Logs. Your application logs will be available at:
```
/aws/ecs/express/digital-badge-app
```

**Recommendation:** Add structured logging to your Flask app for better observability.

### 5. **Auto Scaling**

ECS Express Mode includes auto-scaling by default based on CPU utilization.

**Current Configuration:**
- Default: 1 task minimum, scales up based on CPU
- Recommended: Set `minTaskCount: 2` for high availability

### 6. **Cost Considerations**

**Estimated Monthly Cost (us-east-1):**
- Fargate (1 vCPU, 2GB): ~$30/month per task
- Application Load Balancer: ~$16/month
- CloudWatch Logs: ~$0.50/GB ingested
- Data Transfer: Variable

**For 2 tasks running 24/7:** ~$76/month + logs + data transfer

---

## 🔒 Security Recommendations

### 1. **IAM Roles**
- ✅ Use IAM roles instead of access keys (already configured)
- ✅ Follow principle of least privilege
- ✅ Separate task execution role from task role

### 2. **Secrets Management**
- ⚠️ Move `SECRET_KEY` to AWS Secrets Manager
- ⚠️ Move `ADMIN_PASSWORD` to AWS Secrets Manager
- ✅ Never commit secrets to Git

### 3. **Network Security**
- ✅ ECS Express Mode creates security groups automatically
- ✅ HTTPS/TLS termination at ALB (automatic)
- ⚠️ Consider adding WAF for additional protection

### 4. **Application Security**
- ⚠️ Add authentication to admin routes (currently password-protected)
- ⚠️ Implement rate limiting for API endpoints
- ⚠️ Add CSRF protection for forms
- ✅ File upload validation already implemented (16MB limit)

---

## 📊 Monitoring & Observability

### CloudWatch Metrics (Automatic)
- CPU utilization
- Memory utilization
- Request count
- Target response time
- HTTP 5xx errors

### Recommended Additional Monitoring
- Application-level metrics (badge creation rate, AI generation success rate)
- Custom CloudWatch alarms for business metrics
- X-Ray for distributed tracing

---

## 🎯 Action Items Summary

### Must Do (Before Deployment)
1. ✅ Add `/health` endpoint
2. ✅ Update Dockerfile for port 8080
3. ✅ Create IAM roles (task execution, infrastructure, task)
4. ✅ Push image to ECR
5. ✅ Decide on database strategy (RDS vs EFS)
6. ✅ Decide on file storage strategy (S3 vs EFS)

### Should Do (For Production)
1. ⚠️ Move secrets to AWS Secrets Manager
2. ⚠️ Set up RDS PostgreSQL for database
3. ⚠️ Set up S3 for file storage
4. ⚠️ Configure CloudWatch alarms
5. ⚠️ Add structured logging
6. ⚠️ Set up backup strategy

### Nice to Have
1. 💡 Add CloudFront CDN for static assets
2. 💡 Implement caching layer (Redis/ElastiCache)
3. 💡 Add WAF for security
4. 💡 Set up CI/CD pipeline
5. 💡 Add X-Ray tracing

---

## 🧪 Testing Recommendations

### Before Deployment
```bash
# Test Finch build
finch build -t digital-badge-app .

# Test container locally
finch run -p 8080:8080 \
    -e SECRET_KEY=test \
    -e AWS_REGION=us-east-1 \
    -e BASE_URL=http://localhost:8080 \
    digital-badge-app

# Test health endpoint
curl http://localhost:8080/health

# Test badge creation
curl -X POST http://localhost:8080/api/badges \
    -H "Content-Type: application/json" \
    -d '{"recipient_name": "Test User"}'
```

### After Deployment
```bash
# Monitor deployment
aws ecs monitor-express-gateway-service \
    --service-arn <service-arn>

# Check service status
aws ecs describe-express-gateway-service \
    --service-arn <service-arn>

# Test application
curl https://digital-badge-app.ecs.us-east-1.on.aws/health
```

---

## 📚 Additional Resources

- [ECS Express Mode Documentation](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/express-service-overview.html)
- [Amazon Bedrock Nova Canvas](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-nova-canvas.html)
- [ECS Task IAM Roles](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-iam-roles.html)
- [Flask Production Best Practices](https://flask.palletsprojects.com/en/3.0.x/deploying/)

---

## ✅ Final Verdict

**Your application is READY for ECS Express Mode deployment** after implementing the health check endpoint and updating the Dockerfile. The application follows Flask best practices, has proper AWS integration, and is well-structured for containerized deployment.

**Recommended Timeline:**
- Implement required changes: 30 minutes
- Test locally: 15 minutes
- Deploy to ECS: 15 minutes
- **Total: ~1 hour to production**

**Risk Level:** Low (with required changes implemented)

---

*Report generated for Digital Badge Platform - January 14, 2026*
