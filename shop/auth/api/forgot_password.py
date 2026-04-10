import random
from flask import request, jsonify
from shop.extensions import db
from shop.models import User, Otp, OTPAction
from shop.utils.api_response import error_response
from shop.utils.email_service import send_otp_email

def forgot_password_action():
    try:
        data = request.get_json() or {}
        email = (data.get('email') or '').strip()

        if not email:
            return error_response("Email is required", 400)

        user = User.query.filter_by(email=email, is_active=True).first()
        if not user:
            return error_response("No active account found with this email", 404)

        # 🔥 6-Digit Random OTP Generate karo
        otp_code = str(random.randint(100000, 999999))

        # Purane unused reset OTPs ko disable kar do taaki confusion na ho
        Otp.query.filter_by(user_id=user.id, action=OTPAction.password_reset, is_used=False).update({'is_used': True})

        # Naya OTP database me save karo
        new_otp = Otp(
            user_id=user.id,
            otp_code=otp_code,
            action=OTPAction.password_reset,
            created_by=user.id
        )
        db.session.add(new_otp)
        db.session.commit()

        # Email bhejo
        email_sent = send_otp_email(user.email, otp_code)
        
        if not email_sent:
            return error_response("Failed to send OTP email. Please try again later.", 500)

        return jsonify({"success": True, "message": "OTP sent to your email successfully!"}), 200

    except Exception as e:
        db.session.rollback()
        return error_response(str(e), 500)