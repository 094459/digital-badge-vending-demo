# Getting Started with Digital Badge Platform

## Quick Start (5 minutes)

### 1. Prerequisites

- Python 3.11 or higher
- uv package manager ([installation guide](https://docs.astral.sh/uv/getting-started/installation/))
- AWS account with Bedrock access

### 2. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd digital-badge-app

# Run quick start script
./quickstart.sh
```

### 3. Configure AWS Credentials

The application uses boto3's default credential chain. Choose one method:

**Option 1: AWS CLI (Recommended for local development)**
```bash
aws configure
# Enter your credentials when prompted
```

**Option 2: Environment Variables**
```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_REGION=us-east-1
```

**Option 3: IAM Role (Recommended for production)**
- Attach IAM role to EC2/ECS/Lambda instance
- No credentials needed in code

Edit `.env` file for application settings:
```bash
AWS_REGION=us-east-1
BASE_URL=http://127.0.0.1:5001
SECRET_KEY=your-secret-key
```

**DO NOT store AWS credentials in .env file**

### 4. Start the Server

```bash
uv run python run.py
```

Visit: http://127.0.0.1:5001

## First Steps

### Create Your First Badge

1. **Via Web Interface**:
   - Go to http://127.0.0.1:5001
   - Enter recipient name and email
   - Click "Generate Badge"
   - Get QR code and public URL

2. **Via API**:
```bash
curl -X POST http://127.0.0.1:5001/api/badges \
  -H "Content-Type: application/json" \
  -d '{
    "recipient_name": "John Doe",
    "recipient_email": "john@example.com"
  }'
```

### Access Admin Panel

1. Go to http://127.0.0.1:5001/admin
2. Create templates
3. Upload resources (logos, backgrounds)
4. Generate AI badge designs

### Test AI Badge Generation

```bash
curl -X POST http://127.0.0.1:5001/api/badges \
  -H "Content-Type: application/json" \
  -d '{
    "recipient_name": "Jane Smith",
    "use_ai": true,
    "ai_prompt": "A professional achievement badge with blue gradient and gold star"
  }'
```

## Project Structure

```
digital-badge-app/
├── app/                      # Main application
│   ├── __init__.py          # App factory
│   └── src/
│       ├── models/          # Database models
│       ├── routes/          # API endpoints
│       ├── services/        # Business logic
│       ├── static/          # Static files
│       └── templates/       # HTML templates
├── run.py                   # Development server
├── wsgi.py                  # Production WSGI
├── init_db.py              # Database setup
├── test_api.py             # API tests
├── quickstart.sh           # Quick setup script
├── README.md               # Full documentation
├── ARCHITECTURE.md         # Architecture details
└── DEPLOYMENT.md           # Deployment guide
```

## Common Tasks

### Create a Template

```python
# Via Python
from app import create_app
from app.src.models import Template
from app.src.extensions import db

app = create_app()
with app.app_context():
    template = Template(
        name="Gold Achievement",
        description="Gold-themed achievement badge",
        is_default=False
    )
    template.set_layout_config({
        'width': 800,
        'height': 600,
        'background_color': '#FFD700',
        'text_color': '#000000',
        'name_x': 400,
        'name_y': 300
    })
    db.session.add(template)
    db.session.commit()
```

### Upload a Resource

```bash
curl -X POST http://127.0.0.1:5001/admin/resources \
  -F "file=@logo.png" \
  -F "name=Company Logo" \
  -F "resource_type=logo"
```

### View a Badge

```bash
# Get badge details
curl http://127.0.0.1:5001/api/badges/{uuid}

# View in browser
open http://127.0.0.1:5001/badge/{uuid}
```

## Testing

Run the test suite:
```bash
# Start the server first
uv run python run.py

# In another terminal
uv run python test_api.py
```

## Troubleshooting

### Database Issues

Reset database:
```bash
rm badges.db
uv run python init_db.py
```

### AWS Credentials

Verify credentials:
```bash
aws bedrock list-foundation-models --region us-east-1
```

### Port Already in Use

Change port in `run.py`:
```python
app.run(host='127.0.0.1', port=5002, debug=True)
```

### Import Errors

Reinstall dependencies:
```bash
uv sync --reinstall
```

## Next Steps

1. **Customize Templates**: Create templates matching your brand
2. **Upload Resources**: Add logos and backgrounds
3. **Test AI Generation**: Experiment with different prompts
4. **Deploy**: Follow [DEPLOYMENT.md](DEPLOYMENT.md) for production setup
5. **Integrate**: Use the API in your applications

## Resources

- [Full Documentation](README.md)
- [Architecture Guide](ARCHITECTURE.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Amazon Bedrock Nova Canvas](https://docs.aws.amazon.com/nova/latest/userguide/image-gen-code-examples.html)
- [Strands Agents](https://strandsagents.com/)

## Support

For issues and questions:
1. Check the documentation
2. Review error logs
3. Verify AWS credentials and permissions
4. Test with simple badge creation first

## Example Workflows

### Workflow 1: Simple Badge

1. Start server
2. Go to home page
3. Enter name
4. Generate badge
5. Share on LinkedIn

### Workflow 2: AI-Designed Badge

1. Go to admin panel
2. Use AI badge generator
3. Enter design prompt
4. Preview generated design
5. Create template from design
6. Generate badges using template

### Workflow 3: Batch Generation

```python
import requests

recipients = [
    {"name": "Alice", "email": "alice@example.com"},
    {"name": "Bob", "email": "bob@example.com"},
    {"name": "Charlie", "email": "charlie@example.com"}
]

for recipient in recipients:
    response = requests.post(
        "http://127.0.0.1:5001/api/badges",
        json=recipient
    )
    badge = response.json()
    print(f"Badge created for {recipient['name']}: {badge['public_url']}")
```

## Tips

- Use descriptive template names
- Test AI prompts in admin panel first
- Keep resource files under 16MB
- Use PNG format for transparency
- Set one template as default
- Back up database regularly
- Monitor AWS Bedrock costs
- Use environment-specific .env files

Happy badge creating! 🎖️
