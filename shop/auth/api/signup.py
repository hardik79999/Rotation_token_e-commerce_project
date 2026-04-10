from flask import request, jsonify, current_app
from shop.extensions import db, bcrypt
from shop.models import User, Role
from shop.utils.email_service import send_verification_email
from itsdangerous import URLSafeTimedSerializer
from shop.utils.api_response import error_response

def signup_action():
    try:
        data = request.get_json() or {}
        username = (data.get('username') or '').strip()
        email = (data.get('email') or '').strip()
        password = data.get('password')
        phone = (data.get('phone') or '').strip() or None
        requested_role = (data.get('role') or 'customer').lower().strip()

        if not username or not email or not password:
            return error_response('Username, email, password required', 400)

        if requested_role not in {'customer', 'seller'}:
            return error_response("Invalid role", 400)

        # 1. Check if user already exists
        existing_user = User.query.filter((User.email == email) | (User.username == username)).first()
        
        if existing_user:
            # 🔥 REACTIVATION LOGIC: Agar user pehle se hai par usne account delete kiya tha
            if not existing_user.is_active:
                existing_user.is_active = True
                existing_user.username = username # Username update kar do naye wale se
                existing_user.phone = phone
                existing_user.password = bcrypt.generate_password_hash(password).decode('utf-8') # Naya password
                existing_user.is_verified = False # Security ke liye wapas email verify karwao
                
                db.session.flush()
                
                # Wapas verification email bhejo
                serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
                token = serializer.dumps(existing_user.email, salt='email-confirm')
                send_verification_email(existing_user.email, token)
                
                db.session.commit()
                
                return jsonify({
                    "success": True, 
                    "message": "Welcome back! Your account has been reactivated. Please check email to verify.",
                    "data": {
                        "uuid": existing_user.uuid,
                        "username": existing_user.username,
                        "email": existing_user.email,
                        "role": requested_role
                    }
                }), 200
            
            # Agar user active hai aur fir bhi signup try kar raha hai
            else:
                return error_response('User already exists', 409)

        # ==========================================
        # NORMAL SIGNUP LOGIC (Naye User ke liye)
        # ==========================================
        user_role = Role.query.filter_by(role_name=requested_role).first()
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        new_user = User(
            username=username,
            email=email,
            password=hashed_password,  
            phone=phone,              
            role_id=user_role.id,
            is_active=True,
            is_verified=False
        )

        db.session.add(new_user)
        db.session.flush() 

        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        token = serializer.dumps(new_user.email, salt='email-confirm')

        send_verification_email(new_user.email, token)

        db.session.commit()

        return jsonify({
            "success": True,
            "message": "User registered. Please check email to verify.",
            "data": {
                "uuid": new_user.uuid,
                "username": new_user.username,
                "email": new_user.email,
                "role": requested_role
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"SIGNUP ERROR: {str(e)}") # 🔥 Yahan bhi apna naya logger laga diya!
        return error_response(str(e), 500)