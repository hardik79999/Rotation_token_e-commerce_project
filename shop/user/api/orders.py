from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from shop.models import User, Order
from shop.utils.api_response import error_response

def get_orders_action():
    try:
        verify_jwt_in_request()
        user = User.query.filter_by(uuid=get_jwt().get("user_uuid")).first()

        orders = Order.query.filter_by(user_id=user.id).order_by(Order.created_at.desc()).all()
        
        result = []
        for o in orders:
            result.append({
                "uuid": o.uuid,
                "amount": o.total_amount,
                "status": o.status.name if hasattr(o.status, 'name') else str(o.status),
                "payment_method": o.payment_method.name if hasattr(o.payment_method, 'name') else str(o.payment_method),
                "date": o.created_at.strftime('%Y-%m-%d %H:%M:%S') if o.created_at else None
            })

        return jsonify({"success": True, "total": len(result), "data": result}), 200
    except Exception as e:
        return error_response(str(e), 500)

# 🔥 NAYA FUNCTION: SINGLE ORDER STATUS KE LIYE
# 🔥 UPDATED FUNCTION: WITH TRACKING TIMELINE
def get_order_status_action(order_uuid):
    try:
        verify_jwt_in_request()
        user = User.query.filter_by(uuid=get_jwt().get("user_uuid")).first()

        order = Order.query.filter_by(uuid=order_uuid, user_id=user.id).first()
        if not order:
            return error_response("Order not found", 404)

        # Tracking History nikalna
        tracking_history = []
        for track in order.tracking:
            tracking_history.append({
                "status": track.status.name.capitalize() if hasattr(track.status, 'name') else str(track.status),
                "message": track.message,
                "date": track.created_at.strftime('%Y-%m-%d %H:%M:%S') if track.created_at else None
            })

        return jsonify({
            "success": True,
            "data": {
                "order_uuid": order.uuid,
                "current_status": order.status.name.capitalize() if hasattr(order.status, 'name') else str(order.status),
                "amount": order.total_amount,
                "payment_method": order.payment_method.name if hasattr(order.payment_method, 'name') else str(order.payment_method),
                "tracking_history": tracking_history  # 🔥 Ye rahi teri logistics timeline!
            }
        }), 200
    except Exception as e:
        return error_response(str(e), 500)