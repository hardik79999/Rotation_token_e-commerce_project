from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from shop.models import User, Order
from shop.utils.api_response import error_response

def get_orders_action():
    try:
        verify_jwt_in_request()
        user = User.query.filter_by(uuid=get_jwt().get("user_uuid")).first()

        # Fetch saare orders jo pending se aage badh chuke hain
        # orders = Order.query.filter_by(user_id=user.id).order_by(Order.created_at.desc()).all()
        # result = [{"uuid": o.uuid, "amount": o.total_amount, "status": o.status} for o in orders]

        return jsonify({"success": True, "total": 0, "data": []}), 200
    except Exception as e:
        return error_response(str(e), 500)