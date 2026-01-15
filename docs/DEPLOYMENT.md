# Deployment Guide

## Local Development

### Quick Start

1. Run the quick start script:
```bash
./quickstart.sh
```

2. Start the development server:
```bash
uv run python run.py
```

3. Access the application:
- Home: http://127.0.0.1:5001
- Admin: http://127.0.0.1:5001/admin

## Production Deployment

### Using Docker

1. Build the Docker image:
```bash
docker build -t digital-badge-app .
```

2. Run the container:

**With IAM Role (Recommended for ECS/EKS):**
```bash
docker run -d \
  -p 8000:8000 \
  -e SECRET_KEY="your-secret-key" \
  -e AWS_REGION="us-east-1" \
  -e BASE_URL="https://yourdomain.com" \
  --name badge-app \
  digital-badge-app
```

**With AWS CLI Config (Local/Development):**
```bash
docker run -d \
  -p 8000:8000 \
  -v ~/.aws:/root/.aws:ro \
  -e SECRET_KEY="your-secret-key" \
  -e AWS_REGION="us-east-1" \
  -e BASE_URL="https://yourdomain.com" \
  --name badge-app \
  digital-badge-app
```

**With Environment Variables (Not Recommended):**
```bash
docker run -d \
  -p 8000:8000 \
  -e SECRET_KEY="your-secret-key" \
  -e AWS_REGION="us-east-1" \
  -e AWS_ACCESS_KEY_ID="$AWS_ACCESS_KEY_ID" \
  -e AWS_SECRET_ACCESS_KEY="$AWS_SECRET_ACCESS_KEY" \
  -e BASE_URL="https://yourdomain.com" \
  --name badge-app \
  digital-badge-app
```

### Using Gunicorn (Direct)

1. Install dependencies:
```bash
uv sync
```

2. Initialize database:
```bash
uv run python init_db.py
```

3. Run with gunicorn:
```bash
uv run gunicorn -w 4 -b 0.0.0.0:8000 wsgi:app
```

### Environment Variables

Required for production:

```bash
# Flask
SECRET_KEY=<strong-random-key>
FLASK_ENV=production

# AWS
AWS_REGION=us-east-1
# AWS credentials are NOT stored in environment variables
# Use IAM roles for EC2/ECS/Lambda or AWS CLI config

# Database (optional, defaults to SQLite)
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Application
BASE_URL=https://yourdomain.com
```

### AWS Credentials in Production

**Recommended: Use IAM Roles**

For EC2:
```bash
# Attach IAM role with Bedrock permissions to EC2 instance
# No credentials needed in code or environment
```

For ECS/Fargate:
```json
{
  "taskRoleArn": "arn:aws:iam::account:role/badge-app-task-role"
}
```

For Lambda:
```bash
# Lambda execution role automatically provides credentials
```

**Alternative: AWS CLI Configuration**
```bash
# On the server
aws configure
# Credentials stored in ~/.aws/credentials
```

**Not Recommended: Environment Variables**
```bash
# Only use for testing, not production
export AWS_ACCESS_KEY_ID=<key>
export AWS_SECRET_ACCESS_KEY=<secret>
```

## AWS Configuration

### IAM Permissions

Your AWS credentials need the following permissions:

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

### Enable Bedrock Models

1. Go to AWS Bedrock console
2. Navigate to Model access
3. Enable "Amazon Nova Canvas"
4. Wait for approval (usually instant)

## Database Options

### SQLite (Default)

Good for development and small deployments:
```bash
DATABASE_URL=sqlite:///badges.db
```

### PostgreSQL (Recommended for Production)

1. Install PostgreSQL driver:
```bash
uv add psycopg2-binary
```

2. Set DATABASE_URL:
```bash
DATABASE_URL=postgresql://user:password@localhost:5432/badges
```

### MySQL

1. Install MySQL driver:
```bash
uv add pymysql
```

2. Set DATABASE_URL:
```bash
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/badges
```

## Nginx Configuration

Example nginx configuration for reverse proxy:

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /path/to/app/src/static;
        expires 30d;
    }
}
```

## Systemd Service

Create `/etc/systemd/system/badge-app.service`:

```ini
[Unit]
Description=Digital Badge Platform
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/opt/badge-app
Environment="PATH=/opt/badge-app/.venv/bin"
ExecStart=/usr/local/bin/uv run gunicorn -w 4 -b 127.0.0.1:8000 wsgi:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable badge-app
sudo systemctl start badge-app
```

## Monitoring

### Health Check Endpoint

Add to `app/src/routes/public.py`:

```python
@bp.route('/health')
def health():
    return jsonify({'status': 'healthy'}), 200
```

### Logging

Configure logging in production:

```python
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    file_handler = RotatingFileHandler('logs/badge-app.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
```

## Security Considerations

1. **Use HTTPS**: Always use SSL/TLS in production
2. **Strong SECRET_KEY**: Generate with `python -c "import secrets; print(secrets.token_hex(32))"`
3. **AWS Credentials**: Use IAM roles when possible (EC2, ECS, Lambda)
4. **File Upload Limits**: Already configured to 16MB
5. **CORS**: Add Flask-CORS if needed for API access
6. **Rate Limiting**: Consider Flask-Limiter for API endpoints

## Backup

### Database Backup

SQLite:
```bash
sqlite3 badges.db ".backup 'backup.db'"
```

PostgreSQL:
```bash
pg_dump badges > backup.sql
```

### File Backup

Backup uploaded resources and generated badges:
```bash
tar -czf badge-files-backup.tar.gz app/src/static/uploads app/src/static/badges
```

## Scaling

### Horizontal Scaling

- Use a shared database (PostgreSQL/MySQL)
- Store uploaded files in S3 instead of local filesystem
- Use a load balancer (ALB, nginx)
- Run multiple gunicorn instances

### Vertical Scaling

Increase gunicorn workers:
```bash
uv run gunicorn -w 8 -b 0.0.0.0:8000 wsgi:app
```

Rule of thumb: `workers = (2 * CPU_cores) + 1`
