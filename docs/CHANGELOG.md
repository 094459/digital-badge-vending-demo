# Changelog

## [Security Update] - AWS Credentials Management

### Changed

**AWS Credentials Handling**
- ✅ Removed AWS credentials from `.env.example`
- ✅ Updated `.env` to remove credential fields
- ✅ Added clear warnings against storing credentials in files
- ✅ Updated all documentation to reflect secure credential practices

**Code Updates**
- `app/src/services/image_service.py`: Added comments explaining boto3 credential chain
- `.env.example`: Removed AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY fields
- `.env`: Removed credential fields, added security warnings
- `.gitignore`: Added warning about never committing credentials

**Documentation Updates**
- `README.md`: Updated credential configuration section
- `GETTING_STARTED.md`: Added three credential methods (AWS CLI, env vars, IAM roles)
- `DEPLOYMENT.md`: Updated with IAM role recommendations
- `PROJECT_SUMMARY.md`: Updated credential section
- `Dockerfile`: Added comments about credential handling

**New Documentation**
- `AWS_CREDENTIALS.md`: Comprehensive guide to AWS credential configuration
- `AWS_SETUP_QUICKSTART.md`: Quick reference for AWS setup
- `SECURITY.md`: Complete security guidelines and best practices

**Script Updates**
- `quickstart.sh`: Added AWS credential verification check

### Security Improvements

**Credential Chain Priority**
1. Environment variables (temporary/testing)
2. AWS CLI configuration (~/.aws/credentials) - **Recommended for development**
3. IAM roles (EC2/ECS/Lambda) - **Recommended for production**
4. Instance metadata service (IMDS)

**Best Practices Implemented**
- ✅ No credentials in configuration files
- ✅ No credentials in code
- ✅ Clear documentation on secure methods
- ✅ Git pre-commit hook example
- ✅ Credential leak prevention guide
- ✅ IAM policy examples

### Migration Guide

**If you have credentials in .env:**

1. **Remove credentials from .env:**
```bash
# Edit .env and remove these lines:
# AWS_ACCESS_KEY_ID=...
# AWS_SECRET_ACCESS_KEY=...
```

2. **Configure AWS CLI (Recommended):**
```bash
aws configure
# Enter your credentials when prompted
```

3. **Or use environment variables (temporary):**
```bash
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
```

4. **Verify configuration:**
```bash
aws sts get-caller-identity
```

5. **Test application:**
```bash
uv run python run.py
```

### Documentation Structure

```
├── README.md                    # Main documentation
├── GETTING_STARTED.md          # Quick start guide
├── AWS_CREDENTIALS.md          # Detailed credential guide
├── AWS_SETUP_QUICKSTART.md     # Quick AWS setup reference
├── SECURITY.md                 # Security best practices
├── ARCHITECTURE.md             # System architecture
├── DEPLOYMENT.md               # Production deployment
├── PROJECT_SUMMARY.md          # Project overview
└── CHANGELOG.md                # This file
```

### Breaking Changes

**None** - The application still works with all credential methods. This update only removes insecure practices from documentation and examples.

### Recommendations

**For Development:**
```bash
# Use AWS CLI configuration
aws configure
```

**For Production:**
- Use IAM roles attached to EC2/ECS/Lambda instances
- Never store credentials in files or environment variables
- Enable CloudTrail for audit logging

**For CI/CD:**
- Use temporary credentials from AWS STS
- Use OIDC providers (GitHub Actions, GitLab CI)
- Rotate credentials regularly

### Testing

All existing functionality remains unchanged:
- ✅ Badge creation works
- ✅ AI generation works
- ✅ Admin panel works
- ✅ Public badge viewing works
- ✅ QR code generation works

### Support

For questions about AWS credential configuration:
1. See [AWS_SETUP_QUICKSTART.md](AWS_SETUP_QUICKSTART.md)
2. See [AWS_CREDENTIALS.md](AWS_CREDENTIALS.md)
3. See [SECURITY.md](SECURITY.md)

### References

- [AWS CLI Configuration](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html)
- [Boto3 Credentials](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html)
- [AWS Security Best Practices](https://aws.amazon.com/security/best-practices/)
- [IAM Roles for EC2](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/iam-roles-for-amazon-ec2.html)
