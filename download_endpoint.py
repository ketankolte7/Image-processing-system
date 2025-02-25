from flask import send_file, jsonify
import os
from config import Config

def add_download_endpoint(app):
    """
    Adds the download endpoint to the Flask app.
    
    Parameters:
    app (Flask): The Flask application
    """
    
    @app.route('/api/download/<request_id>', methods=['GET'])
    def download_results(request_id):
        """
        Download API endpoint that allows users to get the resulting CSV
        with both input and output image URLs.
        """
        from database.models import Request
        
        # Check if the request exists and is completed
        request = Request.query.get(request_id)
        
        if not request:
            return jsonify({'error': 'Request ID not found'}), 404
        
        if request.status != 'completed':
            return jsonify({
                'error': 'Processing not complete',
                'status': request.status,
                'completion_percentage': (request.processed_images / request.total_images * 100) if request.total_images > 0 else 0
            }), 400
        
        # Check if the results file exists
        filename = f"{request_id}_results.csv"
        filepath = os.path.join(Config.RESULTS_FOLDER, filename)
        
        if not os.path.exists(filepath):
            # Generate the file if it doesn't exist
            from services.webhook_service import generate_results_csv
            generate_results_csv(request_id)
            
            # Check again if file exists
            if not os.path.exists(filepath):
                return jsonify({'error': 'Results file not found'}), 404
        
        # Send the file
        return send_file(
            filepath, 
            mimetype='text/csv',
            as_attachment=True,
            download_name=f"results_{request_id}.csv"
        )
    
    # Add static routes for processed images and results
    @app.route('/processed/<filename>')
    def processed_file(filename):
        return send_file(os.path.join(Config.PROCESSED_FOLDER, filename))
    
    @app.route('/results/<filename>')
    def results_file(filename):
        return send_file(os.path.join(Config.RESULTS_FOLDER, filename))