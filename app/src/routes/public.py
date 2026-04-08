from flask import Blueprint, render_template, redirect, url_for, jsonify, current_app, session, request
from app.src.models import Badge
from app.src.extensions import db
from app.src.services.storage_service import StorageService
from app.src.utils import get_base_url
import os

bp = Blueprint('public', __name__)


def require_auth():
    """Check if user is authenticated"""
    if not session.get('authenticated'):
        return redirect(url_for('auth.login', next=request.url))
    return None


@bp.route('/health')
def health():
    """Health check endpoint for ECS Express Mode"""
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


@bp.route('/')
def index():
    """Home page"""
    from app.src.models import Template, CustomField
    templates = Template.query.all()
    custom_fields = CustomField.query.all()
    return render_template('index.html', templates=templates, custom_fields=custom_fields)


@bp.route('/badges')
def badges_list():
    """List all issued badges"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    from app.src.models import Badge
    badges = Badge.query.order_by(Badge.created_at.desc()).all()
    base_url = get_base_url()
    return render_template('badges_list.html', badges=badges, base_url=base_url)


@bp.route('/badges/<int:badge_id>/delete', methods=['POST'])
def delete_badge(badge_id):
    """Delete a badge"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    from app.src.models import Badge
    badge = Badge.query.get_or_404(badge_id)
    
    # Delete associated files from storage
    storage = current_app.config.get('STORAGE_SERVICE', StorageService())
    badge_folder = os.path.join(current_app.root_path, 'src', 'static', 'badges')
    
    if badge.image_path:
        relative = storage.file_path_to_relative(badge.image_path)
        storage.delete(relative, badge_folder)
    
    if badge.qr_code_path:
        relative = storage.file_path_to_relative(badge.qr_code_path)
        storage.delete(relative, badge_folder)
    
    db.session.delete(badge)
    db.session.commit()
    
    return jsonify({'message': 'Badge deleted successfully'})


@bp.route('/badge/<uuid>')
def view_badge(uuid):
    """Public badge view page"""
    from urllib.parse import quote
    
    badge = Badge.query.filter_by(uuid=uuid).first_or_404()
    base_url = get_base_url()
    
    # LinkedIn share URL with properly encoded URL parameter
    badge_url = badge.get_public_url(base_url)
    linkedin_share_url = f"https://www.linkedin.com/sharing/share-offsite/?url={quote(badge_url, safe='')}"
    
    return render_template(
        'badge.html', 
        badge=badge,
        badge_url=badge_url,
        linkedin_share_url=linkedin_share_url
    )
