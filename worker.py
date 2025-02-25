import redis
from rq import Worker, Queue, Connection
from config import Config
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Connect to Redis
redis_conn = redis.Redis(
    host=Config.REDIS_HOST,
    port=Config.REDIS_PORT,
    password=Config.REDIS_PASSWORD,
    db=Config.REDIS_DB
)

# Define the function that will be executed by the worker
def process_image(image_id):
    """
    Process a single image by downloading it, compressing it, and uploading the result.
    
    Parameters:
    image_id (str): The ID of the image to process
    """
    from services.image_processor import process_image as celery_process_image
    # We're just calling the Celery task directly, without the .delay()
    celery_process_image(image_id)

if __name__ == '__main__':
    # Start the worker
    with Connection(redis_conn):
        worker = Worker(Queue('default'))
        worker.work()