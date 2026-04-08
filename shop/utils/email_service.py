# shop/utils/email_service.py
from flask_mail import Message
from shop.extensions import mail
from flask import current_app

def send_verification_email(user_email, token):
    # Hum token bhej rahe hain email me link ke saath
    verification_link = f"http://127.0.0.1:7899/api/auth/verify/{token}"
    
    msg = Message('Verify Your Account', 
                  sender=current_app.config['MAIL_USERNAME'], 
                  recipients=[user_email])
    
    # HTML wala part - Button ke liye
    msg.html = f"""
    <div style="font-family: Arial; text-align: center; padding: 20px; border: 1px solid #eee;">
        <h2>Welcome to Our Store! 🚀</h2>
        <p>Apna account activate karne ke liye niche button pe click karo:</p>
        <a href="{verification_link}" 
           style="background: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 20px 0;">
           Verify Email Now
        </a>
        <p>Ye link 10 minute me expire ho jayega.</p>
    </div>
    """
    mail.send(msg)