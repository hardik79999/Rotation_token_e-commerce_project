from flask import request, jsonify, current_app, render_template_string
from shop.extensions import db, bcrypt
from shop.models import User, Role
from shop.utils.email_service import send_verification_email
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    set_access_cookies,
    set_refresh_cookies,
    get_jwt,
    verify_jwt_in_request,
    unset_jwt_cookies
)
from shop.auth import auth_bp
from shop.utils.api_response import error_response, success_response


# =====================================================================
# LOGIN (POST - Data JSON me aayega)
# =====================================================================
@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        # POST method hai toh request.get_json() use karenge
        data = request.get_json() or {}

        email = (data.get('email') or '').strip()
        password = data.get('password')

        if not email or not password:
            return error_response("Email and password required", 400)

        # Lookup by Email
        user = User.query.filter_by(email=email).first()

        if not user or not user.password or not bcrypt.check_password_hash(user.password, password):
            return error_response("Invalid email or password", 401)

        if not user.is_active:
            return error_response("Account blocked", 403)

        if not user.is_verified:
            return error_response("Verify your account first", 401)

        role_name = user.role.role_name if user.role else "customer"

        # 🔥 IMPORTANT FIX: Ab payload me user_id nahi, 'uuid' store karenge!
        claims = {
            "role": role_name,
            "user_uuid": user.uuid  # <--- YAHAN UUID USE KIYA
        }

        # Token identity ko bhi UUID set kar diya
        access_token = create_access_token(
            identity=user.uuid,
            additional_claims=claims
        )

        refresh_token = create_refresh_token(
            identity=user.uuid,
            additional_claims=claims
        )

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
        
        # Ye functions un 4 cookies ko HTTP Headers me set karte hain
        set_access_cookies(response, access_token)
        set_refresh_cookies(response, refresh_token)

        return response, 200

    except Exception as e:
        print("LOGIN ERROR:", e)
        return error_response(str(e), 500)


# =====================================================================
# SIGNUP (POST - Data JSON me aayega)
# =====================================================================
@auth_bp.route('/signup', methods=['POST'])
def signup():
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

        existing_user = User.query.filter(
            (User.email == email) | (User.username == username)
        ).first()

        if existing_user:
            return error_response('User already exists', 409)

        user_role = Role.query.filter_by(role_name=requested_role).first()
        if not user_role:
            return error_response('Roles not initialized', 500)

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
        db.session.flush() # ID/UUID generate karne ke liye flush karna zaroori hai

        # Email Verification Token
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        token = serializer.dumps(new_user.email, salt='email-confirm')

        # Send Email
        send_verification_email(new_user.email, token)

        db.session.commit()

        return jsonify({
            "success": True,
            "message": "User registered successfully. Please check your email to verify your account.",
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

# =====================================================================
# VERIFY EMAIL (GET - Data URL/Path me aayega)
# =====================================================================
@auth_bp.route('/verify/<token>', methods=['GET'])
def verify_email(token):
    # GET request me data directly route parameter (<token>) se milta hai
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = s.loads(token, salt='email-confirm', max_age=600) 
        user = User.query.filter_by(email=email).first()
        
        if user:
            if user.is_verified:
                return render_template_string("<h1 style='color:#4CAF50; text-align:center;'>✅ Already Verified! You can login.</h1>")
                
            user.is_verified = True 
            db.session.commit()
            return render_template_string("<h1 style='color:#4CAF50; text-align:center;'>🎉 Success! Your email is verified.</h1>")
            
    except (SignatureExpired, BadSignature):
        return render_template_string("<h1 style='color:red; text-align:center;'>❌ Verification link is invalid or expired!</h1>")

    return "User not found", 404


# =====================================================================
# REFRESH TOKEN (POST)
# =====================================================================
@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    try:
        verify_jwt_in_request(refresh=True)
        claims = get_jwt()

        # Naya token banate waqt wapas UUID hi pass karenge
        new_access_token = create_access_token(
            identity=claims["sub"], # claims["sub"] me user_uuid pada hai
            additional_claims={
                "role": claims.get("role"),
                "user_uuid": claims.get("user_uuid")
            }
        )

        response = jsonify({"message": "Token refreshed"})
        set_access_cookies(response, new_access_token)

        return response, 200

    except Exception as e:
        print("REFRESH ERROR:", e)
        return error_response(str(e), 500)


# =====================================================================
# PROFILE (GET - UUID ke throw database hit karke data nikalna)
# =====================================================================
@auth_bp.route('/profile', methods=['GET'])
def profile():
    try:
        verify_jwt_in_request()
        claims = get_jwt()

        # 🔥 Hamesha UUID se data find karenge!
        user_uuid = claims.get("user_uuid")
        
        # internal id ki jagah uuid filter lagaya
        user = User.query.filter_by(uuid=user_uuid, is_active=True).first()

        if not user:
            return error_response("User not found", 404)

        return jsonify({
            "success": True,
            "data": {
                "uuid": user.uuid,
                "username": user.username,
                "email": user.email,
                "role": user.role.role_name,
                "phone": user.phone_number
            }
        })

    except Exception as e:
        print("PROFILE ERROR:", e)
        return error_response(str(e), 500)


# =====================================================================
# LOGOUT (POST)
# =====================================================================
@auth_bp.route('/logout', methods=['POST'])
def logout():
    try:
        response = jsonify({"success": True, "message": "Logout successful"})
        unset_jwt_cookies(response)
        return response, 200

    except Exception as e:
        print("LOGOUT ERROR:", e)
        return error_response(str(e), 500)