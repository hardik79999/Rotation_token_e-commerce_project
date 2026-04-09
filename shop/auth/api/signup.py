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

        existing_user = User.query.filter((User.email == email) | (User.username == username)).first()
        if existing_user:
            return error_response('User already exists', 409)

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
        print("SIGNUP ERROR:", e)
        return error_response(str(e), 500)