import redis
import json
from config import Config
from rq import Queue
from worker import process_image

# Connect to Redis
redis_conn = redis.Redis(
    host=Config.REDIS_HOST,
    port=Config.REDIS_PORT,
    password=Config.REDIS_PASSWORD,
    db=Config.REDIS_DB
)

# Create a queue
queue = Queue(connection=redis_conn)

def enqueue_processing_task(request_id, filepath):
    """
    Enqueues a task to process the CSV file and its images.
    
    Parameters:
    request_id (str): The unique ID of the request
    filepath (str): Path to the CSV file
    """
    from services.validation import process_csv_to_db
    from services.image_processor import process_request_images
    from services.webhook_service import send_completion_webhook
    from database.models import Request, db
    from flask import current_app
    
    with current_app.app_context():
        # First, process the CSV into the database
        process_csv_to_db(request_id, filepath)
        
        # Update the request status
        request = Request.query.get(request_id)
        request.status = 'processing'
        db.session.commit()
        
        # Now, enqueue the image processing tasks
        process_request_images.delay(request_id)

def enqueue_image_task(image_id):
    """
    Enqueues a task to process a single image.
    
    Parameters:
    image_id (str): The ID of the image to process
    """
    # Add the job to the queue
    job = queue.enqueue(
        process_image,
        image_id,
        job_timeout=Config.JOB_TIMEOUT
    )
    
    return job.id