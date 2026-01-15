#!/usr/bin/env python3
"""Test font availability in container"""
import os
import platform

def check_fonts():
    """Check if fonts are available"""
    system = platform.system()
    print(f"System: {system}")
    print()
    
    if system == 'Darwin':
        fonts = [
            '/System/Library/Fonts/Supplemental/Arial.ttf',
            '/System/Library/Fonts/Apple Color Emoji.ttc',
        ]
    else:
        fonts = [
            '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            '/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf',
        ]
    
    print("Checking fonts:")
    for font in fonts:
        exists = os.path.exists(font)
        status = "✓" if exists else "✗"
        print(f"  {status} {font}")
    
    print()
    
    # Try to load fonts with PIL
    try:
        from PIL import ImageFont
        print("Testing PIL font loading:")
        
        if system == 'Darwin':
            test_font = '/System/Library/Fonts/Supplemental/Arial.ttf'
        else:
            test_font = '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf'
        
        if os.path.exists(test_font):
            font = ImageFont.truetype(test_font, 36)
            print(f"  ✓ Successfully loaded {test_font} at size 36")
        else:
            print(f"  ✗ Font not found: {test_font}")
            
    except Exception as e:
        print(f"  ✗ Error loading font: {e}")

if __name__ == '__main__':
    check_fonts()
