import razorpay
from flask import current_app

def get_razorpay_client():
    """Razorpay client ko initialize karta hai keys ke sath"""
    key_id = current_app.config['RAZORPAY_KEY_ID']
    key_secret = current_app.config['RAZORPAY_KEY_SECRET']
    return razorpay.Client(auth=(key_id, key_secret))