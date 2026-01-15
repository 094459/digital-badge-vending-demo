from flask import Blueprint, render_template, request, jsonify, current_app, send_file, redirect, url_for, session
from werkzeug.utils import secure_filename
from app.src.models import Template, Resource
from app.src.extensions import db
from app.src.services import ImageService
from app.src.services.export_import_service import ExportImportService
import os
import json
import tempfile

bp = Blueprint('admin', __name__, url_prefix='/admin')


def require_auth():
    """Check if user is authenticated"""
    if not session.get('authenticated'):
        return redirect(url_for('auth.login', next=request.url))
    return None


@bp.route('/')
def index():
    """Admin dashboard"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    templates = Template.query.all()
    resources = Resource.query.all()
    
    # Convert resources to dictionaries for JSON serialization
    resources_dict = [r.to_dict() for r in resources]
    
    return render_template('admin/index.html', templates=templates, resources=resources, resources_json=resources_dict)


@bp.route('/templates', methods=['GET'])
def list_templates():
    """List all templates"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    templates = Template.query.all()
    return jsonify([t.to_dict() for t in templates])


@bp.route('/templates/<int:template_id>', methods=['GET'])
def get_template(template_id):
    """Get a single template"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    template = Template.query.get_or_404(template_id)
    return jsonify(template.to_dict())


@bp.route('/templates', methods=['POST'])
def create_template():
    """Create a new template"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    data = request.get_json()
    
    template = Template(
        name=data['name'],
        description=data.get('description'),
        is_default=data.get('is_default', False)
    )
    
    # Set layout config
    layout_config = data.get('layout_config', {})
    template.set_layout_config(layout_config)
    
    # If this is default, unset other defaults
    if template.is_default:
        Template.query.filter_by(is_default=True).update({'is_default': False})
    
    db.session.add(template)
    db.session.commit()
    
    return jsonify(template.to_dict()), 201


@bp.route('/templates/<int:template_id>', methods=['PUT'])
def update_template(template_id):
    """Update a template"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    template = Template.query.get_or_404(template_id)
    data = request.get_json()
    
    template.name = data.get('name', template.name)
    template.description = data.get('description', template.description)
    
    if 'layout_config' in data:
        template.set_layout_config(data['layout_config'])
    
    if data.get('is_default'):
        Template.query.filter_by(is_default=True).update({'is_default': False})
        template.is_default = True
    
    db.session.commit()
    
    return jsonify(template.to_dict())


@bp.route('/templates/<int:template_id>', methods=['DELETE'])
def delete_template(template_id):
    """Delete a template"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    template = Template.query.get_or_404(template_id)
    
    if template.is_default:
        return jsonify({'error': 'Cannot delete default template'}), 400
    
    db.session.delete(template)
    db.session.commit()
    
    return '', 204


@bp.route('/resources', methods=['GET'])
def list_resources():
    """List all resources"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    resources = Resource.query.all()
    return jsonify([r.to_dict() for r in resources])


@bp.route('/resources', methods=['POST'])
def upload_resource():
    """Upload a new resource"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    resource = Resource(
        name=request.form.get('name', filename),
        resource_type=request.form.get('resource_type', 'image'),
        file_path=f"/static/uploads/{filename}",
        description=request.form.get('description')
    )
    
    db.session.add(resource)
    db.session.commit()
    
    return jsonify(resource.to_dict()), 201


