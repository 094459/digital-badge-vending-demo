from app.src.extensions import db
from datetime import datetime
import uuid
import json


class Badge(db.Model):
    """Virtual badge model"""
    __tablename__ = 'badges'
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    template_id = db.Column(db.Integer, db.ForeignKey('templates.id'), nullable=False)
    recipient_name = db.Column(db.String(200))
    recipient_email = db.Column(db.String(200))
    badge_data = db.Column(db.Text)  # JSON string with badge-specific data
    custom_data = db.Column(db.Text)  # JSON string with custom field values
    image_path = db.Column(db.String(500))  # Path to generated badge image
    qr_code_path = db.Column(db.String(500))  # Path to QR code image
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_custom_data(self):
        """Parse custom data from JSON"""
        return json.loads(self.custom_data) if self.custom_data else {}
    
    def set_custom_data(self, data_dict):
        """Set custom data as JSON"""
        self.custom_data = json.dumps(data_dict) if data_dict else None
    
    def get_public_url(self, base_url):
        """Get the public URL for this badge"""
        return f"{base_url}/badge/{self.uuid}"
    
    def to_dict(self, base_url=None):
        result = {
            'id': self.id,
            'uuid': self.uuid,
            'template_id': self.template_id,
            'recipient_name': self.recipient_name,
            'recipient_email': self.recipient_email,
            'custom_data': self.get_custom_data(),
            'image_path': self.image_path,
            'qr_code_path': self.qr_code_path,
            'created_at': self.created_at.isoformat()
        }
        if base_url:
            result['public_url'] = self.get_public_url(base_url)
        return result
