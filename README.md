# Image Processing API Documentation

This document outlines the API endpoints provided by the Image Processing Service.

![Alt text](https://github.com/ketankolte7/Image-processing-system/blob/master/Image%20Processing%20System%20Flow%20Diagram.png)

## Base URL

All API endpoints are relative to the base URL: `http://localhost:5000`

## Authentication

No authentication is required for this demo. In a production environment, you would implement authentication using API keys, OAuth, or another suitable method.

## Endpoints

### 1. Upload CSV

Uploads a CSV file containing product information and image URLs for processing.

**URL**: `/api/upload`

**Method**: `POST`

**Content Type**: `multipart/form-data`

**Form Parameters**:
- `file` (required): CSV file with product and image data
- `webhook_url` (optional): URL to receive notifications when processing is complete

**Response**:

```json
{
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "pending",
    "message": "File uploaded successfully and processing has been initiated"
}
```

**Status Codes**:
- `202 Accepted`: File accepted for processing
- `400 Bad Request`: Invalid request or file
- `500 Internal Server Error`: Server error

### 2. Check Status

Retrieves the current status of a processing request.

**URL**: `/api/status/{request_id}`

**Method**: `GET`

**URL Parameters**:
- `request_id` (required): The unique ID returned by the upload API

**Response**:

```json
{
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "processing",
    "completion_percentage": 45.5,
    "created_at": "2023-01-15T14:30:12.123456",
    "updated_at": "2023-01-15T14:35:22.654321",
    "total_images": 20,
    "processed_images": 9,
    "webhook_status": "not_sent"
}
```

**Status Values**:
- `pending`: Request is queued but processing has not started
- `processing`: Images are currently being processed
- `completed`: All images have been processed
- `failed`: Processing failed

**Webhook Status Values**:
- `not_sent`: Webhook has not been sent yet
- `sent`: Webhook was successfully sent
- `failed`: Webhook delivery failed

**Status Codes**:
- `200 OK`: Request found
- `404 Not Found`: Request ID not found
- `500 Internal Server Error`: Server error

### 3. Download Results

Downloads the results CSV file containing both input and output image URLs.

**URL**: `/api/download/{request_id}`

**Method**: `GET`

**URL Parameters**:
- `request_id` (required): The unique ID returned by the upload API

**Response**:
- CSV file containing the original data with an additional column for output image URLs

**Status Codes**:
- `200 OK`: File is ready for download
- `404 Not Found`: Request ID not found or processing not complete
- `500 Internal Server Error`: Server error

## Webhook Notifications

If a webhook URL is provided during upload, the system will send a notification when processing is complete.

**Webhook Payload**:

```json
{
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "completed",
    "total_images": 20,
    "processed_images": 20,
    "completion_time": "2023-01-15T15:12:34.567890",
    "results_csv_url": "http://localhost:5000/results/550e8400-e29b-41d4-a716-446655440000_results.csv"
}
```

**Security**:

The webhook includes a signature header `X-Webhook-Signature` that can be used to verify the authenticity of the request. The signature is an HMAC-SHA256 hash of the payload using a shared secret.

## CSV File Format

### Input CSV Format

The CSV file must contain the following columns:
- `S. No.`: Serial number (integer)
- `Product Name`: Name of the product
- `Input Image Urls`: Comma-separated list of image URLs

Example:
```
S. No.,Product Name,Input Image Urls
1,SKU1,"https://www.public-image-url1.jpg,https://www.public-image-url2.jpg"
2,SKU2,"https://www.public-image-url3.jpg,https://www.public-image-url4.jpg"
```

### Output CSV Format

The output CSV will contain the following columns:
- `S. No.`: Serial number (integer)
- `Product Name`: Name of the product
- `Input Image Urls`: Comma-separated list of input image URLs
- `Output Image Urls`: Comma-separated list of output (processed) image URLs

Example:
```
S. No.,Product Name,Input Image Urls,Output Image Urls
1,SKU1,"https://www.public-image-url1.jpg,https://www.public-image-url2.jpg","https://www.public-image-output-url1.jpg,https://www.public-image-output-url2.jpg"
2,SKU2,"https://www.public-image-url3.jpg,https://www.public-image-url4.jpg","https://www.public-image-output-url3.jpg,https://www.public-image-output-url4.jpg"
```
