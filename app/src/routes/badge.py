from flask import Blueprint, request, jsonify, current_app, send_file
from app.src.services import BadgeGenerator
from app.src.models import Badge
from app.src.utils import get_base_url
from pydantic import BaseModel, Field
from typing import Optional
import os

bp = Blueprint('badge', __name__, url_prefix='/api')


class BadgeRequest(BaseModel):
    """Badge creation request schema"""
    template_id: Optional[int] = None
    recipient_name: Optional[str] = None
    recipient_email: Optional[str] = None
    badge_data: Optional[dict] = None
    use_ai: Optional[bool] = False
    ai_prompt: Optional[str] = None


@bp.route('/badges', methods=['POST'])
def create_badge():
    """
    Create a new virtual badge
    
    Request body:
    {
        "template_id": 1,  // optional, uses default if not provided
        "recipient_name": "John Doe",
        "recipient_email": "john@example.com",  // optional, no validation
        "badge_data": {},  // optional additional data
        "use_ai": false,  // optional, use AI generation
        "ai_prompt": "..."  // required if use_ai is true
    }
    
    Response:
    {
        "badge": {...},
        "qr_code_url": "...",
        "public_url": "..."
    }
    """
    try:
        data = request.get_json()
        badge_request = BadgeRequest(**data)
        
        generator = BadgeGenerator(current_app.config)
        
        if badge_request.use_ai and badge_request.ai_prompt:
            badge = generator.generate_with_ai(
                prompt=badge_request.ai_prompt,
                template_id=badge_request.template_id,
                recipient_name=badge_request.recipient_name,
                recipient_email=badge_request.recipient_email
            )
        else:
            badge = generator.create_badge(
                template_id=badge_request.template_id,
                recipient_name=badge_request.recipient_name,
                recipient_email=badge_request.recipient_email,
                badge_data=badge_request.badge_data
            )
        
        base_url = get_base_url()
        
        return jsonify({
            'badge': badge.to_dict(base_url),
            'qr_code_url': f"{base_url}{badge.qr_code_path}",
            'public_url': badge.get_public_url(base_url)
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@bp.route('/badges/<uuid>', methods=['GET'])
def get_badge(uuid):
    """Get badge details by UUID"""
    badge = Badge.query.filter_by(uuid=uuid).first_or_404()
    base_url = get_base_url()
    return jsonify(badge.to_dict(base_url))


@bp.route('/badges/<uuid>/qr', methods=['GET'])
def get_qr_code(uuid):
    """Get QR code image for badge"""
    badge = Badge.query.filter_by(uuid=uuid).first_or_404()
    
    qr_path = os.path.join(
        current_app.root_path, 
        'src', 
        badge.qr_code_path.lstrip('/')
    )
    
    return send_file(qr_path, mimetype='image/png')
