from flask import jsonify
from flask_jwt_extended import unset_jwt_cookies
from shop.utils.api_response import error_response

def logout_action():
    try:
        response = jsonify({"success": True, "message": "Logout successful"})
        unset_jwt_cookies(response)
        return response, 200

    except Exception as e:
        print("LOGOUT ERROR:", e)
        return error_response(str(e), 500)