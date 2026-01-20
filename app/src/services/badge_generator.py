import os
import qrcode
from PIL import Image, ImageDraw, ImageFont
from app.src.models import Badge, Template
from app.src.extensions import db
from app.src.services.image_service import ImageService
from app.src.utils import get_base_url


class BadgeGenerator:
    """Service for generating virtual badges"""
    
    def __init__(self, app_config):
        self.badge_folder = app_config['BADGE_FOLDER']
        # Don't store base_url, use get_base_url() dynamically
        self.image_service = ImageService()
    
    def _is_emoji(self, char):
        """Check if a character is an emoji"""
        code = ord(char)
        # Common emoji ranges
        return (
            0x1F300 <= code <= 0x1F9FF or  # Misc Symbols and Pictographs, Emoticons, etc.
            0x2600 <= code <= 0x26FF or    # Misc symbols
            0x2700 <= code <= 0x27BF or    # Dingbats
            0xFE00 <= code <= 0xFE0F or    # Variation Selectors
            0x1F000 <= code <= 0x1F02F or  # Mahjong Tiles
            0x1F0A0 <= code <= 0x1F0FF or  # Playing Cards
            0x1F100 <= code <= 0x1F64F or  # Enclosed characters
            0x1F680 <= code <= 0x1F6FF or  # Transport and Map
            0x1F900 <= code <= 0x1F9FF     # Supplemental Symbols and Pictographs
        )
    
    def _draw_text_with_emoji(self, draw, text, position, font, emoji_font, color):
        """Draw text with emoji support by using different fonts for emoji characters"""
        x, y = position
        current_x = x
        
        for char in text:
            if self._is_emoji(char):
                # Use emoji font for emoji characters
                try:
                    draw.text((current_x, y), char, fill=color, font=emoji_font, embedded_color=True)
                    bbox = draw.textbbox((0, 0), char, font=emoji_font)
                except:
                    # Fallback to regular font if emoji font fails
                    draw.text((current_x, y), char, fill=color, font=font)
                    bbox = draw.textbbox((0, 0), char, font=font)
            else:
                # Use regular font for normal characters
                draw.text((current_x, y), char, fill=color, font=font)
                bbox = draw.textbbox((0, 0), char, font=font)
            
            # Move x position for next character
            char_width = bbox[2] - bbox[0]
            current_x += char_width
    
    def create_badge(self, template_id: int = None, recipient_name: str = None, 
                     recipient_email: str = None, badge_data: dict = None, custom_data: dict = None):
        """
        Create a new virtual badge
        
        Args:
            template_id: Template to use (uses default if None)
            recipient_name: Name of recipient
            recipient_email: Email of recipient
            badge_data: Additional badge data
            custom_data: Custom field values (e.g., {'score': '95', 'grade': 'A+'})
            
        Returns:
            Badge object
        """
        # Get template
        if template_id:
            template = Template.query.get(template_id)
        else:
            template = Template.query.filter_by(is_default=True).first()
        
        if not template:
            raise ValueError("No template found")
        
        # Create badge record
        badge = Badge(
            template_id=template.id,
            recipient_name=recipient_name,
            recipient_email=recipient_email
        )
        
        # Set custom data if provided
        if custom_data:
            badge.set_custom_data(custom_data)
        
        db.session.add(badge)
        db.session.flush()  # Get the UUID
        
        # Generate badge image
        badge_image_path = self._generate_badge_image(badge, template, badge_data)
        badge.image_path = badge_image_path
        
        # Generate QR code
        qr_code_path = self._generate_qr_code(badge)
        badge.qr_code_path = qr_code_path
        
        db.session.commit()
        
        return badge
    
    def _generate_badge_image(self, badge: Badge, template: Template, badge_data: dict = None):
        """Generate the badge image based on template"""
        layout_config = template.get_layout_config()
        return self._generate_badge_image_with_config(badge, layout_config, badge_data)
    
    def _get_font_path(self, font_family='Arial'):
        """Get font path that works on both macOS and Linux"""
        import platform
        system = platform.system()
        
        if system == 'Darwin':  # macOS
            font_map = {
                'Arial': '/System/Library/Fonts/Supplemental/Arial.ttf',
                'Helvetica': '/System/Library/Fonts/Helvetica.ttc',
                'Times New Roman': '/System/Library/Fonts/Supplemental/Times New Roman.ttf',
                'Georgia': '/System/Library/Fonts/Supplemental/Georgia.ttf',
                'Courier New': '/System/Library/Fonts/Supplemental/Courier New.ttf',
                'Verdana': '/System/Library/Fonts/Supplemental/Verdana.ttf',
                'Trebuchet MS': '/System/Library/Fonts/Supplemental/Trebuchet MS.ttf',
                'Impact': '/System/Library/Fonts/Supplemental/Impact.ttf',
                'Comic Sans MS': '/System/Library/Fonts/Supplemental/Comic Sans MS.ttf',
                'Palatino': '/System/Library/Fonts/Palatino.ttc'
            }
            emoji_font = '/System/Library/Fonts/Apple Color Emoji.ttc'
        else:  # Linux (container)
            font_map = {
                'Arial': '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
                'Helvetica': '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
                'Times New Roman': '/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf',
                'Georgia': '/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf',
                'Courier New': '/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf',
                'Verdana': '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                'Trebuchet MS': '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                'Impact': '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
                'Comic Sans MS': '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                'Palatino': '/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf'
            }
            emoji_font = '/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf'
        
        font_path = font_map.get(font_family, font_map.get('Arial'))
        
        # Verify font exists, fallback if needed
        if not os.path.exists(font_path):
            # Try to find any available font
            fallback_paths = [
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
            ]
            for fallback in fallback_paths:
                if os.path.exists(fallback):
                    font_path = fallback
                    break
        
        # Verify emoji font exists
        if not os.path.exists(emoji_font):
            emoji_font = None
        
        return font_path, emoji_font
    
    def _generate_badge_image_with_config(self, badge: Badge, layout_config: dict, badge_data: dict = None):
        """Generate badge image using provided config (for previews)"""
        # Create badge image
        width = layout_config.get('width', 800)
        height = layout_config.get('height', 600)
        font_family = layout_config.get('font_family', 'Arial')
        
        # Get cross-platform font paths
        font_path, emoji_font_path = self._get_font_path(font_family)
        
        # Create base image
        img = Image.new('RGB', (width, height), color=layout_config.get('background_color', '#FFFFFF'))
        
        # Add background image if specified
        if layout_config.get('background_image'):
            try:
                bg_path = os.path.join(os.path.dirname(self.badge_folder), layout_config['background_image'].lstrip('/static/'))
                if os.path.exists(bg_path):
                    bg_img = Image.open(bg_path).convert('RGB')
                    bg_img = bg_img.resize((width, height))
                    
                    # Apply opacity if specified
                    bg_opacity = layout_config.get('bg_opacity', 100)
                    if bg_opacity < 100:
                        # Convert to RGBA to support transparency
                        bg_img = bg_img.convert('RGBA')
                        # Adjust alpha channel
                        alpha = int(255 * (bg_opacity / 100))
                        bg_img.putalpha(alpha)
                        
                        # Blend with base color
                        base = Image.new('RGBA', (width, height), layout_config.get('background_color', '#FFFFFF'))
                        img = Image.alpha_composite(base, bg_img).convert('RGB')
                    else:
                        img = bg_img
            except Exception as e:
                print(f"Error loading background image: {e}")
        
        # Convert to RGBA for overlay support
        img = img.convert('RGBA')
        
        # Add overlay images
        if layout_config.get('overlay_images'):
            for overlay in layout_config['overlay_images']:
                try:
                    overlay_path = os.path.join(os.path.dirname(self.badge_folder), overlay['path'].lstrip('/static/'))
                    if os.path.exists(overlay_path):
                        overlay_img = Image.open(overlay_path).convert('RGBA')
                        overlay_img = overlay_img.resize((overlay['width'], overlay['height']))
                        img.paste(overlay_img, (overlay['x'], overlay['y']), overlay_img)
                except Exception as e:
                    print(f"Error loading overlay image: {e}")
        
        # Add text
        draw = ImageDraw.Draw(img)
        
        # Load emoji font
        emoji_font_title = None
        emoji_font_name = None
        emoji_font_subtitle = None
        emoji_font_message = None
        
        if emoji_font_path:
            try:
                emoji_font_title = ImageFont.truetype(emoji_font_path, layout_config.get('title_size', 36))
                emoji_font_name = ImageFont.truetype(emoji_font_path, 48)
                emoji_font_subtitle = ImageFont.truetype(emoji_font_path, layout_config.get('subtitle_size', 24))
                emoji_font_message = ImageFont.truetype(emoji_font_path, layout_config.get('message_size', 16))
            except Exception as e:
                print(f"Could not load emoji font: {e}")
                emoji_font_title = emoji_font_name = emoji_font_subtitle = emoji_font_message = None
        
        # Add title if specified
        if layout_config.get('title_text'):
            try:
                title_size = layout_config.get('title_size', 36)
                font = ImageFont.truetype(font_path, title_size)
            except:
                font = ImageFont.load_default()
            
            title_x = layout_config.get('title_x', width // 2)
            title_y = layout_config.get('title_y', 100)
            title_color = layout_config.get('title_color', '#000000')
            
            # Center text
            bbox = draw.textbbox((0, 0), layout_config['title_text'], font=font)
            text_width = bbox[2] - bbox[0]
            
            if emoji_font_title:
                self._draw_text_with_emoji(draw, layout_config['title_text'], 
                                          (title_x - text_width // 2, title_y), 
                                          font, emoji_font_title, title_color)
            else:
                draw.text((title_x - text_width // 2, title_y), layout_config['title_text'], 
                         fill=title_color, font=font)
        
        # Add recipient name
        if badge.recipient_name:
            try:
                font = ImageFont.truetype(font_path, 48)
            except:
                font = ImageFont.load_default()
            
            text_x = layout_config.get('name_x', width // 2)
            text_y = layout_config.get('name_y', height // 2)
            
            # Center text
            bbox = draw.textbbox((0, 0), badge.recipient_name, font=font)
            text_width = bbox[2] - bbox[0]
            
            if emoji_font_name:
                self._draw_text_with_emoji(draw, badge.recipient_name,
                                          (text_x - text_width // 2, text_y),
                                          font, emoji_font_name, layout_config.get('text_color', '#000000'))
            else:
                draw.text((text_x - text_width // 2, text_y), badge.recipient_name, 
                         fill=layout_config.get('text_color', '#000000'), font=font)
        
        # Add subtitle if specified
        if layout_config.get('subtitle_text'):
            try:
                subtitle_size = layout_config.get('subtitle_size', 24)
                font = ImageFont.truetype(font_path, subtitle_size)
            except:
                font = ImageFont.load_default()
            
            subtitle_x = layout_config.get('subtitle_x', width // 2)
            subtitle_y = layout_config.get('subtitle_y', 500)
            subtitle_color = layout_config.get('subtitle_color', '#666666')
            
            # Center text
            bbox = draw.textbbox((0, 0), layout_config['subtitle_text'], font=font)
            text_width = bbox[2] - bbox[0]
            
            if emoji_font_subtitle:
                self._draw_text_with_emoji(draw, layout_config['subtitle_text'],
                                          (subtitle_x - text_width // 2, subtitle_y),
                                          font, emoji_font_subtitle, subtitle_color)
            else:
                draw.text((subtitle_x - text_width // 2, subtitle_y), layout_config['subtitle_text'], 
                         fill=subtitle_color, font=font)
        
        # Add message if specified
        if layout_config.get('message_text'):
            try:
                message_size = layout_config.get('message_size', 16)
                font = ImageFont.truetype(font_path, message_size)
            except:
                font = ImageFont.load_default()
            
            message_x = layout_config.get('message_x', width // 2)
            message_y = layout_config.get('message_y', 550)
            message_color = layout_config.get('message_color', '#666666')
            message_width = layout_config.get('message_width', 600)
            
            # Word wrap for message
            words = layout_config['message_text'].split(' ')
            lines = []
            current_line = ''
            
            for word in words:
                test_line = current_line + (' ' if current_line else '') + word
                bbox = draw.textbbox((0, 0), test_line, font=font)
                test_width = bbox[2] - bbox[0]
                
                if test_width > message_width and current_line:
                    lines.append(current_line)
                    current_line = word
                else:
                    current_line = test_line
            
            if current_line:
                lines.append(current_line)
            
            # Draw each line centered
            line_height = int(message_size * 1.2)
            for i, line in enumerate(lines):
                bbox = draw.textbbox((0, 0), line, font=font)
                line_width = bbox[2] - bbox[0]
                draw.text((message_x - line_width // 2, message_y + (i * line_height)), 
                         line, fill=message_color, font=font)
        
        # Add custom fields if specified
        custom_fields_config = layout_config.get('custom_fields', {})
        if custom_fields_config and badge.custom_data:
            custom_data = badge.get_custom_data()
            
            for field_key, field_config in custom_fields_config.items():
                if not field_config.get('enabled', False):
                    continue
                
                # Get the value for this field
                field_value = custom_data.get(field_key)
                if not field_value:
                    continue
                
                # Get field configuration
                field_x = field_config.get('x', width // 2)
                field_y = field_config.get('y', 350)
                field_size = field_config.get('size', 32)
                field_color = field_config.get('color', '#000000')
                
                # Load font for this field
                try:
                    field_font = ImageFont.truetype(font_path, field_size)
                except:
                    field_font = ImageFont.load_default()
                
                # Draw the custom field value (centered)
                bbox = draw.textbbox((0, 0), str(field_value), font=field_font)
                text_width = bbox[2] - bbox[0]
                draw.text((field_x - text_width // 2, field_y), str(field_value), 
                         fill=field_color, font=field_font)
        
        # Add frame if specified
        if layout_config.get('frame'):
            try:
                frame_path = os.path.join(os.path.dirname(self.badge_folder), layout_config['frame'].lstrip('/static/'))
                if os.path.exists(frame_path):
                    frame_img = Image.open(frame_path).convert('RGBA')
                    frame_img = frame_img.resize((width, height))
                    img.paste(frame_img, (0, 0), frame_img)
            except Exception as e:
                print(f"Error loading frame: {e}")
        
        # Convert back to RGB for saving
        if img.mode == 'RGBA':
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            img = background
        
        # Save image
        filename = f"badge_{badge.uuid}.png"
        filepath = os.path.join(self.badge_folder, filename)
        img.save(filepath)
        
        return f"/static/badges/{filename}"
    
    def _generate_qr_code(self, badge: Badge):
        """Generate QR code for badge URL"""
        # Get base URL dynamically
        base_url = get_base_url()
        badge_url = badge.get_public_url(base_url)
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(badge_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        filename = f"qr_{badge.uuid}.png"
        filepath = os.path.join(self.badge_folder, filename)
        img.save(filepath)
        
        return f"/static/badges/{filename}"
    
    def generate_with_ai(self, prompt: str, template_id: int = None, 
                        recipient_name: str = None, recipient_email: str = None):
        """
        Generate a badge using AI image generation
        
        Args:
            prompt: Text prompt for badge design
            template_id: Template to use
            recipient_name: Name of recipient
            recipient_email: Email of recipient
            
        Returns:
            Badge object
        """
        # Generate image using Nova Canvas
        image_bytes = self.image_service.generate_badge_image(prompt)
        
        # Create badge record
        if template_id:
            template = Template.query.get(template_id)
        else:
            template = Template.query.filter_by(is_default=True).first()
        
        if not template:
            raise ValueError("No template found")
        
        badge = Badge(
            template_id=template.id,
            recipient_name=recipient_name,
            recipient_email=recipient_email
        )
        db.session.add(badge)
        db.session.flush()
        
        # Save generated image
        filename = f"badge_{badge.uuid}.png"
        filepath = os.path.join(self.badge_folder, filename)
        
        with open(filepath, 'wb') as f:
            f.write(image_bytes)
        
        badge.image_path = f"/static/badges/{filename}"
        
        # Generate QR code
        qr_code_path = self._generate_qr_code(badge)
        badge.qr_code_path = qr_code_path
        
        db.session.commit()
        
        return badge
