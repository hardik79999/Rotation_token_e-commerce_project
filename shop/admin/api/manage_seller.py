from flask import jsonify, current_app
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from shop.extensions import db
from shop.models import User, Role
from shop.utils.api_response import error_response

def toggle_seller_status_action(seller_uuid):
    try:
        verify_jwt_in_request()
        if get_jwt().get("role") != "admin":
            return error_response("Admin access required", 403)

        seller = User.query.filter_by(uuid=seller_uuid).first()
        if not seller or seller.role.role_name != "seller":
            return error_response("Seller not found", 404)

        # 🔥 Toggle Status (Active hai toh Inactive kar do, aur vice versa)
        seller.is_active = not seller.is_active
        db.session.commit()

        status_msg = "Activated" if seller.is_active else "Blocked"
        current_app.logger.info(f"Seller {seller.email} {status_msg} by Admin.")

        return jsonify({"success": True, "message": f"Seller account has been {status_msg}."}), 200

    except Exception as e:
        db.session.rollback()
        return error_response(str(e), 500)