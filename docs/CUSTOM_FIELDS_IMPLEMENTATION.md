# Custom Fields (Data Ingestion) Implementation

## Overview
Adding support for dynamic metadata fields (like Score, Grade, Date) that can be inserted into badges.

## Status: COMPLETED ✅

## Implementation Summary

The custom fields feature allows admins to define dynamic metadata fields that can be:
1. Created and managed in the admin dashboard
2. Configured with positioning and styling in templates
3. Filled in during badge creation (web form or API)
4. Rendered on the generated badge images

## Completed Steps:

### 1. Database Model ✅
- Created `app/src/models/custom_field.py`
- Fields: id, name, field_key, description, field_type, is_required, default_value
- Added to `__init__.py` exports

### 2. Badge Model Update ✅
- Added `custom_data` column to Badge model (JSON text field)
- Added `get_custom_data()` and `set_custom_data()` methods
- Updated `to_dict()` to include custom_data

### 3. Admin Routes ✅
- Added CustomField import to admin.py
- Updated index route to pass custom_fields to template
- Added CRUD endpoints:
  - GET /admin/custom-fields - List all
  - POST /admin/custom-fields - Create
  - PUT /admin/custom-fields/<id> - Update
  - DELETE /admin/custom-fields/<id> - Delete

### 4. Admin UI ✅
- Added "Custom Fields (Data Ingestion)" section in admin dashboard
- Table showing existing custom fields with ID, name, field_key, type, required, default value
- "Create New Field" button
- Custom Field modal for create/edit with all field properties
- JavaScript functions for CRUD operations

### 5. Template Editor ✅
- Added custom fields section to template editor
- For each custom field:
  - Enable/disable checkbox
  - X/Y position controls
  - Font size control
  - Color picker with text input
- Settings show/hide when checkbox is toggled
- Configuration saved in template.layout_config.custom_fields
- Template loading populates custom field checkboxes and values from saved config

### 6. Badge Creation UI ✅
- Updated public index route to pass custom_fields
- Badge creation form dynamically shows custom field inputs
- Supports text, number, and date field types
- Shows required indicator (*) for required fields
- Shows field descriptions as help text
- JavaScript collects custom field data and sends in API request

### 7. Badge API ✅
- Updated POST /api/badges endpoint to accept custom_data parameter
- BadgeRequest Pydantic model includes optional custom_data dict
- Badge generator receives and stores custom_data

### 8. Badge Generator ✅
- Updated badge_generator.py to render custom fields
- Reads custom field values from badge.custom_data
- Reads positioning/styling from template.layout_config.custom_fields
- Renders text at specified positions with specified font size and color
- Only renders enabled fields that have values

### 9. Database Migration ✅
- Created migrate_custom_fields.py script
- Adds custom_fields table
- Adds custom_data column to badges table
- Migration executed successfully

## Usage Example:

### 1. Define Custom Field (Admin Dashboard):
```
Name: Score
Field Key: score
Type: number
Required: Yes
Description: Game score or test result
```

### 2. Configure in Template (Template Editor):
```
Custom Fields:
  ☑ Score (score)
    X Position: 600
    Y Position: 400
    Font Size: 48
    Color: #FFD700 (gold)
```

### 3. Create Badge (Web Form):
```
Recipient Name: John Doe
Score: 95
```

### 4. Create Badge (API):
```json
POST /api/badges
{
  "template_id": 1,
  "recipient_name": "John Doe",
  "recipient_email": "john@example.com",
  "custom_data": {
    "score": "95",
    "grade": "A+"
  }
}
```

### 5. Result:
Badge displays "95" at position (600, 400) in gold color with 48px font size.

## Files Modified:
- ✅ app/src/models/custom_field.py (new)
- ✅ app/src/models/__init__.py
- ✅ app/src/models/badge.py
- ✅ app/src/routes/admin.py
- ✅ app/src/routes/public.py
- ✅ app/src/routes/badge.py
- ✅ app/src/templates/admin/index.html
- ✅ app/src/templates/index.html
- ✅ app/src/services/badge_generator.py
- ✅ migrate_custom_fields.py (new)

## Testing Checklist:
- [ ] Create a custom field in admin dashboard
- [ ] Edit and delete custom fields
- [ ] Configure custom field in template editor
- [ ] Save template and verify config persists
- [ ] Create badge with custom field values via web form
- [ ] Create badge with custom field values via API
- [ ] Verify custom field renders correctly on badge image
- [ ] Test required vs optional fields
- [ ] Test different field types (text, number, date)
- [ ] Test with multiple custom fields

## Next Steps:
The feature is complete and ready for testing. Consider:
1. Adding validation for custom field values based on field_type
2. Adding more field types (email, url, select dropdown)
3. Adding field value formatting options (e.g., date format, number format)
4. Adding field visibility conditions (show field X only if field Y has value Z)
