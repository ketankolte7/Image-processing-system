from PIL import Image as PILImage
import requests
from io import BytesIO
import os
import uuid
from celery import Celery
from config import Config
from database.models import Request, Image, db
from services.webhook_service import send_completion_webhook
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Celery
celery = Celery(
    'image_processor',
    broker=f'redis://{Config.REDIS_HOST}:{Config.REDIS_PORT}/{Config.REDIS_DB}'
)

@celery.task
def process_request_images(request_id):
    """
    Process all images for a given request.
    
    Parameters:
    request_id (str): The ID of the request
    """
    from flask import current_app
    
    with current_app.app_context():
        # Get all images for this request
        images = Image.query.join(
            Image.product
        ).filter(
            Product.request_id == request_id,
            Image.status == 'pending'
        ).all()
        
        # Process each image
        for image in images:
            process_image.delay(image.id)

@celery.task
def process_image(image_id):
    """
    Process a single image by downloading it, compressing it, and uploading the result.
    
    Parameters:
    image_id (str): The ID of the image to process
    """
    from flask import current_app
    
    with current_app.app_context():
        # Get the image record
        image = Image.query.get(image_id)
        
        if not image or image.status != 'pending':
            logger.warning(f"Image {image_id} not found or not pending")
            return
        
        try:
            # Update status to processing
            image.status = 'processing'
            db.session.commit()
            
            # Download the image
            response = requests.get(image.input_url, timeout=30)
            response.raise_for_status()
            
            # Open the image with PIL
            img = PILImage.open(BytesIO(response.content))
            
            # Process the image (compress by 50% quality)
            output = BytesIO()
            img.save(output, format=img.format, quality=50)
            output.seek(0)
            
            # Generate a unique filename
            filename = f"{uuid.uuid4()}.{img.format.lower() if img.format else 'jpg'}"
            output_path = os.path.join(Config.PROCESSED_FOLDER, filename)
            
            # Ensure the directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save to disk
            with open(output_path, 'wb') as f:
                f.write(output.read())
            
            # In a real application, you would upload to S3 or similar
            # For this example, we'll just create a URL based on local path
            output_url = f"{Config.BASE_URL}/processed/{filename}"
            
            # Update the image record
            image.output_url = output_url
            image.status = 'completed'
            db.session.commit()
            
            # Check if all images for this request are processed
            check_request_completion(image.product.request_id)
            
        except Exception as e:
            logger.error(f"Error processing image {image_id}: {str(e)}")
            image.status = 'failed'
            db.session.commit()
            check_request_completion(image.product.request_id)

def check_request_completion(request_id):
    """
    Check if all images for a request have been processed.
    If yes, update the request status and trigger webhook if configured.
    
    Parameters:
    request_id (str): The ID of the request
    """
    from flask import current_app
    
    with current_app.app_context():
        # Get the request
        request = Request.query.get(request_id)
        
        if not request:
            logger.warning(f"Request {request_id} not found")
            return
        
        # Count all images and processed images
        total_count = Image.query.join(
            Image.product
        ).filter(
            Product.request_id == request_id
        ).count()
        
        processed_count = Image.query.join(
            Image.product
        ).filter(
            Product.request_id == request_id,
            Image.status.in_(['completed', 'failed'])
        ).count()
        
        # Update the request with current counts
        request.total_images = total_count
        request.processed_images = processed_count
        
        # Check if all images are processed
        if processed_count == total_count:
            request.status = 'completed'
            db.session.commit()
            
            # If webhook is configured, trigger it
            if request.webhook_url and request.webhook_status == 'not_sent':
                send_completion_webhook.delay(request_id)
        else:
            db.session.commit()