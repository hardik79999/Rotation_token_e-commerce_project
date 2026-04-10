from flask import request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from shop.extensions import db
from shop.models import User, Product
from shop.utils.api_response import error_response

# HINT: Model: class Review(BaseModel): user_id, product_id, rating, comment

def add_review_action():
    try:
        verify_jwt_in_request()
        user = User.query.filter_by(uuid=get_jwt().get("user_uuid")).first()
        data = request.get_json() or {}
        
        product_uuid = data.get('product_uuid')
        rating = data.get('rating')
        comment = data.get('comment', '')

        if not product_uuid or not rating:
            return error_response("Product UUID and rating are required", 400)

        # TODO: Yahan check karna chahiye ki user ne ye product kharida hai ya nahi (Order table se)
        
        # db.session.add(Review(user_id=user.id, product_id=product.id, rating=rating, comment=comment))
        # db.session.commit()

        return jsonify({"success": True, "message": "Review submitted successfully"}), 201
    except Exception as e:
        return error_response(str(e), 500)