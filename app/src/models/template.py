from app.src.extensions import db
from datetime import datetime
import json


class Template(db.Model):
    """Badge template model"""
    __tablename__ = 'templates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    layout_config = db.Column(db.Text, nullable=False)  # JSON string with layout configuration
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    badges = db.relationship('Badge', backref='template', lazy=True)
    
    def get_layout_config(self):
        """Parse layout config from JSON"""
        return json.loads(self.layout_config) if self.layout_config else {}
    
    def set_layout_config(self, config_dict):
        """Set layout config as JSON"""
        self.layout_config = json.dumps(config_dict)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'layout_config': self.get_layout_config(),
            'is_default': self.is_default,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
