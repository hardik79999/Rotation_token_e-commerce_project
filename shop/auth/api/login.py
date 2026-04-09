from flask import request, jsonify
from shop.extensions import db, bcrypt
from shop.models import User
from flask_jwt_extended import create_access_token, create_refresh_token, set_access_cookies, set_refresh_cookies
from shop.utils.api_response import error_response

def login_action():
    try:
        data = request.get_json() or {}
        email = (data.get('email') or '').strip()
        password = data.get('password')

        if not email or not password:
            return error_response("Email and password required", 400)

        user = User.query.filter_by(email=email).first()

        if not user or not user.password or not bcrypt.check_password_hash(user.password, password):
            return error_response("Invalid email or password", 401)

        if not user.is_active:
            return error_response("Account blocked", 403)

        if not user.is_verified:
            return error_response("Verify your account first", 401)

        role_name = user.role.role_name if user.role else "customer"

        claims = {
            "role": role_name,
            "user_uuid": user.uuid
        }

        access_token = create_access_token(identity=user.uuid, additional_claims=claims)
        refresh_token = create_refresh_token(identity=user.uuid, additional_claims=claims)

        response = jsonify({
            "success": True,
            "message": "Login successful",
            "data": {
                "uuid": user.uuid,
                "username": user.username,
                "email": user.email,
                "role": role_name
            }
        })
        
        set_access_cookies(response, access_token)
        set_refresh_cookies(response, refresh_token)

        return response, 200

    except Exception as e:
        print("LOGIN ERROR:", e)
        return error_response(str(e), 500)