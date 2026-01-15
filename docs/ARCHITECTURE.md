# Architecture Documentation

## System Overview

The Digital Badge Platform is a Flask-based web application that enables creation, management, and sharing of digital badges with AI-powered design generation.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                          System                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐         ┌────────────────────────────┐        │
│  │ Admin Page   │────────▶│ Resources - templates      │        │
│  │              │         │ used for badges            │        │
│  │ - Upload     │         └────────────┬───────────────┘        │
│  │   templates  │                      │                        │
│  │ - Review/    │                      ▼                        │
│  │   delete     │         ┌────────────────────────────┐        │
│  └──────────────┘         │ Generate unique uuid badge │        │
│                           │ and uri                     │        │
│  ┌──────────────┐    ②   │                            │   ③    │
│  │ Generate     │────────▶│ - Use template badge input │───────▶│
│  │ Badge        │         │   to generate image        │        │
│  │              │         │ - Host credentials page    │        │
│  │ - Which      │         │   for badge                │        │
│  │   template   │         └────────────┬───────────────┘        │
│  │   and design │                      │                        │
│  └──────┬───────┘                      │ ④                      │
│         │                              │                        │
│         │ ①                            ▼                        │
│         │                   ┌──────────────────────┐            │
│  ┌──────▼───────┐           │ QR code to unique    │            │
│  │ Badge/       │           │ badge/achievement    │            │
│  │ Credential   │           └──────────────────────┘            │
│  │ Requested    │                                               │
│  └──────────────┘                                               │
│                                                                  │
│  End User                                                        │
│                                                                  │
│                           ┌──────────────────────┐              │
│                           │ Badges hosted        │              │
│                           │ on public uris       │              │
│                           └──────────┬───────────┘              │
│                                      │ ⑤                        │
│                                      ▼                          │
│                           ┌──────────────────────┐              │
│                           │ Share LinkedIn link  │              │
│                           │ to badge             │              │
│                           └──────────────────────┘              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Flow Description

### 1. Badge Request (Step ①)
- End user requests a badge/credential
- Request includes optional template_id
- If no template_id provided, system uses default template

### 2. Badge Generation (Step ②)
- System receives request with template selection
- Badge Generator service creates unique UUID
- Template configuration is loaded from database

### 3. Badge Creation (Step ③)
- Unique badge record created in database
- Badge image generated using:
  - Template-based composition (default)
  - AI generation via Amazon Bedrock Nova Canvas (optional)
- Badge hosted at unique URI: `/badge/{uuid}`
- QR code generated linking to badge URI

### 4. QR Code Generation (Step ④)
- QR code created pointing to badge public URL
- Returned to requestor for distribution
- Stored for future access

### 5. Public Access & Sharing (Step ⑤)
- Badge accessible via public URI
- LinkedIn sharing button integrated
- Direct download options for badge and QR code

## Component Architecture

### Application Layer

```
┌─────────────────────────────────────────────────────────┐
│                    Flask Application                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Admin      │  │    Badge     │  │   Public     │  │
│  │   Routes     │  │    API       │  │   Routes     │  │
│  │              │  │              │  │              │  │
│  │ - Templates  │  │ - Create     │  │ - View Badge │  │
│  │ - Resources  │  │ - Retrieve   │  │ - Share      │  │
│  │ - AI Gen     │  │ - QR Code    │  │              │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         │                 │                 │           │
│         └─────────────────┼─────────────────┘           │
│                           │                             │
│                  ┌────────▼────────┐                    │
│                  │   Services      │                    │
│                  │                 │                    │
│                  │ - BadgeGen      │                    │
│                  │ - ImageService  │                    │
│                  │ - StrandsAgent  │                    │
│                  └────────┬────────┘                    │
│                           │                             │
│                  ┌────────▼────────┐                    │
│                  │   Data Models   │                    │
│                  │                 │                    │
│                  │ - Template      │                    │
│                  │ - Badge         │                    │
│                  │ - Resource      │                    │
│                  └────────┬────────┘                    │
│                           │                             │
│                  ┌────────▼────────┐                    │
│                  │    Database     │                    │
│                  │   (SQLAlchemy)  │                    │
│                  └─────────────────┘                    │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### External Services

```
┌─────────────────────────────────────────────────────────┐
│              External Service Integration                │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────────────────────────────────┐           │
│  │      Amazon Bedrock (Nova Canvas)        │           │
│  │                                          │           │
│  │  - Text-to-Image Generation              │           │
│  │  - Image Editing (Inpainting)            │           │
│  │  - High-quality badge designs            │           │
│  └──────────────────────────────────────────┘           │
│                                                          │
│  ┌──────────────────────────────────────────┐           │
│  │         LinkedIn Sharing API             │           │
│  │                                          │           │
│  │  - Share badge links                     │           │
│  │  - Professional credential sharing       │           │
│  └──────────────────────────────────────────┘           │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Data Models

