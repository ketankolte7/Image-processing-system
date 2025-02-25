from flask import Flask, request, jsonify
import uuid
import os
from werkzeug.utils import secure_filename
from services.validation import validate_csv
from services.queue_manager import enqueue_processing_task
from database.models import Request, db
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# Ensure upload directory exists
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

@app.route('/api/upload', methods=['POST'])
def upload_csv():
    """
    Upload API endpoint that accepts CSV files and initiates processing.
    Returns a unique request ID that can be used to check processing status.
    """
    # Check if the post request has the file part
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    # If user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and file.filename.endswith('.csv'):
        # Generate a unique request ID
        request_id = str(uuid.uuid4())
        
        # Secure the filename and save the file
        filename = secure_filename(file.filename)
        filepath = os.path.join(Config.UPLOAD_FOLDER, f"{request_id}_{filename}")
        file.save(filepath)
        
        # Validate the CSV
        validation_result = validate_csv(filepath)
        
        if not validation_result['valid']:
            # Remove the invalid file
            os.remove(filepath)
            return jsonify({
                'error': 'Invalid CSV format',
                'details': validation_result['errors']
            }), 400
        
        # Create a new request in the database
        new_request = Request(
            id=request_id,
            status='pending',
            total_images=validation_result['total_images'],
            processed_images=0
        )
        
        # Optional webhook URL
        webhook_url = request.form.get('webhook_url')
        if webhook_url:
            new_request.webhook_url = webhook_url
            new_request.webhook_status = 'not_sent'
        
        # Save to database
        with app.app_context():
            db.session.add(new_request)
            db.session.commit()
        
        # Enqueue the processing task
        enqueue_processing_task(request_id, filepath)
        
        return jsonify({
            'request_id': request_id,
            'status': 'pending',
            'message': 'File uploaded successfully and processing has been initiated'
        }), 202
    
    return jsonify({'error': 'File must be a CSV'}), 400

@app.route('/api/status/<request_id>', methods=['GET'])
def check_status(request_id):
    """
    Status API endpoint that allows users to check the status of their processing request.
    """
    with app.app_context():
        req = Request.query.get(request_id)
        
        if not req:
            return jsonify({'error': 'Request ID not found'}), 404
        
        # Calculate percentage completion
        completion_percentage = 0
        if req.total_images > 0:
            completion_percentage = (req.processed_images / req.total_images) * 100
        
        return jsonify({
            'request_id': req.id,
            'status': req.status,
            'completion_percentage': completion_percentage,
            'created_at': req.created_at.isoformat(),
            'updated_at': req.updated_at.isoformat(),
            'total_images': req.total_images,
            'processed_images': req.processed_images,
            'webhook_status': req.webhook_status if req.webhook_url else None
        }), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=Config.DEBUG, host=Config.HOST, port=Config.PORT)