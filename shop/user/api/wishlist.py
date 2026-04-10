from flask import request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from shop.extensions import db
from shop.models import User, Product
from shop.utils.api_response import error_response

# HINT: Model me aisi table honi chahiye:
# class Wishlist(BaseModel): user_id, product_id

def toggle_wishlist_action():
    try:
        verify_jwt_in_request()
        user = User.query.filter_by(uuid=get_jwt().get("user_uuid")).first()
        product_uuid = (request.get_json() or {}).get('product_uuid')

        if not product_uuid: return error_response("Product UUID required", 400)
        product = Product.query.filter_by(uuid=product_uuid, is_active=True).first()
        if not product: return error_response("Product not found", 404)

        # Logic: Agar wishlist me hai toh hata do, nahi hai toh daal do
        # existing = Wishlist.query.filter_by(user_id=user.id, product_id=product.id).first()
        # if existing:
        #     db.session.delete(existing)
        #     msg = "Removed from wishlist"
        # else:
        #     db.session.add(Wishlist(user_id=user.id, product_id=product.id))
        #     msg = "Added to wishlist"
        # db.session.commit()

        return jsonify({"success": True, "message": "Wishlist updated"}), 200
    except Exception as e:
        return error_response(str(e), 500)

def get_wishlist_action():
    try:
        verify_jwt_in_request()
        # Logic: User ki saari wishlist items fetch karo aur serialize_seller_product se return kardo
        return jsonify({"success": True, "data": []}), 200
    except Exception as e:
        return error_response(str(e), 500)