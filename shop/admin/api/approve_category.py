from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from shop.extensions import db
from shop.models import SellerCategory, User
from shop.utils.api_response import error_response

def approve_category_action(seller_category_uuid):
    try:
        verify_jwt_in_request()
        claims = get_jwt()

        if claims.get("role") != "admin":
            return error_response("Unauthorized!", 403)

        request_obj = SellerCategory.query.filter_by(uuid=seller_category_uuid).first()
        if not request_obj:
            return error_response("Seller Category request not found", 404)

        if request_obj.is_approved:
            return error_response("This request is already approved.", 400)

        request_obj.is_approved = True
        
        admin_uuid = claims.get("user_uuid")
        admin_user = User.query.filter_by(uuid=admin_uuid).first()
        request_obj.updated_by = admin_user.id
        
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Seller category approved successfully!"
        }), 200

    except Exception as e:
        db.session.rollback()
        print("APPROVE ERROR:", e)
        return error_response(str(e), 500)