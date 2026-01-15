# Font Rendering Fix for Containers

## Problem
Badge text appeared tiny in containers (both local Finch and ECS) but looked correct on macOS. This was caused by hardcoded macOS font paths that don't exist in Linux containers.

## Root Cause
The badge generator was using hardcoded macOS system font paths:
- `/System/Library/Fonts/Supplemental/Arial.ttf`
- `/System/Library/Fonts/Apple Color Emoji.ttc`

When PIL/Pillow can't find the specified font file, it silently falls back to a tiny default bitmap font, resulting in barely readable text.

## Solution

### 1. Install Fonts in Container
Updated `Dockerfile` to install proper TrueType fonts:
```dockerfile
RUN apt-get update && apt-get install -y \
    fonts-dejavu-core \
    fonts-liberation \
    fonts-noto-color-emoji \
    && rm -rf /var/lib/apt/lists/*
```

**Fonts installed:**
- **Liberation fonts**: Drop-in replacements for Arial, Times New Roman, Courier (metric-compatible with Microsoft fonts)
- **DejaVu fonts**: High-quality fonts with extensive Unicode coverage
- **Noto Color Emoji**: Google's emoji font for Linux

### 2. Cross-Platform Font Detection
Added `_get_font_path()` method to `badge_generator.py` that:
- Detects the operating system (macOS vs Linux)
- Returns appropriate font paths for each platform
- Includes fallback logic if fonts are missing
- Handles emoji fonts separately

**Font mapping:**
| Font Family | macOS | Linux (Container) |
|-------------|-------|-------------------|
| Arial/Helvetica | System fonts | Liberation Sans |
| Times New Roman/Georgia | System fonts | Liberation Serif |
| Courier New | System fonts | Liberation Mono |
| Verdana/Trebuchet | System fonts | DejaVu Sans |
| Emoji | Apple Color Emoji | Noto Color Emoji |

### 3. Graceful Fallbacks
If a requested font isn't found:
1. Try the mapped font for the platform
2. Fall back to DejaVu Sans (always available)
3. Fall back to Liberation Sans (always available)
4. If all else fails, PIL will use its default font

## Testing

### Test Locally on Mac
```bash
uv run python test_fonts.py
```
Should show ✓ for macOS system fonts.

### Test in Container
```bash
finch build --platform linux/amd64 -t digital-badge-app:latest .
finch run --rm digital-badge-app:latest uv run python test_fonts.py
```
Should show ✓ for Liberation and Noto fonts.

### Test Badge Generation
1. Run the app locally or in container
2. Create a badge with text
3. Verify text is properly sized and readable

## Deployment

After making these changes, rebuild and redeploy:

```bash
./deploy-to-ecs-express.sh
```

The deployment script will:
1. Build new image with fonts installed
2. Push to ECR
3. Update ECS service
4. ECS will pull new image and restart tasks

## Why This Matters

**Before fix:**
- Text size: ~8-10px (bitmap font)
- Barely readable
- No emoji support

**After fix:**
- Text size: As specified (36px, 48px, etc.)
- Crisp, readable text
- Full emoji support
- Consistent rendering across environments

## Related Files
- `Dockerfile` - Font package installation
- `app/src/services/badge_generator.py` - Cross-platform font detection
- `test_fonts.py` - Font availability test script
