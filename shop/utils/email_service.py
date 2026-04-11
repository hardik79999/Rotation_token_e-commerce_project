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










def send_category_request_email_to_admin(admin_emails, seller_name, category_name):
    try:
        msg = Message(
            subject=f'New Category Approval Request: {category_name}', 
            sender=current_app.config['MAIL_USERNAME'], 
            recipients=admin_emails
        )
        
        msg.html = f"""
        <div style="font-family: Arial; padding: 20px; border: 1px solid #eee;">
            <h2>New Seller Category Request 🛍️</h2>
            <p>Hello Admin,</p>
            <p>Seller <strong>{seller_name}</strong> ne nai category me sell karne ki request bheji hai.</p>
            <p><strong>Category Name:</strong> {category_name}</p>
            <br>
            <p>Kripya apne Admin Panel me login karein aur is request ko Approve/Reject karein.</p>
        </div>
        """
        mail.send(msg)
        return True
    except Exception as e:
        print("ADMIN EMAIL ERROR:", e)
        return False
    




def send_otp_email(user_email, otp_code):
    try:
        msg = Message(
            subject='Password Reset OTP', 
            sender=current_app.config['MAIL_USERNAME'], 
            recipients=[user_email]
        )
        
        msg.html = f"""
        <div style="font-family: Arial; text-align: center; padding: 20px; border: 1px solid #eee;">
            <h2>Password Reset Request 🔒</h2>
            <p>Tumhara password reset karne ka OTP niche diya gaya hai:</p>
            <h1 style="color: #28a745; letter-spacing: 5px;">{otp_code}</h1>
            <p>Ye OTP 10 minute me expire ho jayega. Kisi ke sath share mat karna!</p>
        </div>
        """
        mail.send(msg)
        return True
    except Exception as e:
        print("OTP EMAIL ERROR:", e)
        return False
    




def send_order_status_email(user_email, order_uuid, new_status):
    msg = Message(
        subject=f"Order Update: Your order is now {new_status.upper()}",
        sender=current_app.config['MAIL_USERNAME'],
        recipients=[user_email]
    )
    msg.body = f"Hello,\n\nYour order (ID: {order_uuid}) status has been updated to: {new_status}.\n\nThank you for shopping with us!"
    mail.send(msg)