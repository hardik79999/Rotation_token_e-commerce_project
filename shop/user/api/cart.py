from flask import request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from shop.extensions import db
from shop.models import User, Product # Import Cart model as well
from shop.utils.api_response import error_response

def add_to_cart_action():
    try:
        verify_jwt_in_request()
        user = User.query.filter_by(uuid=get_jwt().get("user_uuid")).first()

        data = request.get_json() or {}
        product_uuid = data.get('product_uuid')
        quantity = int(data.get('quantity', 1))

        if not product_uuid:
            return error_response("Product UUID is required", 400)

        product = Product.query.filter_by(uuid=product_uuid, is_active=True).first()
        if not product:
            return error_response("Product not found", 404)

        if product.stock < quantity:
            return error_response(f"Only {product.stock} items left in stock", 400)

        # HINT: Yahan Cart table me save karna
        # existing_item = Cart.query.filter_by(user_id=user.id, product_id=product.id).first()
        # if existing_item: existing_item.quantity += quantity
        # else: db.session.add(Cart(user_id=user.id, product_id=product.id, quantity=quantity))
        # db.session.commit()

        return jsonify({"success": True, "message": "Added to cart"}), 201
    except Exception as e:
        db.session.rollback()
        return error_response('Failed to add to cart', 500)

def get_cart_action():
    try:
        verify_jwt_in_request()
        user = User.query.filter_by(uuid=get_jwt().get("user_uuid")).first()

        # HINT: Fetch cart items
        # cart_items = Cart.query.filter_by(user_id=user.id).all()
        # Calculate total price, etc.
        
        return jsonify({"success": True, "total_amount": 0, "items": []}), 200
    except Exception as e:
        return error_response(str(e), 500)