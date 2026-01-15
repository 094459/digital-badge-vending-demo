# Digital Badge Platform

A Flask-based web application for creating, managing, and sharing digital badges with AI-powered design generation using Amazon Bedrock Nova Canvas.

## Features

### Admin Features
- Create and manage badge templates
- Upload and manage resources (logos, backgrounds, icons)
- AI-powered badge design generation using Amazon Bedrock Nova Canvas
- Template layout editor
- Set default templates

### Badge Generation
- Create virtual badges from templates
- AI-generated badge designs
- Automatic QR code generation
- Unique public URLs for each badge
- LinkedIn sharing integration

### Public Access
- Public badge viewing pages
- Share badges on LinkedIn
- Download badge images and QR codes

## Architecture

The system follows this flow:

1. **Admin Setup**: Admin creates templates and uploads resources
2. **Badge Request**: User requests a badge (with optional template ID)
3. **Badge Generation**: System generates unique badge with UUID and public URL
4. **QR Code**: System creates QR code linking to badge URL
5. **Public Access**: Badge accessible via unique URI with LinkedIn sharing

## Tech Stack

- **Framework**: Flask (application factory pattern)
- **Database**: SQLAlchemy with SQLite (configurable)
- **Validation**: Pydantic
- **AI**: Amazon Bedrock Nova Canvas for image generation
- **Image Processing**: Pillow, qrcode
- **Package Management**: uv

## Setup

### Prerequisites

- Python 3.11+
- uv package manager
- AWS account with Bedrock access (us-east-1 or us-west-2)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd digital-badge-app
```

2. Install dependencies using uv:
```bash
uv sync
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

Required environment variables:
- `SECRET_KEY`: Flask secret key
- `AWS_REGION`: AWS region (us-east-1 or us-west-2)
- `BASE_URL`: Base URL for badge links (e.g., http://127.0.0.1:5001)

**AWS Credentials**: The application uses boto3's default credential chain:
1. Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
2. AWS CLI configuration (`~/.aws/credentials`)
3. IAM role (when running on EC2/ECS/Lambda)
4. Instance metadata service (IMDS)

**DO NOT store AWS credentials in .env file**

4. Initialize the database:
```bash
uv run python init_db.py
```

### Running Locally

Development server (127.0.0.1:5001):
```bash
uv run python run.py
```

### Running in Production

Using gunicorn:
```bash
uv run gunicorn -w 4 -b 0.0.0.0:8000 wsgi:app
```

## API Endpoints

### Badge API

**Create Badge**
```
POST /api/badges
Content-Type: application/json

{
  "template_id": 1,  // optional
  "recipient_name": "John Doe",
  "recipient_email": "john@example.com",  // optional, no validation
  "use_ai": false,  // optional
  "ai_prompt": "..."  // required if use_ai is true
}

Response:
{
  "badge": {...},
  "qr_code_url": "...",
  "public_url": "..."
}
```

**Get Badge**
```
GET /api/badges/<uuid>
```

**Get QR Code**
```
GET /api/badges/<uuid>/qr
```

### Admin API

**List Templates**
```
GET /admin/templates
```

**Create Template**
```
POST /admin/templates
Content-Type: application/json

{
  "name": "Template Name",
  "description": "Description",
  "is_default": false,
  "layout_config": {
    "width": 800,
    "height": 600,
    "background_color": "#FFFFFF",
    "text_color": "#000000",
    "name_x": 400,
    "name_y": 300
  }
}
```

**Upload Resource**
```
POST /admin/resources
Content-Type: multipart/form-data

file: <file>
name: "Resource Name"
resource_type: "logo|background|icon|image"
description: "Description"
```

**Generate AI Badge Design**
```
POST /admin/generate-ai-badge
Content-Type: application/json

{
  "prompt": "A professional certificate badge with gold borders"
}
```

## Project Structure

```
├── app/
│   ├── __init__.py              # Application factory
│   └── src/
│       ├── extensions.py        # Flask extensions
│       ├── models/              # Database models
│       │   ├── template.py
│       │   ├── badge.py
│       │   └── resource.py
│       ├── routes/              # API routes
│       │   ├── admin.py
│       │   ├── badge.py
│       │   └── public.py
│       ├── services/            # Business logic
│       │   ├── badge_generator.py
│       │   └── image_service.py
│       ├── static/              # Static files
│       │   ├── uploads/         # Uploaded resources
│       │   └── badges/          # Generated badges
│       └── templates/           # HTML templates
│           ├── base.html
│           ├── index.html
│           ├── badge.html
│           └── admin/
│               └── index.html
├── init_db.py                   # Database initialization
├── run.py                       # Development server
├── wsgi.py                      # Production WSGI
├── pyproject.toml              # Project dependencies
└── .env                        # Environment variables
```

## Usage Examples

### Creating a Simple Badge

```bash
curl -X POST http://127.0.0.1:5001/api/badges \
  -H "Content-Type: application/json" \
  -d '{
    "recipient_name": "Jane Smith",
    "recipient_email": "jane@example.com"
  }'
```

### Creating an AI-Generated Badge

```bash
curl -X POST http://127.0.0.1:5001/api/badges \
  -H "Content-Type: application/json" \
  -d '{
    "recipient_name": "John Doe",
    "use_ai": true,
    "ai_prompt": "A modern achievement badge with blue gradient background and gold star"
  }'
```

## AWS Bedrock Configuration

The application uses Amazon Bedrock Nova Canvas for AI image generation. Ensure:

1. Your AWS credentials have access to Bedrock
2. You're using us-east-1 or us-west-2 region
3. Nova Canvas model is enabled in your account

## License

MIT