@bp.route('/resources/<int:resource_id>', methods=['DELETE'])
def delete_resource(resource_id):
    """Delete a resource"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    resource = Resource.query.get_or_404(resource_id)
    
    # Delete file
    filepath = os.path.join(current_app.root_path, 'src', resource.file_path.lstrip('/'))
    if os.path.exists(filepath):
        os.remove(filepath)
    
    db.session.delete(resource)
    db.session.commit()
    
    return '', 204


@bp.route('/generate-ai-badge', methods=['POST'])
def generate_ai_badge():
    """Generate a badge design using AI"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    data = request.get_json()
    prompt = data.get('prompt')
    style = data.get('style')  # Optional style text to append to prompt
    
    if not prompt:
        return jsonify({'error': 'Prompt is required'}), 400
    
    try:
        # Append style to prompt if provided
        full_prompt = prompt
        if style:
            full_prompt = f"{prompt}, {style}"
        
        image_service = ImageService()
        image_bytes = image_service.generate_badge_image(
            prompt=full_prompt
        )
        
        # Save as resource
        import uuid
        filename = f"ai_generated_{uuid.uuid4()}.png"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        
        with open(filepath, 'wb') as f:
            f.write(image_bytes)
        
        # Create resource record
        resource = Resource(
            name=f"AI Generated: {prompt[:50]}",
            resource_type='ai_generated',
            file_path=f"/static/uploads/{filename}",
            description=f"Generated with prompt: {prompt}"
        )
        
        db.session.add(resource)
        db.session.commit()
        
        return jsonify({
            'image_url': f"/static/uploads/{filename}",
            'resource_id': resource.id,
            'message': 'Badge design generated and saved as resource'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/generate-ai-frame', methods=['POST'])
def generate_ai_frame():
    """Generate a decorative frame/border using AI"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    data = request.get_json()
    prompt = data.get('prompt')
    width = data.get('width', 1024)
    height = data.get('height', 1024)
    style = data.get('style')  # Optional style text to append to prompt
    
    if not prompt:
        return jsonify({'error': 'Prompt is required'}), 400
    
    try:
        # Enhance prompt to strongly emphasize transparent center and border-only design
        # Don't add floral language - respect the user's prompt
        enhanced_prompt = (
            f"Create a decorative border frame with the following design: {prompt}. "
            f"IMPORTANT: Only draw the border/frame around the edges. "
            f"The center must be completely empty and transparent so content can show through. "
            f"Think of it as a picture frame - only the frame itself, not the picture. "
            f"PNG format with alpha transparency in the center area."
        )
        
        # Append style to prompt if provided
        if style:
            enhanced_prompt = f"{enhanced_prompt} Style: {style}."
        
        image_service = ImageService()
        image_bytes = image_service.generate_badge_image(
            prompt=enhanced_prompt,
            width=int(width),
            height=int(height)
        )
        
        # Post-process to ensure center transparency
        from PIL import Image
        import io
        
        img = Image.open(io.BytesIO(image_bytes)).convert('RGBA')
        pixels = img.load()
        img_width, img_height = img.size
        
        # Define the center region (leave 20% border on each side)
        border_percent = 0.15
        left_border = int(img_width * border_percent)
        right_border = int(img_width * (1 - border_percent))
        top_border = int(img_height * border_percent)
        bottom_border = int(img_height * (1 - border_percent))
        
        # Make center region transparent
        for y in range(top_border, bottom_border):
            for x in range(left_border, right_border):
                # Get current pixel
                r, g, b, a = pixels[x, y]
                # Make it transparent
                pixels[x, y] = (r, g, b, 0)
        
        # Save processed image
        import uuid
        filename = f"ai_frame_{uuid.uuid4()}.png"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        img.save(filepath, 'PNG')
        
        # Create resource record
        resource = Resource(
            name=f"AI Frame: {prompt[:50]}",
            resource_type='frame',
            file_path=f"/static/uploads/{filename}",
            description=f"Frame generated with prompt: {prompt} ({width}x{height})"
        )
        
        db.session.add(resource)
        db.session.commit()
        
        return jsonify({
            'image_url': f"/static/uploads/{filename}",
            'resource_id': resource.id,
            'message': 'Frame generated and saved as resource'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/preview-badge', methods=['POST'])
def preview_badge():
    """Create a temporary preview badge for testing template"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    from app.src.models import Badge
    import uuid
    
    data = request.get_json()
    
    try:
        # Create a temporary template in memory (not saved to DB)
        temp_template = Template(
            name=data.get('name', 'Preview Template'),
            description='Temporary preview template'
        )
        temp_template.set_layout_config(data.get('layout_config', {}))
        
        # Create a preview badge
        badge = Badge(
            uuid=str(uuid.uuid4()),
            template_id=1,  # Will use temp config instead
            recipient_name='John Doe',
            recipient_email='preview@example.com'
        )
        
        db.session.add(badge)
        db.session.flush()
        
        # Generate badge image using the preview template config
        from app.src.services import BadgeGenerator
        generator = BadgeGenerator(current_app.config)
        
        # Manually generate with preview config
        layout_config = temp_template.get_layout_config()
        badge_image_path = generator._generate_badge_image_with_config(badge, layout_config)
        badge.image_path = badge_image_path
        
        # Generate QR code
        qr_code_path = generator._generate_qr_code(badge)
        badge.qr_code_path = qr_code_path
        
        db.session.commit()
        
        return jsonify({
            'badge_uuid': badge.uuid,
            'message': 'Preview badge created'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/export', methods=['GET'])
def export_application():
    """Export all templates, resources, and files (excluding badges)"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    try:
        export_service = ExportImportService()
        zip_buffer = export_service.export_application(current_app.config)
        
        # Generate filename with timestamp
        from datetime import datetime
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f'badge_platform_export_{timestamp}.zip'
        
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/import', methods=['POST'])
def import_application():
    """Import templates, resources, and files from export ZIP"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith('.zip'):
        return jsonify({'error': 'File must be a ZIP archive'}), 400
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
            file.save(temp_file.name)
            temp_path = temp_file.name
        
        # Import the data
        export_service = ExportImportService()
        stats = export_service.import_application(temp_path, current_app.config)
        
        # Clean up temp file
        os.unlink(temp_path)
        
        if stats['errors']:
            return jsonify({
                'error': 'Import completed with errors',
                'stats': stats
            }), 500
        
        return jsonify({
            'message': 'Import successful',
            'stats': stats
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
