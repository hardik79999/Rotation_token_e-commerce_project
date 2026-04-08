import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key')
    
    # Database setup
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT setup
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'default-jwt-secret')
    
    # Mail setup
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True') == 'True'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')

    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')


    # JWT setup
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'default-jwt-secret')
    
    # 🔥 TOKEN ROTATION & COOKIE SETUP
    JWT_TOKEN_LOCATION = ["cookies"]
    JWT_COOKIE_SECURE = False          # Set to True in Production (HTTPS)
    JWT_COOKIE_HTTPONLY = True         # Protects against XSS
    JWT_COOKIE_SAMESITE = "Lax"        
    
    # 🔥 ENABLE CSRF TO GET csrf_access_token & csrf_refresh_token
    JWT_COOKIE_CSRF_PROTECT = True     
    JWT_CSRF_IN_COOKIES = True         # Puts the CSRF token in a readable cookie for frontend
    
    JWT_ACCESS_TOKEN_EXPIRES = 900        # 15 min
    JWT_REFRESH_TOKEN_EXPIRES = 86400     # 1 day