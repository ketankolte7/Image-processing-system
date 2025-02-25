import requests
import json
import hmac
import hashlib
from celery import Celery
from config import Config
from database.models import Request, Product, Image, db
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Celery
celery = Celery(
    'webhook_service',
    broker=f'redis://{Config.REDIS_HOST}:{Config.REDIS_PORT}/{Config.REDIS_DB}'
)

@celery.task(bind=True, max_retries=3)
def send_completion_webhook(self, request_id):
    """
    Sends a webhook notification when all images for a request have been processed.
    
    Parameters:
    request_id (str): The ID of the request
    """
    from flask import current_app
    
    with current_app.app_context():
        # Get the request
        request = Request.query.get(request_id)
        
        if not request or not request.webhook_url:
            logger.warning(f"Request {request_id} not found or has no webhook URL")
            return
        
        try:
            # Generate the CSV with results
            csv_url = generate_results_csv(request_id)
            
            # Prepare webhook payload
            payload = {
                'request_id': request_id,
                'status': request.status,
                'total_images': request.total_images,
                'processed_images': request.processed_images,
                'completion_time': request.updated_at.isoformat(),
                'results_csv_url': csv_url
            }
            
            # Sign the payload if a secret is configured
            signature = None
            if Config.WEBHOOK_SECRET:
                signature = hmac.new(
                    Config.WEBHOOK_SECRET.encode(),
                    json.dumps(payload).encode(),
                    hashlib.sha256
                ).hexdigest()
            
            # Prepare headers
            headers = {
                'Content-Type': 'application/json'
            }
            
            if signature:
                headers['X-Webhook-Signature'] = signature
            
            # Send the webhook
            response = requests.post(
                request.webhook_url,
                headers=headers,
                json=payload,
                timeout=10
            )
            
            response.raise_for_status()
            
            # Update webhook status
            request.webhook_status = 'sent'
            db.session.commit()
            
        except requests.RequestException as e:
            logger.error(f"Error sending webhook for request {request_id}: {str(e)}")
            request.webhook_status = 'failed'
            db.session.commit()
            
            # Retry with exponential backoff
            retry_count = self.request.retries
            backoff = 60 * (2 ** retry_count)  # 1 min, 2 min, 4 min
            
            raise self.retry(exc=e, countdown=backoff)

def generate_results_csv(request_id):
    """
    Generates a CSV file with the processing results.
    
    Parameters:
    request_id (str): The ID of the request
    
    Returns:
    str: URL to the generated CSV file
    """
    import pandas as pd
    import os
    
    # Get all products and images for this request
    products = Product.query.filter_by(request_id=request_id).order_by(Product.serial_number).all()
    
    # Prepare data for CSV
    data = []
    for product in products:
        # Get all images for this product
        images = Image.query.filter_by(product_id=product.id).all()
        
        # Combine input and output URLs
        input_urls = ','.join([img.input_url for img in images])
        output_urls = ','.join([img.output_url if img.output_url else '' for img in images])
        
        data.append({
            'S. No.': product.serial_number,
            'Product Name': product.product_name,
            'Input Image Urls': input_urls,
            'Output Image Urls': output_urls
        })
    
    # Create DataFrame and save as CSV
    df = pd.DataFrame(data)
    
    # Ensure directory exists
    os.makedirs(Config.RESULTS_FOLDER, exist_ok=True)
    
    # Generate filename and path
    filename = f"{request_id}_results.csv"
    filepath = os.path.join(Config.RESULTS_FOLDER, filename)
    
    # Save to CSV
    df.to_csv(filepath, index=False)
    
    # Return URL to the CSV
    return f"{Config.BASE_URL}/results/{filename}"