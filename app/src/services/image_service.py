import boto3
import json
import base64
import os
from io import BytesIO
from PIL import Image
from botocore.config import Config
import random


class ImageService:
    """Service for generating images using Amazon Bedrock Nova Canvas"""
    
    def __init__(self):
        # Support separate region for Bedrock API calls
        # This allows deploying the app in one region (e.g., eu-west-1)
        # while calling Bedrock in another region (e.g., us-east-1)
        self.bedrock_region = os.getenv('BEDROCK_REGION', os.getenv('AWS_REGION', 'us-east-1'))
        
        # boto3 automatically picks up credentials from:
        # 1. Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
        # 2. AWS CLI config (~/.aws/credentials)
        # 3. IAM role (when running on EC2/ECS/Lambda)
        # 4. Instance metadata service (IMDS)
        self.bedrock_client = boto3.client(
            service_name='bedrock-runtime',
            region_name=self.bedrock_region,
            config=Config(read_timeout=300)
        )
        self.model_id = 'amazon.nova-canvas-v1:0'
    
    def generate_badge_image(self, prompt: str, width: int = 1024, height: int = 1024) -> bytes:
        """
        Generate a badge image using Nova Canvas
        
        Args:
            prompt: Text description for the badge (include style in the prompt text)
            width: Image width (must be 1024, 1152, 1173, 1216, 1344, or 1536)
            height: Image height (must be 1024, 1152, 1173, 1216, 1344, or 1536)
            
        Returns:
            Image bytes
        """
        # Nova Canvas supported dimensions
        supported_dimensions = [1024, 1152, 1173, 1216, 1344, 1536]
        
        # Find closest supported dimension
        def find_closest(value):
            return min(supported_dimensions, key=lambda x: abs(x - value))
        
        width = find_closest(width)
        height = find_closest(height)
        seed = random.randint(0, 858993460)
        
        body = json.dumps({
            "taskType": "TEXT_IMAGE",
            "textToImageParams": {
                "text": prompt
            },
            "imageGenerationConfig": {
                "numberOfImages": 1,
                "quality": "premium",
                "height": height,
                "width": width,
                "cfgScale": 8.0,
                "seed": seed
            }
        })
        
        response = self.bedrock_client.invoke_model(
            body=body,
            modelId=self.model_id,
            accept="application/json",
            contentType="application/json"
        )
        
        response_body = json.loads(response.get("body").read())
        
        # Extract base64 image
        base64_image = response_body.get("images")[0]
        image_bytes = base64.b64decode(base64_image)
        
        return image_bytes
    
    def edit_badge_image(self, base_image_path: str, prompt: str, mask_prompt: str = None) -> bytes:
        """
        Edit an existing badge image using Nova Canvas
        
        Args:
            base_image_path: Path to the base image
            prompt: Text description for the edit
            mask_prompt: Optional mask prompt for selective editing
            
        Returns:
            Edited image bytes
        """
        # Load and encode base image
        with open(base_image_path, 'rb') as f:
            base_image_bytes = f.read()
        base_image_base64 = base64.b64encode(base_image_bytes).decode('utf-8')
        
        body = {
            "taskType": "INPAINTING",
            "inPaintingParams": {
                "text": prompt,
                "image": base_image_base64
            },
            "imageGenerationConfig": {
                "numberOfImages": 1,
                "quality": "premium",
                "cfgScale": 8.0
            }
        }
        
        if mask_prompt:
            body["inPaintingParams"]["maskPrompt"] = mask_prompt
        
        response = self.bedrock_client.invoke_model(
            body=json.dumps(body),
            modelId=self.model_id,
            accept="application/json",
            contentType="application/json"
        )
        
        response_body = json.loads(response.get("body").read())
        base64_image = response_body.get("images")[0]
        image_bytes = base64.b64decode(base64_image)
        
        return image_bytes
    
    def composite_badge(self, background_path: str, elements: list) -> Image:
        """
        Composite a badge from background and elements
        
        Args:
            background_path: Path to background image
            elements: List of dicts with 'path', 'x', 'y', 'width', 'height'
            
        Returns:
            PIL Image object
        """
        background = Image.open(background_path).convert('RGBA')
        
        for element in elements:
            overlay = Image.open(element['path']).convert('RGBA')
            overlay = overlay.resize((element['width'], element['height']))
            background.paste(overlay, (element['x'], element['y']), overlay)
        
        return background
