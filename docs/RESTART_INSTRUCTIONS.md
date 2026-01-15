# How to Apply the BASE_URL Fix

## The Fix

I've updated the code to properly import and use the `get_base_url()` function. All tests pass successfully!

## What Was Fixed

1. ✅ Added `from app.src.utils import get_base_url` to `badge_generator.py`
2. ✅ Updated `get_base_url()` to use `has_request_context()` for better error handling
3. ✅ Removed `self.base_url` from `BadgeGenerator.__init__()` 
4. ✅ All imports are correct and verified

## How to Apply the Fix

### If Running Development Server

**Stop and restart your Flask development server:**

```bash
# Stop the current server (Ctrl+C in the terminal where it's running)

# Then restart it
uv run python run.py
```

### If Running with Finch/Docker

**Rebuild and restart the container:**

```bash
# Stop and remove old container
finch stop digital-badge-app
finch rm digital-badge-app

# Rebuild the image
finch build -t digital-badge-app .

# Run the new container
finch run -d --name digital-badge-app -p 8080:8080 \
    -e SECRET_KEY=test \
    -e AWS_REGION=us-east-1 \
    -e BASE_URL=http://localhost:8080 \
    digital-badge-app
```

Or use the test script:
```bash
./test-local-finch.sh
```

## Verify the Fix

After restarting, test badge generation:

```bash
# Test the API
curl -X POST http://localhost:5001/api/badges \
  -H "Content-Type: application/json" \
  -d '{"recipient_name": "Test User", "recipient_email": "test@example.com"}'
```

You should get a successful response with a badge UUID and QR code URL.

## Run the Test Suite

Verify everything works:

```bash
uv run python test_base_url.py
```

All tests should pass:
- ✓ Without BASE_URL environment variable
- ✓ With BASE_URL environment variable  
- ✓ Within Flask request context
- ✓ Badge generation imports correctly

## What Changed

### Before (Broken)
```python
# badge_generator.py
class BadgeGenerator:
    def __init__(self, app_config):
        self.base_url = os.getenv('BASE_URL', 'http://127.0.0.1:5001')
    
    def _generate_qr_code(self, badge):
        badge_url = badge.get_public_url(self.base_url)  # Used self.base_url
```

### After (Fixed)
```python
# badge_generator.py
from app.src.utils import get_base_url  # Added import

class BadgeGenerator:
    def __init__(self, app_config):
        # Removed self.base_url
        pass
    
    def _generate_qr_code(self, badge):
        base_url = get_base_url()  # Uses dynamic function
        badge_url = badge.get_public_url(base_url)
```

## Benefits

Now your application:
- ✅ Works without BASE_URL set
- ✅ Automatically detects URL from request headers
- ✅ Handles ECS Express Mode's dynamic URLs
- ✅ Falls back gracefully to localhost
- ✅ Supports custom domains when BASE_URL is set

## Troubleshooting

### Still Getting the Error?

1. **Make sure you restarted the server**
   - The Python process needs to reload the code
   - Simply saving the file isn't enough

2. **Check for syntax errors**
   ```bash
   uv run python -m py_compile app/src/utils.py
   uv run python -m py_compile app/src/services/badge_generator.py
   ```

3. **Verify imports**
   ```bash
   uv run python -c "from app.src.utils import get_base_url; print('OK')"
   uv run python -c "from app.src.services.badge_generator import BadgeGenerator; print('OK')"
   ```

4. **Check for cached bytecode**
   ```bash
   find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
   ```

### Error: "has_request_context is not defined"

This shouldn't happen, but if it does:
```bash
# Verify Flask is installed
uv run python -c "from flask import has_request_context; print('OK')"
```

## Ready to Deploy?

Once badge generation works locally, you're ready to deploy to ECS:

```bash
./deploy-to-ecs-express.sh
```

The deployment script will handle BASE_URL configuration automatically!
