from flask import Flask
from app.src.extensions import db
from app.src.routes import admin, badge, public, auth
from werkzeug.middleware.proxy_fix import ProxyFix
import os


def create_app():
    """Application factory pattern"""
    # Set template and static folders to src subdirectory
    app = Flask(
        __name__,
        template_folder='src/templates',
        static_folder='src/static'
    )
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///badges.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
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
    
    # Register blueprints
    app.register_blueprint(auth.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(badge.bp)
    app.register_blueprint(public.bp)
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    return app
