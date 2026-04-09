from flask import request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from shop.extensions import db
from shop.models import Category, User
from shop.utils.api_response import error_response

def create_category_action():
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