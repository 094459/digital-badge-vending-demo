import json
import os
import zipfile
import shutil
from io import BytesIO
from datetime import datetime
from app.src.models import Template, Resource
from app.src.extensions import db


class ExportImportService:
    """Service for exporting and importing application configuration"""
    
    def export_application(self, app_config) -> BytesIO:
        """
        Export templates, resources, and their files (excluding badges)
        
        Returns:
            BytesIO: ZIP file containing all exportable data
        """
        # Create in-memory ZIP file
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Export metadata
            metadata = {
                'export_date': datetime.utcnow().isoformat(),
                'version': '1.0',
                'description': 'Digital Badge Platform Export'
            }
            zip_file.writestr('metadata.json', json.dumps(metadata, indent=2))
            
            # Export templates
            templates = Template.query.all()
            templates_data = [self._template_to_export_dict(t) for t in templates]
            zip_file.writestr('templates.json', json.dumps(templates_data, indent=2))
            
            # Export resources
            resources = Resource.query.all()
            resources_data = [r.to_dict() for r in resources]
            zip_file.writestr('resources.json', json.dumps(resources_data, indent=2))
            
            # Export resource files
            upload_folder = app_config.get('UPLOAD_FOLDER')
            for resource in resources:
                file_path = resource.file_path.lstrip('/')
                full_path = os.path.join(upload_folder, os.path.basename(file_path))
                
                if os.path.exists(full_path):
                    # Store files in 'files/' directory within ZIP
                    zip_file.write(full_path, f'files/{os.path.basename(file_path)}')
        
        zip_buffer.seek(0)
        return zip_buffer
    
    def import_application(self, zip_file_path, app_config) -> dict:
        """
        Import templates, resources, and files from export ZIP
        Overwrites existing templates and resources
        
        Args:
            zip_file_path: Path to the ZIP file to import
            app_config: Flask app configuration
            
        Returns:
            dict: Import statistics
        """
        stats = {
            'templates_imported': 0,
            'resources_imported': 0,
            'files_imported': 0,
            'errors': []
        }
        
        try:
            with zipfile.ZipFile(zip_file_path, 'r') as zip_file:
                # Read metadata
                metadata = json.loads(zip_file.read('metadata.json'))
                
                # Clear existing templates and resources
                Template.query.delete()
                Resource.query.delete()
                db.session.commit()
                
                # Import templates
                templates_data = json.loads(zip_file.read('templates.json'))
                for template_dict in templates_data:
                    template = Template(
                        name=template_dict['name'],
                        description=template_dict.get('description'),
                        layout_config=json.dumps(template_dict['layout_config']),
                        is_default=template_dict.get('is_default', False)
                    )
                    db.session.add(template)
                    stats['templates_imported'] += 1
                
                db.session.commit()
                
                # Import resources
                resources_data = json.loads(zip_file.read('resources.json'))
                upload_folder = app_config.get('UPLOAD_FOLDER')
                
                # Ensure upload folder exists
                os.makedirs(upload_folder, exist_ok=True)
                
                for resource_dict in resources_data:
                    resource = Resource(
                        name=resource_dict['name'],
                        resource_type=resource_dict['resource_type'],
                        file_path=resource_dict['file_path'],
                        description=resource_dict.get('description')
                    )
                    db.session.add(resource)
                    stats['resources_imported'] += 1
                
                db.session.commit()
                
                # Extract files
                for file_info in zip_file.infolist():
                    if file_info.filename.startswith('files/'):
                        filename = os.path.basename(file_info.filename)
                        target_path = os.path.join(upload_folder, filename)
                        
                        with zip_file.open(file_info) as source:
                            with open(target_path, 'wb') as target:
                                shutil.copyfileobj(source, target)
                        
                        stats['files_imported'] += 1
                
        except Exception as e:
            stats['errors'].append(str(e))
            db.session.rollback()
            raise
        
        return stats
    
    def _template_to_export_dict(self, template: Template) -> dict:
        """Convert template to export-friendly dictionary"""
        return {
            'name': template.name,
            'description': template.description,
            'layout_config': template.get_layout_config(),
            'is_default': template.is_default
        }
