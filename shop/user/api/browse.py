from flask import jsonify
from shop.models import Category, Product
from shop.utils.api_response import error_response
from shop.seller.api.helpers import serialize_seller_product # (Purana helper reuse kar lenge)

def get_categories_action():
    try:
        categories = Category.query.filter_by(is_active=True).all()
        result = [{"uuid": c.uuid, "name": c.name, "description": c.description} for c in categories]
        return jsonify({"success": True, "data": result}), 200
    except Exception as e:
        return error_response(str(e), 500)

def get_products_action():
    try:
        # Sirf active products dikhao jo approved categories me hain
        products = Product.query.filter_by(is_active=True).order_by(Product.created_at.desc()).all()
        result = [serialize_seller_product(p) for p in products]
        return jsonify({"success": True, "total": len(result), "data": result}), 200
    except Exception as e:
        return error_response(str(e), 500)

def get_single_product_action(product_uuid):
    try:
        product = Product.query.filter_by(uuid=product_uuid, is_active=True).first()
        if not product:
            return error_response("Product not found", 404)
        
        return jsonify({"success": True, "data": serialize_seller_product(product)}), 200
    except Exception as e:
        return error_response(str(e), 500)