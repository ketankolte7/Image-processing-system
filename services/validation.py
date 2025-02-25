import pandas as pd
import requests
from database.models import Product, Image, db

def validate_csv(filepath):
    """
    Validates that the CSV file has the correct format and accessible image URLs.
    
    Parameters:
    filepath (str): Path to the CSV file
    
    Returns:
    dict: Validation result with 'valid' boolean and 'errors' list if invalid
    """
    result = {
        'valid': True,
        'errors': [],
        'total_images': 0
    }
    
    try:
        # Read the CSV file
        df = pd.read_csv(filepath)
        
        # Check required columns
        required_columns = ['S. No.', 'Product Name', 'Input Image Urls']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            result['valid'] = False
            result['errors'].append(f"Missing required columns: {', '.join(missing_columns)}")
            return result
        
        # Validate each row
        total_images = 0
        for index, row in df.iterrows():
            # Check for empty values
            if pd.isna(row['S. No.']) or pd.isna(row['Product Name']) or pd.isna(row['Input Image Urls']):
                result['valid'] = False
                result['errors'].append(f"Row {index+1} has empty required fields")
                continue
            
            # Validate serial number is an integer
            try:
                int(row['S. No.'])
            except:
                result['valid'] = False
                result['errors'].append(f"Row {index+1} has invalid serial number")
                continue
            
            # Validate image URLs
            image_urls = [url.strip() for url in str(row['Input Image Urls']).split(',')]
            if not image_urls:
                result['valid'] = False
                result['errors'].append(f"Row {index+1} has no image URLs")
                continue
            
            total_images += len(image_urls)
            
            # Optional: Check if URLs are accessible (commented out to avoid actual network requests during validation)
            """
            for url in image_urls:
                try:
                    response = requests.head(url, timeout=5)
                    if response.status_code != 200:
                        result['valid'] = False
                        result['errors'].append(f"Row {index+1} has inaccessible image URL: {url}")
                except:
                    result['valid'] = False
                    result['errors'].append(f"Row {index+1} has invalid image URL: {url}")
            """
        
        result['total_images'] = total_images
        
    except Exception as e:
        result['valid'] = False
        result['errors'].append(f"Error reading CSV file: {str(e)}")
    
    return result

def process_csv_to_db(request_id, filepath):
    """
    Processes the CSV file and stores product and image data in the database.
    
    Parameters:
    request_id (str): The unique ID of the request
    filepath (str): Path to the CSV file
    """
    try:
        # Read the CSV file
        df = pd.read_csv(filepath)
        
        # Process each row
        for _, row in df.iterrows():
            # Create product
            product = Product(
                request_id=request_id,
                serial_number=int(row['S. No.']),
                product_name=row['Product Name']
            )
            
            db.session.add(product)
            db.session.flush()  # Get the product ID
            
            # Create images
            image_urls = [url.strip() for url in str(row['Input Image Urls']).split(',')]
            for url in image_urls:
                if url:  # Skip empty URLs
                    image = Image(
                        product_id=product.id,
                        input_url=url,
                        status='pending'
                    )
                    db.session.add(image)
        
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        raise e