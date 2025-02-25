from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()

class Request(db.Model):
    """Represents a single processing request for a CSV file."""
    __tablename__ = 'requests'

    id = db.Column(db.String(36), primary_key=True)
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    total_images = db.Column(db.Integer, default=0)
    processed_images = db.Column(db.Integer, default=0)
    webhook_url = db.Column(db.String(255), nullable=True)
    webhook_status = db.Column(db.String(20), nullable=True)  # not_sent, sent, failed
    
    products = db.relationship('Product', backref='request', lazy=True, cascade="all, delete-orphan")

class Product(db.Model):
    """Represents a product from the CSV file."""
    __tablename__ = 'products'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    request_id = db.Column(db.String(36), db.ForeignKey('requests.id'), nullable=False)
    serial_number = db.Column(db.Integer, nullable=False)
    product_name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    images = db.relationship('Image', backref='product', lazy=True, cascade="all, delete-orphan")

class Image(db.Model):
    """Represents an image associated with a product."""
    __tablename__ = 'images'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = db.Column(db.String(36), db.ForeignKey('products.id'), nullable=False)
    input_url = db.Column(db.String(1024), nullable=False)
    output_url = db.Column(db.String(1024), nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)