### Template
```python
{
    "id": int,
    "name": str,
    "description": str,
    "layout_config": {
        "width": int,
        "height": int,
        "background_color": str,
        "text_color": str,
        "name_x": int,
        "name_y": int,
        "font_size": int
    },
    "is_default": bool,
    "created_at": datetime,
    "updated_at": datetime
}
```

### Badge
```python
{
    "id": int,
    "uuid": str,  # Unique identifier
    "template_id": int,
    "recipient_name": str,
    "recipient_email": str,
    "badge_data": dict,  # Additional metadata
    "image_path": str,
    "qr_code_path": str,
    "created_at": datetime
}
```

### Resource
```python
{
    "id": int,
    "name": str,
    "resource_type": str,  # logo, background, icon, image
    "file_path": str,
    "description": str,
    "created_at": datetime
}
```

## API Endpoints

### Public Routes
- `GET /` - Home page
- `GET /badge/{uuid}` - View badge page

### Badge API
- `POST /api/badges` - Create new badge
- `GET /api/badges/{uuid}` - Get badge details
- `GET /api/badges/{uuid}/qr` - Get QR code image

### Admin API
- `GET /admin` - Admin dashboard
- `GET /admin/templates` - List templates
- `POST /admin/templates` - Create template
- `PUT /admin/templates/{id}` - Update template
- `DELETE /admin/templates/{id}` - Delete template
- `GET /admin/resources` - List resources
- `POST /admin/resources` - Upload resource
- `DELETE /admin/resources/{id}` - Delete resource
- `POST /admin/generate-ai-badge` - Generate AI badge preview

## Security Considerations

### Authentication & Authorization
- Admin routes should be protected (add authentication middleware)
- API endpoints should implement rate limiting
- File uploads validated for type and size

### Data Protection
- AWS credentials stored in environment variables
- Database credentials not in code
- SECRET_KEY for session management

### Input Validation
- Pydantic models for request validation
- File upload restrictions (16MB limit)
- SQL injection prevention via SQLAlchemy ORM

## Scalability Considerations

### Horizontal Scaling
- Stateless application design
- Database connection pooling
- Shared file storage (S3) for multi-instance deployments

### Performance Optimization
- Static file caching
- Database query optimization
- Async image generation (optional)
- CDN for badge images

### Storage Strategy
- Local filesystem for development
- S3 for production deployments
- Database for metadata only

## Technology Stack

### Backend
- **Framework**: Flask 3.0+
- **ORM**: SQLAlchemy
- **Validation**: Pydantic
- **WSGI Server**: Gunicorn

### AI/ML
- **Image Generation**: Amazon Bedrock Nova Canvas
- **Agent Framework**: Strands Agents (optional)

### Image Processing
- **Library**: Pillow (PIL)
- **QR Codes**: qrcode

### Database
- **Development**: SQLite
- **Production**: PostgreSQL (recommended)

### Package Management
- **Tool**: uv

## Deployment Options

1. **Docker Container**
   - Containerized application
   - Easy deployment to any container platform

2. **Traditional Server**
   - Systemd service
   - Nginx reverse proxy
   - Gunicorn WSGI server

3. **Cloud Platforms**
   - AWS Elastic Beanstalk
   - AWS ECS/Fargate
   - Heroku
   - Google Cloud Run

## Future Enhancements

### Planned Features
- User authentication and authorization
- Badge expiration dates
- Badge verification system
- Analytics dashboard
- Email notifications
- Batch badge generation
- Custom fonts and styling
- Badge templates marketplace

### Technical Improvements
- Redis caching layer
- Celery for async tasks
- GraphQL API option
- WebSocket for real-time updates
- Multi-language support
- Advanced AI features with Strands Agents
