import random
from datetime import datetime, timedelta
from flask import request, jsonify, current_app
from shop.extensions import db
from shop.models import User, Otp, OTPAction
from shop.utils.api_response import error_response
from shop.utils.email_service import send_otp_email

def forgot_password_action():
    try:
        data = request.get_json() or {}
        email = data.get('email')

        if not email:
            return error_response("Email is required", 400)

        # 1. User dhundho
        user = User.query.filter_by(email=email, is_active=True).first()
        if not user:
            # Security Note: Hacker ko mat batao ki email galat hai
            return jsonify({"success": True, "message": "If this email is registered, you will receive an OTP."}), 200

        # 2. Purane active OTPs ko invalidate (is_used = True) kar do
        Otp.query.filter_by(user_id=user.id, action=OTPAction.password_reset, is_used=False).update({"is_used": True})
        
        # 3. Naya 6-digit OTP Generate karo
        otp_code = str(random.randint(100000, 999999))

        # 4. 🔥 Database me save karo
        new_otp = Otp(
            user_id=user.id,
            otp_code=otp_code,
            action=OTPAction.password_reset,
            is_used=False,
            expires_at=datetime.utcnow() + timedelta(minutes=10),
            created_by=user.id
        )
        db.session.add(new_otp)
        db.session.commit()

        # 5. Email Bhejo
        email_sent = send_otp_email(user.email, otp_code)
        
        if not email_sent:
            return error_response("Failed to send email. Please check your mail configuration.", 500)

        return jsonify({
            "success": True, 
            "message": "OTP sent successfully to your email!"
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Forgot Password Error: {str(e)}")
        return error_response(f"An error occurred: {str(e)}", 500)