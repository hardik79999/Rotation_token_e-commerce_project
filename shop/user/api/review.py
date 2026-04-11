from flask import request, jsonify, current_app
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from shop.extensions import db
from shop.models import Product, Order, OrderStatus, Review, User, OrderItem, CartItem
from shop.utils.api_response import error_response
from sqlalchemy import func

def add_product_review_action(product_uuid):
    try:
        verify_jwt_in_request()
        user_uuid = get_jwt().get("user_uuid")
        user = User.query.filter_by(uuid=user_uuid).first()
        
        data = request.get_json()
        rating = data.get("rating")
        comment = data.get("comment", "").strip()

        if not rating or not (1 <= int(rating) <= 5):
            return error_response("Rating must be between 1 and 5", 400)

        product = Product.query.filter_by(uuid=product_uuid, is_active=True).first()
        if not product:
            return error_response("Product not found", 404)

        # 🔥 VERIFIED BUYER LOGIC: Check karo kya is user ne ye product khareeda hai aur wo deliver hua hai
        # (Note: Ye query tere Order aur OrderItem ke relation par depend karegi. Ye ek standard approach hai)
        has_bought = db.session.query(Order).join(OrderItem).filter(
            Order.user_id == user.id,
            Order.status == OrderStatus.delivered,
            OrderItem.product_id == product.id
        ).first()

        if not has_bought:
            return error_response("You can only review products you have bought and received.", 403)

        # Check agar pehle se review diya hai
        existing_review = Review.query.filter_by(user_id=user.id, product_id=product.id).first()
        if existing_review:
            return error_response("You have already reviewed this product. You can't review twice.", 400)

        # Naya Review Add karo
        new_review = Review(
            user_id=user.id,
            product_id=product.id,
            rating=int(rating),
            comment=comment
        )
        db.session.add(new_review)
        db.session.commit()

        # 🔥 DYNAMIC RATING UPDATE: Product ki average rating calculate karke update kar do
        avg_rating = db.session.query(func.avg(Review.rating)).filter(Review.product_id == product.id).scalar()
        product.average_rating = round(avg_rating, 1)
        db.session.commit()

        return jsonify({
            "success": True, 
            "message": "Review added successfully!",
            "new_average_rating": product.average_rating
        }), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Review Error: {str(e)}")
        return error_response(str(e), 500)