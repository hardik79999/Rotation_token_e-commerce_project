from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt, create_access_token, create_refresh_token, set_access_cookies, set_refresh_cookies, unset_jwt_cookies
from shop.utils.api_response import error_response
from datetime import datetime, timezone, timedelta

def refresh_action():
    try:
        verify_jwt_in_request(refresh=True)
        claims = get_jwt()
        
        user_uuid = claims["sub"]
        role_name = claims.get("role")

        exp_timestamp = claims["exp"]
        now_timestamp = datetime.now(timezone.utc).timestamp()
        remaining_seconds = exp_timestamp - now_timestamp

        if remaining_seconds <= 0:
            response = jsonify({"success": False, "message": "Session expired after 7 days. Please login again."})
            unset_jwt_cookies(response)
            return response, 401

        new_access_token = create_access_token(
            identity=user_uuid,
            additional_claims={"role": role_name, "user_uuid": user_uuid}
        )

        remaining_delta = timedelta(seconds=remaining_seconds)
        new_refresh_token = create_refresh_token(
            identity=user_uuid,
            additional_claims={"role": role_name, "user_uuid": user_uuid},
            expires_delta=remaining_delta  
        )

        days_left = round(remaining_seconds / 86400, 2)

        response = jsonify({
            "success": True, 
            "message": "Token refreshed successfully",
            "session_days_left": days_left
        })
        
        set_access_cookies(response, new_access_token)
        set_refresh_cookies(response, new_refresh_token)

        return response, 200

    except Exception as e:
        error_msg = str(e)
        # 🔥 Puraana fix: Clean 401 error on expiry
        if "Signature has expired" in error_msg or "Token has expired" in error_msg:
            response = jsonify({
                "success": False, 
                "message": "Session expired. Please login again."
            })
            unset_jwt_cookies(response)  
            return response, 401
            
        print("REFRESH ERROR:", e)
        return error_response(error_msg, 500)