# Digital Badge Platform

A Flask-based web application for creating, managing, and sharing digital badges with AI-powered design generation using Amazon Bedrock Nova Canvas.

## Features

### Admin Features
- Create and manage badge templates
- Upload and manage resources (logos, backgrounds, icons)
- AI-powered badge design generation using Amazon Bedrock Nova Canvas
- AI-powered badge frame generation
- Template layout editor with live preview
- Custom fields for badge metadata
- Export/import templates and resources
- Set default templates

### Badge Generation
- Create virtual badges from templates
- AI-generated badge designs via Strands Agents SDK
- Automatic QR code generation
- Unique public URLs for each badge
- LinkedIn sharing integration
- Custom field values per badge

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
- **Database**: SQLAlchemy with PostgreSQL (RDS) or SQLite for local dev
- **Validation**: Pydantic
- **AI Text**: Amazon Bedrock Nova 2 Lite via Strands Agents SDK
- **AI Image**: Amazon Bedrock Nova Canvas
- **Storage**: Amazon S3 (with Flask proxy) or local filesystem
- **Image Processing**: Pillow, qrcode
- **Package Management**: uv
- **Container**: Docker/Finch, deployed to Amazon ECS Express Mode

## Setup

### Prerequisites

- Python 3.11+
- uv package manager
- AWS account with Bedrock access
- (Optional) Finch or Docker for container builds

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
uv run gunicorn -w 4 -b 0.0.0.0:8080 --timeout 120 wsgi:app
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|---|---|---|
| `SECRET_KEY` | Flask secret key | `dev-secret-key` |
| `ADMIN_PASSWORD` | Admin panel password | (required) |
| `FLASK_ENV` | `development` or `production` | `development` |
| `BASE_URL` | Base URL for badge links | `http://127.0.0.1:5001` |
| `AWS_REGION` | AWS region for ECS deployment | `eu-west-1` |
| `BEDROCK_REGION` | AWS region for Bedrock API calls | Falls back to `AWS_REGION` |

### Database

The app supports PostgreSQL (recommended for production) and SQLite (local dev).

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | Full database connection string | `sqlite:///badges.db` |
| `DB_HOST` | RDS PostgreSQL hostname | — |
| `DB_PORT` | Database port | `5432` |
| `DB_NAME` | Database name | `badges` |
| `DB_USERNAME` | Database user | `postgres` |
| `DB_PASSWORD` | Database password | — |

The database URI is resolved in this order:
1. `DATABASE_URL` if set (takes precedence)
2. Built from individual `DB_*` vars if `DB_HOST` is set
3. Falls back to `sqlite:///badges.db`

### S3 Storage

When `S3_BUCKET` is set, all file storage (badge images, QR codes, uploaded resources) uses S3 instead of the local filesystem. Flask proxies `/static/*` requests to S3 transparently, so all existing URLs continue to work.

| Variable | Description | Default |
|---|---|---|
| `S3_BUCKET` | S3 bucket name for file storage | — (uses local filesystem) |
| `S3_PREFIX` | Optional key prefix in the bucket | — |

Without `S3_BUCKET`, files are stored locally in `app/src/static/uploads/` and `app/src/static/badges/`.

### AWS Credentials

The application uses boto3's default credential chain:
1. Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
2. AWS CLI configuration (`~/.aws/credentials`)
3. IAM role (when running on EC2/ECS/Lambda)

**Do not store AWS credentials in .env files.**

## Deployment

### Build and Push Container to ECR

```bash
./build-and-push-ecr.sh
```

This builds a linux/amd64 container image using Finch and pushes it to ECR. The script auto-creates the ECR repository if it doesn't exist.

### Deploy to ECS Express Mode

```bash
./deploy-to-ecs-express.sh
```

This handles IAM roles, ECR push, and ECS Express Mode service creation/update.

### Required IAM Permissions (Task Role)

The ECS task role (`badgeAppTaskRole`) needs:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": ["bedrock:InvokeModel"],
            "Resource": ["arn:aws:bedrock:*::foundation-model/amazon.nova-canvas-v1:0"]
        },
        {
            "Effect": "Allow",
            "Action": ["s3:PutObject", "s3:GetObject", "s3:DeleteObject"],
            "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME/*"
        },
        {
            "Effect": "Allow",
            "Action": ["s3:ListBucket"],
            "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME"
        }
    ]
}
```

## API Endpoints

### Badge API

**Create Badge**
```
POST /api/badges
Content-Type: application/json

{
  "template_id": 1,
  "recipient_name": "John Doe",
  "recipient_email": "john@example.com",
  "custom_data": {"score": "95", "grade": "A+"},
  "use_ai": false,
  "ai_prompt": "..."
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

**Templates**: `GET/POST /admin/templates`, `GET/PUT/DELETE /admin/templates/<id>`

**Resources**: `GET/POST /admin/resources`, `DELETE /admin/resources/<id>`

**Custom Fields**: `GET/POST /admin/custom-fields`, `PUT/DELETE /admin/custom-fields/<id>`

**AI Generation**: `POST /admin/generate-ai-badge`, `POST /admin/generate-ai-frame`

**Export/Import**: `GET /admin/export`, `POST /admin/import`

**Preview**: `POST /admin/preview-badge`

## Project Structure

```
├── app/
│   ├── __init__.py                  # Application factory
│   └── src/
│       ├── extensions.py            # Flask extensions (SQLAlchemy)
│       ├── utils.py                 # Utility functions
│       ├── models/
│       │   ├── badge.py             # Badge model
│       │   ├── template.py          # Template model
│       │   ├── resource.py          # Resource model
│       │   └── custom_field.py      # Custom field model
│       ├── routes/
│       │   ├── admin.py             # Admin routes
│       │   ├── auth.py              # Authentication
│       │   ├── badge.py             # Badge API routes
│       │   └── public.py            # Public routes
│       ├── services/
│       │   ├── badge_generator.py   # Badge image generation
│       │   ├── image_service.py     # Bedrock Nova Canvas client
│       │   ├── storage_service.py   # S3/local file storage
│       │   ├── strands_agent_service.py  # Strands AI agent
│       │   └── export_import_service.py  # Export/import
│       ├── static/
│       │   ├── uploads/             # Uploaded resources
│       │   └── badges/              # Generated badges
│       └── templates/               # HTML templates
├── build-and-push-ecr.sh           # Build & push container to ECR
├── deploy-to-ecs-express.sh        # Full ECS deployment
├── Dockerfile                       # Container definition
├── init_db.py                       # Database initialization
├── run.py                           # Development server
├── wsgi.py                          # Production WSGI entry point
└── pyproject.toml                   # Dependencies (managed by uv)
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

## License

MIT
