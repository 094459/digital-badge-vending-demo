from app.src.extensions import db
from datetime import datetime


class CustomField(db.Model):
    """Custom field definition for badge metadata"""
    __tablename__ = 'custom_fields'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)  # e.g., "Score", "Grade"
    field_key = db.Column(db.String(100), nullable=False, unique=True)  # e.g., "score", "grade"
    description = db.Column(db.Text)
    field_type = db.Column(db.String(50), default='text')  # text, number, date
    is_required = db.Column(db.Boolean, default=False)
    default_value = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'field_key': self.field_key,
            'description': self.description,
            'field_type': self.field_type,
            'is_required': self.is_required,
            'default_value': self.default_value,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
