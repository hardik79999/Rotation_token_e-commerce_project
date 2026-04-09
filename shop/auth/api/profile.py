from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from shop.models import User
from shop.utils.api_response import error_response

def profile_action():
    try:
        verify_jwt_in_request()
        claims = get_jwt()
        user_uuid = claims.get("user_uuid")
        
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
                "phone": user.phone
            }
        })

    except Exception as e:
        error_msg = str(e)
        # Add the same token expiry handling for profile APIs too
        if "Signature has expired" in error_msg or "Token has expired" in error_msg:
            return jsonify({"success": False, "message": "Session expired. Please login again."}), 401
            
        print("PROFILE ERROR:", e)
        return error_response(error_msg, 500)