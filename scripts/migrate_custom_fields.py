#!/usr/bin/env python3
"""
Database migration script to add custom fields support
"""
from app import create_app
from app.src.extensions import db
from app.src.models import CustomField, Badge
import sys


def migrate():
    """Run the migration"""
    app = create_app()
    
    with app.app_context():
        print("Starting migration...")
        
        try:
            # Create all tables (will create custom_fields table)
            db.create_all()
            print("✓ Created custom_fields table")
            
            # Check if custom_data column exists in badges table
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('badges')]
            
            if 'custom_data' not in columns:
                print("Adding custom_data column to badges table...")
                with db.engine.connect() as conn:
                    conn.execute(db.text('ALTER TABLE badges ADD COLUMN custom_data TEXT'))
                    conn.commit()
                print("✓ Added custom_data column to badges table")
            else:
                print("✓ custom_data column already exists in badges table")
            
            print("\nMigration completed successfully!")
            print("\nYou can now:")
            print("1. Create custom fields in the admin dashboard")
            print("2. Configure them in templates")
            print("3. Use them when creating badges")
            
        except Exception as e:
            print(f"✗ Migration failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == '__main__':
    migrate()
