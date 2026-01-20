# Custom Fields Quick Start Guide

## Overview

Custom fields allow you to add dynamic metadata to badges (like scores, grades, dates, etc.) that can be positioned and styled in templates.

## Quick Start

### 1. Create Custom Fields (Admin Dashboard)

1. Navigate to `/admin` and login
2. Scroll to "Custom Fields (Data Ingestion)" section
3. Click "Create New Field"
4. Fill in the form:
   - **Name**: Display name (e.g., "Score")
   - **Field Key**: Internal identifier (auto-generated, e.g., "score")
   - **Type**: text, number, or date
   - **Required**: Whether the field must be filled
   - **Default Value**: Optional default value
   - **Description**: Help text for users

### 2. Configure in Template

1. In admin dashboard, click "Edit" on a template
2. Scroll to "Custom Fields (Optional)" section
3. Check the box next to the field you want to enable
4. Configure positioning and styling:
   - **X Position**: Horizontal position in pixels
   - **Y Position**: Vertical position in pixels
   - **Font Size**: Text size in pixels
   - **Color**: Text color (hex code)
5. Save the template

### 3. Create Badges with Custom Data

#### Via Web Form:
1. Go to home page (`/`)
2. Fill in recipient name
3. Fill in custom field values (they appear automatically)
4. Click "Generate Badge"

#### Via API:
```bash
curl -X POST http://localhost:5001/api/badges \
  -H "Content-Type: application/json" \
  -d '{
    "recipient_name": "John Doe",
    "recipient_email": "john@example.com",
    "custom_data": {
      "score": "95",
      "grade": "A+"
    }
  }'
```

## Example Use Cases

### Gaming Leaderboard
- **Field**: Score (number, required)
- **Position**: Center, below name
- **Style**: Large, gold color

### Educational Certificates
- **Field**: Grade (text, required)
- **Field**: Date (date, required)
- **Position**: Bottom right corner
- **Style**: Medium, dark gray

### Event Badges
- **Field**: Event Date (date, required)
- **Field**: Role (text, optional)
- **Position**: Top right corner
- **Style**: Small, accent color

## Field Types

- **text**: Any text value (names, labels, etc.)
- **number**: Numeric values (scores, counts, etc.)
- **date**: Date values (formatted as YYYY-MM-DD)

## Tips

1. **Positioning**: Use the template preview to see where fields appear
2. **Colors**: Use contrasting colors for readability
3. **Required Fields**: Mark fields as required if they're essential
4. **Default Values**: Set defaults for optional fields
5. **Field Keys**: Keep them short and descriptive (lowercase, underscores)

## Testing

Run the test script to verify everything works:

```bash
uv run python test_custom_fields_complete.py
```

This will:
1. Create sample custom fields
2. Configure a template
3. Generate a badge with custom data
4. Verify the badge image was created

## Troubleshooting

### Custom fields don't appear in web form
- Make sure custom fields are created in admin dashboard
- Check that the server restarted after creating fields

### Custom fields don't render on badge
- Verify the field is enabled in the template configuration
- Check that the field has a value when creating the badge
- Ensure positioning values are within badge dimensions

### Database errors
- Run the migration script: `uv run python migrate_custom_fields.py`
- This adds the required database tables and columns
