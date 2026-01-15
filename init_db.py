#!/usr/bin/env python3
"""Initialize database with default template"""
import os
from dotenv import load_dotenv
from app import create_app
from app.src.extensions import db
from app.src.models import Template

load_dotenv()

app = create_app()

with app.app_context():
    # Create tables
    db.create_all()
    
    # Check if default template exists
    default_template = Template.query.filter_by(is_default=True).first()
    
    if not default_template:
        # Create default template
        default_template = Template(
            name='Default Badge Template',
            description='Standard badge template with centered text',
            is_default=True
        )
        
        default_template.set_layout_config({
            'width': 800,
            'height': 600,
            'background_color': '#FFFFFF',
            'text_color': '#000000',
            'name_x': 400,
            'name_y': 300,
            'font_size': 48
        })
        
        db.session.add(default_template)
        db.session.commit()
        
        print('✓ Default template created')
    else:
        print('✓ Default template already exists')
    
    print('✓ Database initialized successfully')
