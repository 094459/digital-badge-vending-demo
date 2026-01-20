# Custom Fields Feature - Verification Steps

## Issue Fixed
The custom field management buttons (Create New, Edit, Delete) were not working because the JavaScript functions were defined outside the `<script>` tags. This has been corrected.

## Verification Steps

### 1. Access Admin Dashboard
1. Navigate to `http://127.0.0.1:5001/admin`
2. Login with your credentials
3. Scroll down to "Custom Fields (Data Ingestion)" section

### 2. Test Create Custom Field
1. Click "Create New Field" button
2. Modal should appear with form
3. Fill in:
   - Name: "Score"
   - Field Key: (auto-generated as "score")
   - Type: Number
   - Required: Check the box
   - Description: "Test score or game score"
4. Click "Save Field"
5. Page should reload and show the new field in the table

### 3. Test Edit Custom Field
1. Click "Edit" button on the Score field
2. Modal should appear with existing values
3. Change description to "Updated description"
4. Click "Save Field"
5. Page should reload with updated values

### 4. Test Configure in Template
1. Click "Edit" on any template
2. Scroll to "Custom Fields (Optional)" section
3. Check the box next to "Score"
4. Settings should appear below
5. Set:
   - X Position: 400
   - Y Position: 350
   - Font Size: 48
   - Color: #FFD700 (gold)
6. **Preview should show `[Score]` at the configured position**
7. Adjust position/size/color and watch preview update in real-time
8. Save template

### 5. Test Badge Creation
1. Go to home page (`http://127.0.0.1:5001/`)
2. Form should show "Score" field
3. Fill in:
   - Recipient Name: "Test User"
   - Score: 95
4. Click "Generate Badge"
5. Badge should be created with score displayed

### 6. Test API
```bash
curl -X POST http://127.0.0.1:5001/api/badges \
  -H "Content-Type: application/json" \
  -d '{
    "recipient_name": "API Test",
    "custom_data": {
      "score": "100"
    }
  }'
```

### 7. Test Delete Custom Field
1. In admin dashboard, click "Delete" on a field
2. Confirm the deletion
3. Page should reload without the field

## Browser Console Debugging

If buttons still don't work, open browser console (F12) and check for:
- "Custom field management functions loaded" message
- Any JavaScript errors
- When clicking buttons, you should see:
  - "showCreateCustomField called"
  - "editCustomField called with id: X"
  - "deleteCustomField called with id: X"

## Common Issues

### Buttons do nothing
- Hard refresh the page (Ctrl+Shift+R or Cmd+Shift+R)
- Clear browser cache
- Check browser console for JavaScript errors

### Modal doesn't appear
- Verify modal HTML exists in page source
- Check if modal has `display: none` style
- Verify JavaScript functions are defined (check console)

### Fields don't save
- Check network tab for API errors
- Verify authentication (must be logged in)
- Check server logs for errors

## Files Modified
- `app/src/templates/admin/index.html` - Fixed JavaScript function placement
- Added console.log statements for debugging
