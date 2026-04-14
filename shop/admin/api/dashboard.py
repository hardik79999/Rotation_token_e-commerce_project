from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from shop.extensions import db
from shop.models import User, Order, Product, Payment, PaymentStatus
from shop.utils.api_response import error_response
from sqlalchemy import func

def admin_dashboard_action():
    try:
        verify_jwt_in_request()
        if get_jwt().get("role") != "admin":
            return error_response("Unauthorized Access", 403)

        # SQL Queries to count data
        total_users = User.query.filter_by(is_active=True).count()
        total_products = Product.query.filter_by(is_active=True).count()
        total_orders = Order.query.count()
        
        # SQL Aggregation for Total Revenue
        revenue = db.session.query(func.sum(Payment.amount)).filter(Payment.status == PaymentStatus.completed).scalar() or 0.0

        return jsonify({
            "success": True,
            "message": "Analytics fetched successfully",
            "data": {
                "total_users": total_users,
                "total_products": total_products,
                "total_orders": total_orders,
                "total_revenue": round(revenue, 2)
            }
        }), 200

    except Exception as e:
        return error_response(str(e), 500)