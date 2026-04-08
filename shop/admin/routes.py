from flask import request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from shop.extensions import db
from shop.models import Category, User
from shop.admin import admin_bp
from shop.utils.api_response import error_response, success_response

# =====================================================================
# CREATE CATEGORY (POST - Only for Admin)
# URL: http://127.0.0.1:7899/api/admin/category
# =====================================================================
@admin_bp.route('/category', methods=['POST'])
def create_category():
    try:
        # 1. Check if user is logged in (Token Validate)
        verify_jwt_in_request()
        claims = get_jwt()

        # 2. Role Authorization (Sirf Admin allowed hai)
        if claims.get("role") != "admin":
            return error_response("Unauthorized! Only admins can create categories.", 403)

        # 3. Get Data from Request Body (JSON)
        data = request.get_json() or {}
        name = (data.get('name') or '').strip()
        description = (data.get('description') or '').strip()

        if not name:
            return error_response("Category name is required", 400)

        # Check if category already exists
        existing_category = Category.query.filter_by(name=name).first()
        if existing_category:
            return error_response("Category with this name already exists.", 409)

        # 4. Get Admin's internal ID to store in 'created_by'
        admin_uuid = claims.get("user_uuid")
        admin_user = User.query.filter_by(uuid=admin_uuid).first()

        # 5. Create new Category
        new_category = Category(
            name=name,
            description=description,
            user_id=admin_user.id,     # Track kisne banaya
            created_by=admin_user.id   # Auditing field
        )

        db.session.add(new_category)
        db.session.commit()

        # 6. Return standard JSON with UUID
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