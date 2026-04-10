from flask import request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from shop.extensions import db
# 🔥 FIX: Yahan 'Cart' ki jagah 'CartItem' import kiya
from shop.models import User, Product, CartItem 
from shop.utils.api_response import error_response

def add_to_cart_action():
    try:
        verify_jwt_in_request()
        user = User.query.filter_by(uuid=get_jwt().get("user_uuid")).first()

        data = request.get_json() or {}
        product_uuid = data.get('product_uuid')
        qty = int(data.get('quantity', 1))

        product = Product.query.filter_by(uuid=product_uuid, is_active=True).first()
        if not product:
            return error_response("Product not found", 404)

        # 🔥 FIX: CartItem use kiya
        existing_item = CartItem.query.filter_by(user_id=user.id, product_id=product.id, is_active=True).first()

        if existing_item:
            existing_item.quantity += qty 
        else:
            # 🔥 FIX: CartItem use kiya
            new_cart_item = CartItem(
                user_id=user.id,
                product_id=product.id,
                quantity=qty,
                created_by=user.id
            )
            db.session.add(new_cart_item)

        db.session.commit() 
        return jsonify({"success": True, "message": "Item added to cart!"}), 200

    except Exception as e:
        db.session.rollback()
        return error_response(str(e), 500)

def get_cart_action():
    try:
        verify_jwt_in_request()
        user = User.query.filter_by(uuid=get_jwt().get("user_uuid")).first()

        # 🔥 FIX: CartItem use kiya
        cart_items = CartItem.query.filter_by(user_id=user.id, is_active=True).all()
        
        total_bill = 0
        items_list = []

        for item in cart_items:
            product = item.product
            item_total = float(product.price) * item.quantity
            total_bill += item_total
            
            items_list.append({
                "cart_item_id": item.id,
                "product_name": product.name,
                "price": float(product.price),
                "quantity": item.quantity,
                "subtotal": item_total,
                "image": product.images[0].image_url if product.images else None
            })

        return jsonify({
            "success": True,
            "total_amount": total_bill,
            "data": items_list
        }), 200
    except Exception as e:
        return error_response(str(e), 500)