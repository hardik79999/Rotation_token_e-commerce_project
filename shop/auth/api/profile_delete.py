from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from shop.extensions import db
from shop.models import User
from shop.utils.api_response import error_response
from flask import current_app

def soft_delete_user_action():
    try:
        verify_jwt_in_request()
        user_uuid = get_jwt().get("user_uuid")
        
        user = User.query.filter_by(uuid=user_uuid, is_active=True).first()
        if not user:
            return error_response("User not found or already deleted", 404)

        # 🔥 SOFT DELETE MAGIC: Data rahega, par login nahi hoga
        user.is_active = False 
        db.session.commit()

        current_app.logger.info(f"User Soft Deleted: {user.email}")

        return jsonify({"success": True, "message": "Your account has been deleted successfully."}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Delete Account Error: {str(e)}")
        return error_response(str(e), 500)