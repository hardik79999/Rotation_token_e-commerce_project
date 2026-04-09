from flask import request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from shop.extensions import db
from shop.models import Category, SellerCategory, Product, User
from shop.seller import seller_bp
from shop.utils.api_response import error_response, success_response

@seller_bp.route('/request-category', methods=['POST'])
def request_category():
    try:
        verify_jwt_in_request()
        claims = get_jwt()

        if claims.get("role") != "seller":
            return error_response("Unauthorized! Only sellers can request categories.", 403)

        data = request.get_json() or {}
        category_uuid = data.get('category_uuid')

        if not category_uuid:
            return error_response("Category UUID is required", 400)

        category = Category.query.filter_by(uuid=category_uuid, is_active=True).first()
        if not category:
            return error_response("Category not found", 404)

        seller_uuid = claims.get("user_uuid")
        seller = User.query.filter_by(uuid=seller_uuid).first()

        existing_req = SellerCategory.query.filter_by(seller_id=seller.id, category_id=category.id).first()
        
        if existing_req:
            if existing_req.is_approved:
                return error_response("You are already approved for this category.", 400)
            return error_response("Your request is already pending for admin approval.", 400)

        new_request = SellerCategory(
            seller_id=seller.id,
            category_id=category.id,
            is_approved=False,
            created_by=seller.id
        )

        db.session.add(new_request)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": f"Request to sell in '{category.name}' sent to Admin for approval."
        }), 201

    except Exception as e:
        db.session.rollback()
        print("REQUEST CATEGORY ERROR:", e)
        return error_response(str(e), 500)

@seller_bp.route('/product', methods=['POST'])
def create_product():
    try:
        verify_jwt_in_request()
        claims = get_jwt()

        if claims.get("role") != "seller":
            return error_response("Unauthorized! Only sellers can add products.", 403)

        data = request.get_json() or {}
        name = (data.get('name') or '').strip()
        description = (data.get('description') or '').strip()
        price = data.get('price')
        stock = data.get('stock', 0)
        category_uuid = data.get('category_uuid')

        if not all([name, description, price, category_uuid]):
            return error_response("Name, description, price, and category_uuid are required.", 400)

        category = Category.query.filter_by(uuid=category_uuid, is_active=True).first()
        if not category:
            return error_response("Category not found", 404)

        seller_uuid = claims.get("user_uuid")
        seller = User.query.filter_by(uuid=seller_uuid).first()

        is_allowed = SellerCategory.query.filter_by(
            seller_id=seller.id, 
            category_id=category.id, 
            is_approved=True
        ).first()

        if not is_allowed:
            return error_response("Permission Denied! Pehle admin se is category ke liye approve karwayein.", 403)

        new_product = Product(
            name=name,
            description=description,
            price=float(price),
            stock=int(stock),
            category_id=category.id,
            seller_id=seller.id,
            created_by=seller.id
        )

        db.session.add(new_product)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Product added successfully!",
            "data": {
                "uuid": new_product.uuid,
                "name": new_product.name,
                "price": new_product.price,
                "stock": new_product.stock
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        print("CREATE PRODUCT ERROR:", e)
        return error_response(str(e), 500)