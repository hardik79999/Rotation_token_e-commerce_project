from datetime import datetime, timezone
from flask import request, jsonify
from shop.extensions import db, bcrypt
from shop.models import User, Otp, OTPAction
from shop.utils.api_response import error_response

def reset_password_action():
    try:
        data = request.get_json() or {}
        email = (data.get('email') or '').strip()
        otp_code = (data.get('otp_code') or '').strip()
        new_password = data.get('new_password')

        if not all([email, otp_code, new_password]):
            return error_response("Email, OTP, and new password are required", 400)

        user = User.query.filter_by(email=email, is_active=True).first()
        if not user:
            return error_response("User not found", 404)

        # OTP Verify karo (Latest active OTP nikalo)
        otp_record = Otp.query.filter_by(
            user_id=user.id, 
            otp_code=otp_code, 
            action=OTPAction.password_reset, 
            is_used=False
        ).order_by(Otp.created_at.desc()).first()

        if not otp_record:
            return error_response("Invalid or used OTP", 400)

        # Check karo OTP expire toh nahi ho gaya (10 mins limit thi models me)
        if otp_record.expires_at < datetime.utcnow():
            return error_response("OTP has expired. Please request a new one.", 400)

        # Sab sahi hai, toh naya password hash karke save karo
        hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        user.password = hashed_password
        
        # OTP ko used mark kar do taaki dubara use na ho
        otp_record.is_used = True
        
        db.session.commit()

        return jsonify({"success": True, "message": "Password has been reset successfully. You can now login."}), 200

    except Exception as e:
        db.session.rollback()
        return error_response(str(e), 500)