from flask import Flask, Response
from app.src.extensions import db
from app.src.routes import admin, badge, public, auth
from app.src.services.storage_service import StorageService
from werkzeug.middleware.proxy_fix import ProxyFix
import os


def create_app():
    """Application factory pattern"""

    # Check if S3 storage is configured — if so, disable Flask's built-in static handler
    # so our proxy route can serve files from S3 instead
    s3_bucket = os.getenv('S3_BUCKET')
    static_folder_arg = None if s3_bucket else 'src/static'

    # Set template and static folders to src subdirectory
    app = Flask(
        __name__,
        template_folder='src/templates',
        static_folder=static_folder_arg,
        static_url_path='/static'
    )
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    # Build database URI from individual env vars, DATABASE_URL, or fallback to SQLite
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        db_host = os.getenv('DB_HOST')
        if db_host:
            db_user = os.getenv('DB_USERNAME', 'postgres')
            db_pass = os.getenv('DB_PASSWORD', '')
            db_port = os.getenv('DB_PORT', '5432')
            db_name = os.getenv('DB_NAME', 'badges')
            database_url = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
        else:
            database_url = 'sqlite:///badges.db'
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Log database connection info (mask password for security)
    if database_url.startswith('postgresql'):
        # postgresql://user:pass@host:port/dbname
        safe_url = database_url.split('@')[-1] if '@' in database_url else database_url
        print(f"[DB] Connecting to PostgreSQL: {safe_url}")
    else:
        print(f"[DB] Connecting to SQLite: {database_url}")
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'src', 'static', 'uploads')
    app.config['BADGE_FOLDER'] = os.path.join(app.root_path, 'src', 'static', 'badges')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    
    # Session configuration for production (behind load balancer)
    flask_env = os.getenv('FLASK_ENV', 'development')
    if flask_env == 'production':
        app.config['SESSION_COOKIE_SECURE'] = True  # Only send cookie over HTTPS
        app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access
        app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
        app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour session timeout
        
        # Trust proxy headers from ALB (X-Forwarded-For, X-Forwarded-Proto, etc.)
        # This is required for Flask to correctly detect HTTPS when behind a load balancer
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    
    # Ensure directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['BADGE_FOLDER'], exist_ok=True)
    
    # Initialize extensions
    db.init_app(app)

    # Initialize storage service (S3 or local filesystem)
    storage = StorageService()
    app.config['STORAGE_SERVICE'] = storage

    # S3 proxy route — serves files from S3 via Flask when S3_BUCKET is set
    if storage.is_s3():
        import mimetypes

        @app.route('/static/<path:filename>')
        def serve_static(filename):
            """Proxy static file requests to S3, fall back to local files"""
            data = storage.load_bytes(filename)
            if data is not None:
                content_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
                return Response(data, content_type=content_type)
            
            # Fall back to serving from local src/static/ directory
            local_path = os.path.join(app.root_path, 'src', 'static', filename)
            if os.path.exists(local_path):
                from flask import send_file
                return send_file(local_path)
            
            return Response('Not found', status=404)
    
    # Register blueprints
    app.register_blueprint(auth.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(badge.bp)
    app.register_blueprint(public.bp)
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    return app
