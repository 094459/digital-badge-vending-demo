from app.src.extensions import db
from datetime import datetime


class Resource(db.Model):
    """Resource model for logos, images, and assets"""
    __tablename__ = 'resources'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    resource_type = db.Column(db.String(50), nullable=False)  # logo, background, icon, etc.
    file_path = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'resource_type': self.resource_type,
            'file_path': self.file_path,
            'description': self.description,
            'created_at': self.created_at.isoformat()
        }
