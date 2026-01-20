#!/usr/bin/env python3
"""
Complete end-to-end test for custom fields feature
This test creates custom fields, configures a template, and creates a badge
"""
from app import create_app
from app.src.extensions import db
from app.src.models import CustomField, Template, Badge
from app.src.services import BadgeGenerator


def test_complete_workflow():
    """Test the complete custom fields workflow"""
    app = create_app()
    
    with app.app_context():
        print("Testing Custom Fields - Complete Workflow")
        print("=" * 60)
        
        # Step 1: Create custom fields
        print("\n1. Creating custom fields...")
        
        # Check if fields already exist
        score_field = CustomField.query.filter_by(field_key='score').first()
        if not score_field:
            score_field = CustomField(
                name='Score',
                field_key='score',
                description='Test score or game score',
                field_type='number',
                is_required=True
            )
            db.session.add(score_field)
            print("   ✓ Created 'Score' field")
        else:
            print("   ✓ 'Score' field already exists")
        
        grade_field = CustomField.query.filter_by(field_key='grade').first()
        if not grade_field:
            grade_field = CustomField(
                name='Grade',
                field_key='grade',
                description='Letter grade',
                field_type='text',
                is_required=False,
                default_value='A'
            )
            db.session.add(grade_field)
            print("   ✓ Created 'Grade' field")
        else:
            print("   ✓ 'Grade' field already exists")
        
        db.session.commit()
        
        # Step 2: Get or create a template with custom fields configured
        print("\n2. Configuring template with custom fields...")
        
        template = Template.query.filter_by(is_default=True).first()
        if not template:
            template = Template(
                name='Test Template',
                description='Template for testing custom fields',
                is_default=True
            )
            db.session.add(template)
        
        # Configure layout with custom fields
        layout_config = template.get_layout_config()
        layout_config['custom_fields'] = {
            'score': {
                'enabled': True,
                'x': 400,
                'y': 350,
                'size': 48,
                'color': '#FFD700'  # Gold
            },
            'grade': {
                'enabled': True,
                'x': 400,
                'y': 420,
                'size': 36,
                'color': '#4169E1'  # Royal Blue
            }
        }
        template.set_layout_config(layout_config)
        db.session.commit()
        print("   ✓ Template configured with custom fields")
        
        # Step 3: Create a badge with custom data
        print("\n3. Creating badge with custom data...")
        
        generator = BadgeGenerator(app.config)
        badge = generator.create_badge(
            template_id=template.id,
            recipient_name='John Doe',
            recipient_email='john@example.com',
            custom_data={
                'score': '95',
                'grade': 'A+'
            }
        )
        
        print(f"   ✓ Badge created: {badge.uuid}")
        print(f"   ✓ Image path: {badge.image_path}")
        print(f"   ✓ Custom data: {badge.get_custom_data()}")
        
        # Step 4: Verify the badge
        print("\n4. Verifying badge...")
        
        # Check that custom data was stored
        stored_data = badge.get_custom_data()
        if stored_data.get('score') == '95' and stored_data.get('grade') == 'A+':
            print("   ✓ Custom data stored correctly")
        else:
            print("   ✗ Custom data mismatch!")
            return False
        
        # Check that image was generated
        import os
        image_full_path = os.path.join(app.root_path, 'src', badge.image_path.lstrip('/'))
        if os.path.exists(image_full_path):
            print(f"   ✓ Badge image generated: {image_full_path}")
        else:
            print(f"   ✗ Badge image not found: {image_full_path}")
            return False
        
        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print(f"\nView the badge at: http://127.0.0.1:5001/badge/{badge.uuid}")
        print(f"Badge image: {badge.image_path}")
        
        return True


if __name__ == '__main__':
    success = test_complete_workflow()
    exit(0 if success else 1)
