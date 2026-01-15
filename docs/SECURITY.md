# Security Guidelines

## AWS Credentials Management

### ✅ Recommended Practices

**1. Use IAM Roles (Production)**
- EC2 instances: Attach IAM role to instance
- ECS/Fargate: Use task roles
- Lambda: Use execution roles
- No credentials in code or configuration files

**2. Use AWS CLI Configuration (Development)**
```bash
aws configure
# Credentials stored in ~/.aws/credentials
# Never commit this file to git
```

**3. Use Environment Variables (Temporary/Testing)**
```bash
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
# Only for current session
```

### ❌ Never Do This

**DON'T store credentials in .env files**
```bash
# BAD - Never do this
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

**DON'T commit credentials to git**
```bash
# Check before committing
git diff
git status
# Ensure .env is in .gitignore
```

**DON'T hard-code credentials**
```python
# BAD - Never do this
client = boto3.client(
    'bedrock-runtime',
    aws_access_key_id='AKIAIOSFODNN7EXAMPLE',
    aws_secret_access_key='wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'
)
```

**DON'T share credentials**
- Each developer should have their own AWS credentials
- Use AWS SSO for team access
- Rotate credentials regularly

## Credential Leak Prevention

### Git Pre-commit Hook

Create `.git/hooks/pre-commit`:
```bash
#!/bin/bash

# Check for AWS credentials in staged files
if git diff --cached | grep -E 'AWS_ACCESS_KEY_ID|AWS_SECRET_ACCESS_KEY|AKIA[0-9A-Z]{16}'; then
    echo "ERROR: AWS credentials detected in commit!"
    echo "Remove credentials before committing."
    exit 1
fi
```

Make it executable:
```bash
chmod +x .git/hooks/pre-commit
```

### Scan for Leaked Credentials

```bash
# Install git-secrets
brew install git-secrets  # macOS
# or
git clone https://github.com/awslabs/git-secrets.git
cd git-secrets
make install

# Setup
git secrets --install
git secrets --register-aws

# Scan repository
git secrets --scan
```

### If Credentials Are Leaked

1. **Immediately rotate credentials**
```bash
aws iam create-access-key --user-name your-user
aws iam delete-access-key --access-key-id OLD_KEY --user-name your-user
```

2. **Remove from git history**
```bash
# Use BFG Repo-Cleaner
brew install bfg
bfg --replace-text passwords.txt
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

3. **Check AWS CloudTrail** for unauthorized access

## Application Security

### Secret Key

Generate a strong secret key:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Store in .env (not committed):
```bash
SECRET_KEY=your_generated_secret_key_here
```

### File Upload Security

The application includes:
- File size limits (16MB)
- Secure filename handling
- Type validation

Additional recommendations:
```python
# Add to admin.py
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'svg'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
```

### SQL Injection Prevention

Using SQLAlchemy ORM prevents SQL injection:
```python
# Safe - parameterized query
Badge.query.filter_by(uuid=uuid).first()

# Unsafe - never do this
db.session.execute(f"SELECT * FROM badges WHERE uuid='{uuid}'")
```

### XSS Prevention

Flask's Jinja2 templates auto-escape by default:
```html
<!-- Safe - auto-escaped -->
<p>{{ badge.recipient_name }}</p>

<!-- Unsafe - only use for trusted content -->
<p>{{ badge.recipient_name | safe }}</p>
```

### CSRF Protection

Add Flask-WTF for CSRF protection:
```bash
uv add flask-wtf
```

```python
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
csrf = CSRFProtect(app)
```

## Network Security

### HTTPS Only

Production configuration:
```python
# Force HTTPS
if not app.debug:
    @app.before_request
    def before_request():
        if request.url.startswith('http://'):
            url = request.url.replace('http://', 'https://', 1)
            return redirect(url, code=301)
```

### CORS Configuration

If needed, use Flask-CORS:
```bash
uv add flask-cors
```

```python
from flask_cors import CORS

CORS(app, resources={
    r"/api/*": {
        "origins": ["https://yourdomain.com"],
        "methods": ["GET", "POST"],
        "allow_headers": ["Content-Type"]
    }
})
```

### Rate Limiting

Add Flask-Limiter:
```bash
uv add flask-limiter
```

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@bp.route('/api/badges', methods=['POST'])
@limiter.limit("10 per minute")
def create_badge():
    # ...
```

## Database Security

### Connection Security

For PostgreSQL:
```bash
# Use SSL
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require
```

### Backup Encryption

```bash
# Encrypt backups
gpg --symmetric --cipher-algo AES256 backup.sql
```

## Monitoring & Logging

### Log Security Events

```python
import logging

# Don't log sensitive data
logger.info(f"Badge created for {badge.uuid}")  # Good
logger.info(f"Badge created with data {badge_data}")  # Bad if contains PII
```

### AWS CloudTrail

Enable CloudTrail to monitor API calls:
```bash
aws cloudtrail create-trail --name badge-app-trail \
    --s3-bucket-name my-cloudtrail-bucket
```

## Compliance

### GDPR Considerations

- Store minimal personal data
- Implement data deletion
- Provide data export
- Document data processing

### PII Handling

```python
# Encrypt email addresses
from cryptography.fernet import Fernet

key = Fernet.generate_key()
cipher = Fernet(key)

encrypted_email = cipher.encrypt(email.encode())
```

## Security Checklist

- [ ] AWS credentials NOT in .env or code
- [ ] .env file in .gitignore
- [ ] Strong SECRET_KEY generated
- [ ] HTTPS enabled in production
- [ ] File upload validation
- [ ] Rate limiting configured
- [ ] CSRF protection enabled
- [ ] SQL injection prevention (using ORM)
- [ ] XSS prevention (auto-escaping)
- [ ] CloudTrail enabled
- [ ] Regular credential rotation
- [ ] Security updates applied
- [ ] Backups encrypted
- [ ] Logs don't contain sensitive data

## Resources

- [AWS Security Best Practices](https://aws.amazon.com/security/best-practices/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Flask Security](https://flask.palletsprojects.com/en/latest/security/)
- [Boto3 Credentials](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html)
