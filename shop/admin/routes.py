from flask import request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from shop.extensions import db
from shop.models import Category, User, SellerCategory
from shop.admin import admin_bp
from shop.utils.api_response import error_response, success_response

# =====================================================================
# CREATE CATEGORY (POST - Only for Admin)
# =====================================================================
@admin_bp.route('/category', methods=['POST'])
def create_category():
    try:
        verify_jwt_in_request()
        claims = get_jwt()

        if claims.get("role") != "admin":
            return error_response("Unauthorized! Only admins can create categories.", 403)

        data = request.get_json() or {}
        name = (data.get('name') or '').strip()
        description = (data.get('description') or '').strip()

        if not name:
            return error_response("Category name is required", 400)

        existing_category = Category.query.filter_by(name=name).first()
        if existing_category:
            return error_response("Category with this name already exists.", 409)

        admin_uuid = claims.get("user_uuid")
        admin_user = User.query.filter_by(uuid=admin_uuid).first()

        # 🔥 FIXED: Sirf 'created_by' use kiya, 'user_id' hata diya
        new_category = Category(
            name=name,
            description=description,     
            created_by=admin_user.id   
        )

        db.session.add(new_category)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Category created successfully!",
            "data": {
                "uuid": new_category.uuid,
                "name": new_category.name,
                "description": new_category.description
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        print("CREATE CATEGORY ERROR:", e)
        return error_response(str(e), 500)

# =====================================================================
# APPROVE SELLER CATEGORY (PUT - Admin Only)
# =====================================================================
@admin_bp.route('/approve-category/<seller_category_uuid>', methods=['PUT'])
def approve_seller_category(seller_category_uuid):
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